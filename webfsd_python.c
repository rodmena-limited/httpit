/*
 * Python wrapper for webfsd
 * This provides a minimal interface to run webfsd from Python
 */

#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <pthread.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

/* Global state */
static PyObject *WebfsdError;
static volatile int server_running = 0;
static pid_t server_pid = 0;

/* Start the server by forking webfsd */
static PyObject *
webfsd_start(PyObject *self, PyObject *args, PyObject *kwargs)
{
    /* Basic required parameters */
    int port = 8000;
    const char *root = ".";
    
    /* Most commonly used optional parameters */
    int debug = 0;
    int no_listing = 0;
    int foreground = 1;  /* Default to foreground mode */
    const char *auth = NULL;
    const char *log_file = NULL;
    const char *cors = NULL;
    const char *host = NULL;
    const char *bind_ip = NULL;
    int timeout = 60;
    int max_connections = 32;
    const char *index_file = NULL;
    
    static char *kwlist[] = {
        "port", "root", "debug", "no_listing", "foreground", "auth", "log", "cors", 
        "host", "bind_ip", "timeout", "max_connections", "index", NULL
    };
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|isiiizzzziiz:start_server", kwlist,
                                     &port, &root, &debug, &no_listing, &foreground, &auth,
                                     &log_file, &cors, &host, &bind_ip, &timeout,
                                     &max_connections, &index_file)) {
        return NULL;
    }
    
    if (server_running) {
        PyErr_SetString(WebfsdError, "Server is already running");
        return NULL;
    }
    
    /* Check if port is already in use */
    int test_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (test_socket >= 0) {
        struct sockaddr_in addr;
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = INADDR_ANY;
        
        if (bind(test_socket, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            close(test_socket);
            if (errno == EADDRINUSE) {
                PyErr_Format(WebfsdError, "Port %d is already in use. Please choose a different port or stop the existing server.", port);
                return NULL;
            }
        }
        close(test_socket);
    }
    
    /* Fork and exec webfsd */
    server_pid = fork();
    if (server_pid < 0) {
        PyErr_SetFromErrno(WebfsdError);
        return NULL;
    }
    
    if (server_pid == 0) {
        /* Child process - exec webfsd */
        char port_str[32];
        char timeout_str[32];
        char max_conn_str[32];
        snprintf(port_str, sizeof(port_str), "%d", port);
        snprintf(timeout_str, sizeof(timeout_str), "%d", timeout);
        snprintf(max_conn_str, sizeof(max_conn_str), "%d", max_connections);
        
        /* Build arguments */
        char *argv[32];
        int argc = 0;
        
        /* Get webfsd path from environment variable set by Python */
        char *webfsd_path = getenv("HTTPIT_WEBFSD_PATH");
        if (!webfsd_path) {
            fprintf(stderr, "HTTPIT_WEBFSD_PATH not set\n");
            _exit(1);
        }
        
        argv[argc++] = webfsd_path;
        if (foreground) {
            argv[argc++] = "-F";  /* Run in foreground mode */
        }
        argv[argc++] = "-p";
        argv[argc++] = port_str;
        argv[argc++] = "-r";
        argv[argc++] = (char *)root;
        argv[argc++] = "-t";
        argv[argc++] = timeout_str;
        argv[argc++] = "-c";
        argv[argc++] = max_conn_str;
        
        /* Optional parameters */
        if (debug) argv[argc++] = "-d";
        if (no_listing) argv[argc++] = "-j";
        
        if (auth) {
            argv[argc++] = "-b";
            argv[argc++] = (char *)auth;
        }
        
        if (log_file) {
            argv[argc++] = "-l";
            argv[argc++] = (char *)log_file;
        }
        
        if (cors) {
            argv[argc++] = "-O";
            argv[argc++] = (char *)cors;
        }
        
        if (host) {
            argv[argc++] = "-n";
            argv[argc++] = (char *)host;
        }
        
        if (bind_ip) {
            argv[argc++] = "-i";
            argv[argc++] = (char *)bind_ip;
        }
        
        if (index_file) {
            argv[argc++] = "-f";
            argv[argc++] = (char *)index_file;
        }
        
        argv[argc] = NULL;
        
        /* Redirect stderr to /dev/null unless debugging */
        if (!getenv("HTTPIT_DEBUG")) {
            freopen("/dev/null", "w", stderr);
        }
        
        execvp(webfsd_path, argv);
        
        /* If we get here, exec failed */
        fprintf(stderr, "Failed to execute webfsd: %s\n", strerror(errno));
        _exit(1);
    }
    
    /* Parent process */
    server_running = 1;
    
    /* Give the server time to start */
    usleep(500000);  /* 500ms */
    
    /* If not in foreground mode, webfsd will fork and the initial process will exit */
    if (!foreground) {
        /* Wait for the initial process to exit (parent of daemon) */
        int status;
        pid_t wait_result = waitpid(server_pid, &status, 0);
        
        if (wait_result == server_pid) {
            if (WIFEXITED(status) && WEXITSTATUS(status) == 0) {
                /* Initial process exited successfully, daemon is running */
                /* We can't track the daemon PID easily, so mark as running */
                server_pid = -1;  /* Special value indicating daemon mode */
            } else {
                /* Initial process failed */
                server_running = 0;
                server_pid = 0;
                if (WIFEXITED(status)) {
                    PyErr_Format(WebfsdError, "Server failed to start (exit code %d)", WEXITSTATUS(status));
                } else {
                    PyErr_SetString(WebfsdError, "Server failed to start");
                }
                return NULL;
            }
        } else {
            server_running = 0;
            server_pid = 0;
            PyErr_SetString(WebfsdError, "Failed to wait for server process");
            return NULL;
        }
    } else {
        /* Foreground mode - check if the process is still running */
        if (kill(server_pid, 0) != 0) {
            server_running = 0;
            server_pid = 0;
            
            /* Try to get the exit status */
            int status;
            if (waitpid(server_pid, &status, WNOHANG) > 0) {
                if (WIFEXITED(status)) {
                    PyErr_Format(WebfsdError, "Server exited with code %d", WEXITSTATUS(status));
                } else if (WIFSIGNALED(status)) {
                    PyErr_Format(WebfsdError, "Server killed by signal %d", WTERMSIG(status));
                } else {
                    PyErr_SetString(WebfsdError, "Server failed to start");
                }
            } else {
                PyErr_SetString(WebfsdError, "Server failed to start");
            }
            return NULL;
        }
    }
    
    Py_RETURN_NONE;
}

