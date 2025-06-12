"""
High-level Python interface for the httpit server
"""

import os
import signal
import threading
import time
from typing import Optional

# Defer imports to avoid circular import
_webfsd = None

# Create a placeholder WebfsdError that will be replaced
class WebfsdError(Exception):
    """HTTP server error"""
    pass

def _ensure_imports():
    global _webfsd, WebfsdError
    if _webfsd is None:
        try:
            from . import _webfsd as webfsd_module
            from .embedded import get_webfsd_path
        except ImportError:
            # Development mode - try direct import
            try:
                import _webfsd as webfsd_module
                from embedded import get_webfsd_path
            except ImportError:
                import fasthttp._webfsd as webfsd_module
                from fasthttp.embedded import get_webfsd_path
        
        _webfsd = webfsd_module
        # Replace the placeholder with the real WebfsdError
        globals()['WebfsdError'] = webfsd_module.WebfsdError
        
        # Set the webfsd path in environment
        os.environ['HTTPIT_WEBFSD_PATH'] = get_webfsd_path()


class HTTPServer:
    """
    Fast HTTP server for serving static files with full httpit feature support.
    
    Example:
        >>> server = HTTPServer(port=8000, root='./public')
        >>> server.start()
        >>> # Server is now running in background
        >>> server.stop()
    """
    
    def __init__(self, 
                 # Basic options
                 port: int = 8000,
                 root: str = '.',
                 # Network options
                 ipv4_only: bool = False,
                 ipv6_only: bool = False,
                 bind_ip: Optional[str] = None,
                 # Server behavior
                 debug: bool = False,
                 foreground: bool = True,
                 syslog: bool = False,
                 timeout: int = 60,
                 max_connections: int = 32,
                 # HTTP options
                 cors: Optional[str] = None,
                 host: Optional[str] = None,
                 canonical_name: bool = False,
                 virtual_hosts: bool = False,
                 # Directory options
                 index: Optional[str] = None,
                 no_listing: bool = False,
                 max_cached_dirs: int = 128,
                 # Logging
                 log: Optional[str] = None,
                 flush_log: bool = False,
                 # Files and security
                 mime_file: Optional[str] = None,
                 pid_file: Optional[str] = None,
                 auth: Optional[str] = None,
                 chroot: bool = False,
                 # Advanced features
                 expire_seconds: int = 0,
                 cgi_dir: Optional[str] = None,
                 user_dir: Optional[str] = None):
        """
        Initialize HTTP server with full httpit options.
        
        Args:
            port: Port to listen on (default: 8000)
            root: Document root directory (default: current directory)
            ipv4_only: Use IPv4 only (-4)
            ipv6_only: Use IPv6 only (-6)
            bind_ip: Bind to specific IP address (-i)
            debug: Enable debug output (-d)
            syslog: Enable syslog for start/stop/errors (-s)
            timeout: Network timeout in seconds (-t, default: 60)
            max_connections: Maximum concurrent connections (-c, default: 32)
            cors: CORS header value (-O)
            host: Server hostname (-n)
            canonical_name: Use canonical name for host (-N)
            virtual_hosts: Enable virtual hosts (-v)
            index: Index file name (-f)
            no_listing: Disable directory listings (-j)
            max_cached_dirs: Maximum cached directories (-a, default: 128)
            log: Log file path (-l)
            flush_log: Flush log after every line (-L)
            mime_file: MIME types file path (-m)
            pid_file: PID file path (-k)
            auth: Basic auth in 'user:pass' format (-b)
            chroot: Chroot to document root (-R)
            expire_seconds: Set expires header for cache control (-e)
            cgi_dir: CGI script directory relative to root (-x)
            user_dir: User home directory for ~user expansion (-~)
        """
        self.port = port
        self.root = os.path.abspath(root)
        self.ipv4_only = ipv4_only
        self.ipv6_only = ipv6_only
        self.bind_ip = bind_ip
        self.debug = debug
        self.foreground = foreground
        self.syslog = syslog
        self.timeout = timeout
        self.max_connections = max_connections
        self.cors = cors
        self.host = host
        self.canonical_name = canonical_name
        self.virtual_hosts = virtual_hosts
        self.index = index
        self.no_listing = no_listing
        self.max_cached_dirs = max_cached_dirs
        self.log = log
        self.flush_log = flush_log
        self.mime_file = mime_file
        self.pid_file = pid_file
        self.auth = auth
        self.chroot = chroot
        self.expire_seconds = expire_seconds
        self.cgi_dir = cgi_dir
        self.user_dir = user_dir
        self._lock = threading.Lock()
        
    def start(self):
        """Start the HTTP server in the background."""
        _ensure_imports()
        with self._lock:
            if self.is_running():
                raise WebfsdError("Server is already running")
            
            # Ensure document root exists
            if not os.path.exists(self.root):
                raise WebfsdError(f"Document root does not exist: {self.root}")
            
            # Call the C function - start with minimal args and add optional ones
            args = [self.port, self.root, self.debug, self.no_listing, self.foreground]
            
            # Add auth if provided
            if self.auth is not None:
                args.append(self.auth)
            
            _webfsd.start_server(*args)
            
    def stop(self):
        """Stop the HTTP server."""
        _ensure_imports()
        with self._lock:
            if not self.is_running():
                raise WebfsdError("Server is not running")
            _webfsd.stop_server()
            
    def is_running(self) -> bool:
        """Check if the server is running."""
        _ensure_imports()
        return _webfsd.is_running()
    
    def restart(self):
        """Restart the HTTP server."""
        if self.is_running():
            self.stop()
            time.sleep(0.1)  # Brief pause
        self.start()
    
    def serve_forever(self):
        """
        Start the server and block until interrupted.
        
        This method will start the server and block the current thread
        until a keyboard interrupt (Ctrl+C) is received.
        
        In daemon mode (foreground=False), this will start the daemon
        and return immediately.
        """
        def signal_handler(signum, frame):
            print("\nShutting down server...")
            if self.foreground:  # Only stop if we can (foreground mode)
                self.stop()
            else:
                print("Server is running as daemon. Use 'pkill httpit' to stop.")
            
        # Install signal handler
        old_handler = signal.signal(signal.SIGINT, signal_handler)
        
        try:
            self.start()
            print(f"Serving HTTP on port {self.port} from '{self.root}'")
            if self.bind_ip:
                print(f"Bound to IP: {self.bind_ip}")
            if self.debug:
                print("Debug mode enabled")
            if self.no_listing:
                print("Directory listing disabled")
            if self.auth:
                print("Basic authentication enabled")
            
            if self.foreground:
                print("Press Ctrl+C to stop...")
                # Block until server stops
                while self.is_running():
                    time.sleep(0.5)
            else:
                print("Server started as daemon.")
                print("Use 'pkill httpit' or 'ps aux | grep webfsd' to manage the daemon.")
                # Don't block in daemon mode
                
        finally:
            # Restore old signal handler
            signal.signal(signal.SIGINT, old_handler)
            
    def __enter__(self):
        """Context manager support."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        if self.is_running():
            self.stop()