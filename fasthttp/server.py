"""
High-level Python interface for the webfsd server
"""

import os
import signal
import threading
import time
from typing import Optional

try:
    from fasthttp import _webfsd
except ImportError:
    # Development mode - try parent directory
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from fasthttp import _webfsd

WebfsdError = _webfsd.WebfsdError


class HTTPServer:
    """
    Fast HTTP server for serving static files.
    
    Example:
        >>> server = HTTPServer(port=8000, root='./public')
        >>> server.start()
        >>> # Server is now running in background
        >>> server.stop()
    """
    
    def __init__(self, 
                 port: int = 8000,
                 root: str = '.',
                 host: Optional[str] = None,
                 index: str = 'index.html',
                 log: Optional[str] = None,
                 listing: bool = True,
                 max_connections: int = 32,
                 timeout: int = 60):
        """
        Initialize HTTP server.
        
        Args:
            port: Port to listen on (default: 8000)
            root: Document root directory (default: current directory)
            host: Server hostname (default: auto-detect)
            index: Index file name (default: index.html)
            log: Log file path (default: no logging)
            listing: Enable directory listing (default: True)
            max_connections: Maximum concurrent connections (default: 32)
            timeout: Network timeout in seconds (default: 60)
        """
        self.port = port
        self.root = os.path.abspath(root)
        self.host = host
        self.index = index
        self.log = log
        self.listing = listing
        self.max_connections = max_connections
        self.timeout = timeout
        self._lock = threading.Lock()
        
    def start(self):
        """Start the HTTP server in the background."""
        with self._lock:
            if self.is_running():
                raise WebfsdError("Server is already running")
            
            # Ensure document root exists
            if not os.path.exists(self.root):
                raise WebfsdError(f"Document root does not exist: {self.root}")
            
            # Start the server
            kwargs = {
                'port': self.port,
                'root': self.root,
                'listing': self.listing,
                'max_connections': self.max_connections,
                'timeout': self.timeout,
            }
            
            if self.host:
                kwargs['host'] = self.host
            if self.index:
                kwargs['index'] = self.index
            if self.log:
                kwargs['log'] = self.log
            
            _webfsd.start_server(**kwargs)
            
    def stop(self):
        """Stop the HTTP server."""
        with self._lock:
            if not self.is_running():
                raise WebfsdError("Server is not running")
            _webfsd.stop_server()
            
    def is_running(self) -> bool:
        """Check if the server is running."""
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
        """
        def signal_handler(signum, frame):
            print("\nShutting down server...")
            self.stop()
            
        # Install signal handler
        old_handler = signal.signal(signal.SIGINT, signal_handler)
        
        try:
            self.start()
            print(f"Serving HTTP on port {self.port} from '{self.root}'")
            print("Press Ctrl+C to stop...")
            
            # Block until server stops
            while self.is_running():
                time.sleep(0.5)
                
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