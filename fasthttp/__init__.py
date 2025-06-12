"""
httpit - Ultra-fast lightweight HTTP server

High-performance C-based HTTP server with Python integration.
Developed and maintained by RODMENA LIMITED (https://rodmena.co.uk)
Visit https://httpit.rodmena.co.uk for documentation and support.
"""

from fasthttp.server import HTTPServer, WebfsdError

__version__ = '1.21.2'
__author__ = 'RODMENA LIMITED'
__email__ = 'info@rodmena.co.uk'
__url__ = 'https://github.com/rodmena-limited/fasthttp'
__all__ = ['HTTPServer', 'WebfsdError']