/* Stop the server */
static PyObject *
webfsd_stop(PyObject *self, PyObject *args)
{
    if (!server_running) {
        PyErr_SetString(WebfsdError, "Server is not running");
        return NULL;
    }
    
    if (server_pid == -1) {
        /* Daemon mode - we can't easily stop it from here */
        PyErr_SetString(WebfsdError, "Cannot stop daemon mode server from Python. Use 'pkill httpit' or similar.");
        return NULL;
    }
    
    if (server_pid <= 0) {
        PyErr_SetString(WebfsdError, "Server is not running");
        return NULL;
    }
    
    /* Send SIGTERM to the server */
    if (kill(server_pid, SIGTERM) != 0) {
        PyErr_SetFromErrno(WebfsdError);
        return NULL;
    }
    
    /* Wait for the process to exit */
    int status;
    waitpid(server_pid, &status, 0);
    
    server_running = 0;
    server_pid = 0;
    
    Py_RETURN_NONE;
}

/* Check if server is running */
static PyObject *
webfsd_is_running(PyObject *self, PyObject *args)
{
    if (server_running) {
        if (server_pid == -1) {
            /* Daemon mode - assume it's running since we can't easily check */
            Py_RETURN_TRUE;
        } else if (server_pid > 0) {
            /* Foreground mode - check if process is still alive */
            if (kill(server_pid, 0) == 0) {
                Py_RETURN_TRUE;
            } else {
                /* Process died */
                server_running = 0;
                server_pid = 0;
            }
        }
    }
    Py_RETURN_FALSE;
}

/* Method definitions */
static PyMethodDef webfsd_methods[] = {
    {"start_server", (PyCFunction)webfsd_start, METH_VARARGS | METH_KEYWORDS,
     "Start the web server.\n\n"
     "Args:\n"
     "    port (int): Port to listen on (default: 8000)\n"
     "    root (str): Document root directory (default: '.')\n"
     "    debug (bool): Enable debug output\n"
     "    no_listing (bool): Disable directory listings\n"
     "    foreground (bool): Run in foreground mode (default: True)\n"
     "    auth (str): Basic auth in 'user:pass' format\n"
     "    log (str): Log file path\n"
     "    cors (str): CORS header value\n"
     "    host (str): Server hostname\n"
     "    bind_ip (str): Bind to specific IP address\n"
     "    timeout (int): Network timeout in seconds (default: 60)\n"
     "    max_connections (int): Maximum connections (default: 32)\n"
     "    index (str): Index file name\n"},
    {"stop_server", webfsd_stop, METH_NOARGS,
     "Stop the web server."},
    {"is_running", webfsd_is_running, METH_NOARGS,
     "Check if the server is running."},
    {NULL, NULL, 0, NULL}
};

/* Module definition */
static struct PyModuleDef webfsd_module = {
    PyModuleDef_HEAD_INIT,
    "_webfsd",
    "Fast HTTP server based on webfsd",
    -1,
    webfsd_methods
};

/* Module initialization */
PyMODINIT_FUNC
PyInit__webfsd(void)
{
    PyObject *m;
    
    m = PyModule_Create(&webfsd_module);
    if (m == NULL)
        return NULL;
    
    /* Create custom exception */
    WebfsdError = PyErr_NewException("_webfsd.WebfsdError", NULL, NULL);
    Py_XINCREF(WebfsdError);
    if (PyModule_AddObject(m, "WebfsdError", WebfsdError) < 0) {
        Py_XDECREF(WebfsdError);
        Py_CLEAR(WebfsdError);
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}