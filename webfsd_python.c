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

/* Global state */
static PyObject *WebfsdError;
static volatile int server_running = 0;
static pthread_t server_thread;
static pid_t server_pid = 0;

/* Start the server by forking webfsd */
static PyObject *
webfsd_start(PyObject *self, PyObject *args, PyObject *kwargs)
{
    int port = 8000;
    const char *root = ".";
    const char *host = NULL;
    const char *index_file = NULL;
    const char *log_file = NULL;
    int enable_listing = 1;
    int max_connections = 32;
    int timeout = 60;
    
    static char *kwlist[] = {"port", "root", "host", "index", "log", 
                            "listing", "max_connections", "timeout", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|issssipi:start_server", kwlist,
                                     &port, &root, &host, &index_file, &log_file,
                                     &enable_listing, &max_connections, &timeout)) {
        return NULL;
    }
    
    if (server_running) {
        PyErr_SetString(WebfsdError, "Server is already running");
        return NULL;
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
        
        /* Find webfsd binary - try different locations */
        char *webfsd_path = NULL;
        if (access("./webfsd", X_OK) == 0) {
            webfsd_path = "./webfsd";
        } else if (access("/usr/local/bin/webfsd", X_OK) == 0) {
            webfsd_path = "/usr/local/bin/webfsd";
        } else if (access("/usr/bin/webfsd", X_OK) == 0) {
            webfsd_path = "/usr/bin/webfsd";
        } else {
            /* Try to find in PATH */
            webfsd_path = "webfsd";
        }
        
        argv[argc++] = webfsd_path;
        argv[argc++] = "-F";  /* Foreground mode */
        argv[argc++] = "-p";
        argv[argc++] = port_str;
        argv[argc++] = "-r";
        argv[argc++] = (char *)root;
        argv[argc++] = "-t";
        argv[argc++] = timeout_str;
        argv[argc++] = "-c";
        argv[argc++] = max_conn_str;
        
        if (host) {
            argv[argc++] = "-n";
            argv[argc++] = (char *)host;
        }
        
        if (index_file) {
            argv[argc++] = "-f";
            argv[argc++] = (char *)index_file;
        }
        
        if (log_file) {
            argv[argc++] = "-l";
            argv[argc++] = (char *)log_file;
        }
        
        if (!enable_listing) {
            argv[argc++] = "-j";
        }
        
        argv[argc] = NULL;
        
        /* Redirect stderr to /dev/null unless debugging */
        if (!getenv("FASTHTTP_DEBUG")) {
            freopen("/dev/null", "w", stderr);
        }
        
        execvp(webfsd_path, argv);
        
        /* If we get here, exec failed */
        fprintf(stderr, "Failed to execute webfsd: %s\n", strerror(errno));
        _exit(1);
    }
    
    /* Parent process */
    server_running = 1;
    
    /* Give the server a moment to start */
    usleep(100000);  /* 100ms */
    
    /* Check if the process is still running */
    if (kill(server_pid, 0) != 0) {
        server_running = 0;
        server_pid = 0;
        PyErr_SetString(WebfsdError, "Server failed to start");
        return NULL;
    }
    
    Py_RETURN_NONE;
}

/* Stop the server */
static PyObject *
webfsd_stop(PyObject *self, PyObject *args)
{
    if (!server_running || server_pid == 0) {
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
    if (server_running && server_pid > 0) {
        /* Double-check the process is still alive */
        if (kill(server_pid, 0) == 0) {
            Py_RETURN_TRUE;
        } else {
            /* Process died */
            server_running = 0;
            server_pid = 0;
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
     "    host (str): Server hostname\n"
     "    index (str): Index file name\n"
     "    log (str): Log file path\n"
     "    listing (bool): Enable directory listing (default: True)\n"
     "    max_connections (int): Maximum connections (default: 32)\n"
     "    timeout (int): Network timeout in seconds (default: 60)\n"},
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