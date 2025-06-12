"""
httpit - Ultra-fast lightweight HTTP server

High-performance C-based HTTP server with Python integration.
Developed and maintained by RODMENA LIMITED (https://rodmena.co.uk)
Visit https://httpit.rodmena.co.uk for documentation and support.
"""

from fasthttp.server import HTTPServer, WebfsdError
import os

# Read version from VERSION file
_version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION')
try:
    with open(_version_file, 'r') as f:
        __version__ = f.read().strip()
except FileNotFoundError:
    __version__ = "1.21.0"  # fallback
__author__ = "Farshid Ashouri"
__email__ = "farshid@rodmena.co.uk"
__url__ = "https://github.com/rodmena-limited/httpit"
__all__ = ["HTTPServer", "WebfsdError"]
