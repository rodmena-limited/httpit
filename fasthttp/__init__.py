"""
FastHTTP - Ultra-fast lightweight HTTP server

A Python wrapper around the high-performance webfsd C web server.
"""

from fasthttp.server import HTTPServer, WebfsdError

__version__ = '1.21.0'
__all__ = ['HTTPServer', 'WebfsdError']