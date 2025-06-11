#include <Python.h>
#include <signal.h>
#include <pthread.h>
#include "httpd.h"

/* External functions from webfsd.c that we need to expose */
extern int slisten;
extern char *doc_root;
extern char *listen_port;
extern int debug;
extern int dontdetach;
extern char *mimetypes;
extern int timeout;
extern int max_conn;
extern char *server_host;
extern char *indexhtml;
extern int no_listing;
extern char *logfile;
extern int usesyslog;
extern int virtualhosts;
extern char *userpass;
extern char *cgipath;
extern time_t now;

/* Function declarations from webfsd.c */
void init_mime(char *file, char *def);
void init_quote(void);
void* mainloop(void *thread_arg);

/* Global server thread */
static pthread_t server_thread;
static int server_running = 0;
static PyObject *WebfsdError;

/* Initialize the server with given parameters */
static int init_server(int port, const char *root_dir) {
    struct addrinfo ask, *res;
    int rc, opt = 1;
    char port_str[16];
    
    /* Set defaults */
    doc_root = (char *)root_dir;
    snprintf(port_str, sizeof(port_str), "%d", port);
    listen_port = strdup(port_str);
    dontdetach = 1;  /* Always run in foreground mode for Python */
    debug = 0;
    timeout = 60;
    max_conn = 32;
    
    /* Initialize server hostname */
    gethostname(server_host, sizeof(server_host));
    
    /* Setup socket */
    memset(&ask, 0, sizeof(ask));
    ask.ai_flags = AI_PASSIVE;
    ask.ai_socktype = SOCK_STREAM;
    ask.ai_family = PF_UNSPEC;
    
    if ((rc = getaddrinfo(NULL, listen_port, &ask, &res)) != 0) {
        PyErr_Format(WebfsdError, "getaddrinfo failed: %s", gai_strerror(rc));
        return -1;
    }
    
    /* Try IPv6 first */
    slisten = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (slisten == -1) {
        /* Try IPv4 */
        ask.ai_family = PF_INET;
        freeaddrinfo(res);
        if ((rc = getaddrinfo(NULL, listen_port, &ask, &res)) != 0) {
            PyErr_Format(WebfsdError, "getaddrinfo (IPv4) failed: %s", gai_strerror(rc));
            return -1;
        }
        slisten = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
        if (slisten == -1) {
            PyErr_SetString(WebfsdError, "Failed to create socket");
            freeaddrinfo(res);
            return -1;
        }
    }
    
    /* Set socket options */
    setsockopt(slisten, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
#ifdef SO_REUSEPORT
    setsockopt(slisten, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt));
#endif
    fcntl(slisten, F_SETFL, O_NONBLOCK);
    
    /* Bind */
    if (bind(slisten, res->ai_addr, res->ai_addrlen) == -1) {
        if (errno == EADDRINUSE) {
            PyErr_Format(WebfsdError, "Port %d is already in use", port);
        } else if (errno == EACCES || errno == EPERM) {
            PyErr_Format(WebfsdError, "Permission denied to bind to port %d", port);
        } else {
            PyErr_SetFromErrno(WebfsdError);
        }
        close(slisten);
        freeaddrinfo(res);
        return -1;
    }
    
    /* Listen */
    if (listen(slisten, 2 * max_conn) == -1) {
        PyErr_SetFromErrno(WebfsdError);
        close(slisten);
        freeaddrinfo(res);
        return -1;
    }
    
    freeaddrinfo(res);
    
    /* Initialize mime types and quote handling */
    init_mime(mimetypes, "text/plain");
    init_quote();
    
    return 0;
}

/* Python method: start_server */
static PyObject *webfsd_start(PyObject *self, PyObject *args, PyObject *kwargs) {
    int port = 8000;
    const char *root_dir = ".";
    const char *host = NULL;
    const char *index_file = NULL;
    const char *log_file = NULL;
    int enable_listing = 1;
    int max_connections = 32;
    int network_timeout = 60;
    
    static char *kwlist[] = {"port", "root", "host", "index", "log", 
                            "listing", "max_connections", "timeout", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|issssipi:start_server", kwlist,
                                     &port, &root_dir, &host, &index_file, &log_file,
                                     &enable_listing, &max_connections, &network_timeout)) {
        return NULL;
    }
    
    if (server_running) {
        PyErr_SetString(WebfsdError, "Server is already running");
        return NULL;
    }
    
    /* Apply settings */
    if (host) {
        strncpy(server_host, host, sizeof(server_host) - 1);
    }
    if (index_file) {
        indexhtml = strdup(index_file);
    }
    if (log_file) {
        logfile = strdup(log_file);
    }
    no_listing = !enable_listing;
    max_conn = max_connections;
    timeout = network_timeout;
    
    /* Initialize server */
    if (init_server(port, root_dir) < 0) {
        return NULL;
    }
    
    /* Start server thread */
    if (pthread_create(&server_thread, NULL, mainloop, NULL) != 0) {
        PyErr_SetString(WebfsdError, "Failed to create server thread");
        close(slisten);
        return NULL;
    }
    
    server_running = 1;
    
    Py_RETURN_NONE;
}

/* Python method: stop_server */
static PyObject *webfsd_stop(PyObject *self, PyObject *args) {
    if (!server_running) {
        PyErr_SetString(WebfsdError, "Server is not running");
        return NULL;
    }
    
    /* Signal the server to stop by closing the listen socket */
    if (slisten >= 0) {
        close(slisten);
        slisten = -1;
    }
    
    /* Wait for server thread to finish */
    pthread_join(server_thread, NULL);
    server_running = 0;
    
    Py_RETURN_NONE;
}

/* Python method: is_running */
static PyObject *webfsd_is_running(PyObject *self, PyObject *args) {
    return PyBool_FromLong(server_running);
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
PyMODINIT_FUNC PyInit__webfsd(void) {
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
    
    /* Initialize globals */
    server_host[0] = '\0';
    mimetypes = "/etc/mime.types";
    
    return m;
}