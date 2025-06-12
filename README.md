# FastHTTP

Ultra-fast lightweight HTTP server for serving static files. FastHTTP is a Python wrapper around the high-performance webfsd C web server, providing blazing-fast static file serving with a clean Python API.

## Features

🚀 **Ultra-Fast Performance**
- Built on webfsd, optimized for serving static files
- Uses sendfile() for zero-copy file transmission
- Minimal memory footprint and CPU usage
- Handles thousands of concurrent connections

⚡ **Simple to Use**
- Install with `pip install fasthttp`
- One-line server startup: `fasthttp`
- Clean Python API and command-line interface

🛠 **Full Feature Set**
- Directory listing with caching
- Virtual host support
- IPv4/IPv6 support
- Keep-alive and pipelined requests
- Byte range serving (partial content)
- Basic authentication
- CGI support (GET requests)
- CORS headers
- Custom MIME types
- Access logging
- SSL/TLS support

## Quick Start

### Installation

#### Local Development
```bash
# Clone and install locally
git clone <repository>
cd webfsd
pip install -e .
```

#### From Source
```bash
# Build webfsd binary first
make

# Install Python package
pip install .
```

### Command Line Usage

```bash
# Serve current directory on port 8000
fasthttp

# Serve on custom port
fasthttp 8080

# Serve specific directory
fasthttp /path/to/files

# Serve directory on custom port
fasthttp /var/www 3000

# Advanced usage with authentication
fasthttp -p 443 -r /var/www -b admin:secret --no-listing

# Enable CORS and logging
fasthttp -p 8080 -O "*" -l access.log

# Virtual hosts with chroot
fasthttp -p 80 -R /var/www -v
```

### Python API

```python
from fasthttp import HTTPServer

# Basic usage
server = HTTPServer(port=8000, root='./public')
server.start()

# Server runs in background
# Do other work...

server.stop()

# Context manager
with HTTPServer(port=8080, no_listing=True) as server:
    # Server automatically stops when exiting context
    pass

# Full configuration
server = HTTPServer(
    port=8080,
    root='/var/www',
    auth='admin:secret',
    cors='*',
    virtual_hosts=True,
    no_listing=True,
    log='access.log',
    debug=True
)
server.serve_forever()  # Blocks until Ctrl+C
```

## Command Line Options

FastHTTP supports all webfsd command-line options:

### Network Options
- `-4, --ipv4-only` - Use IPv4 only
- `-6, --ipv6-only` - Use IPv6 only  
- `-p, --port` - Port to listen on (default: 8000)
- `-i, --bind-ip` - Bind to specific IP address

### Server Behavior
- `-d, --debug` - Enable debug output
- `-s, --syslog` - Enable syslog for start/stop/errors
- `-t, --timeout` - Network timeout in seconds (default: 60)
- `-c, --max-connections` - Maximum concurrent connections (default: 32)

### HTTP Options
- `-O, --cors` - Set CORS header value
- `-n, --host` - Server hostname
- `-N, --canonical-name` - Use canonical name for host
- `-v, --virtual-hosts` - Enable virtual hosts

### Directory Options
- `-r, --root` - Document root directory (default: current directory)
- `-R, --chroot` - Chroot to document root directory
- `-f, --index` - Index file name
- `-j, --no-listing` - Disable directory listings
- `-a, --max-cached-dirs` - Maximum cached directories (default: 128)

### Logging
- `-l, --log` - Log file path
- `-L, --flush-log` - Flush log after every line

### Files and Security
- `-m, --mime-file` - MIME types file path
- `-k, --pid-file` - PID file path
- `-b, --auth` - Basic authentication (user:pass)

### Advanced Features
- `-e, --expire-seconds` - Set expires header for cache control
- `-x, --cgi-dir` - CGI script directory (relative to root)
- `-~, --user-dir` - User home directory for ~user expansion

## Python API Reference

### HTTPServer Class

```python
class HTTPServer:
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
        user_dir: Optional[str] = None
    )
```

### Methods

- `start()` - Start the server in the background
- `stop()` - Stop the server
- `restart()` - Restart the server
- `is_running()` - Check if server is running
- `serve_forever()` - Start server and block until interrupted

## Examples

### Basic File Serving
```python
from fasthttp import HTTPServer

# Serve current directory
server = HTTPServer()
server.serve_forever()
```

### Static Website with Custom Settings
```python
server = HTTPServer(
    port=8080,
    root='./dist',
    index='index.html',
    cors='https://myapp.com',
    log='access.log',
    expire_seconds=3600  # 1 hour cache
)
server.serve_forever()
```

### Development Server with Authentication
```python
server = HTTPServer(
    port=3000,
    root='./app',
    auth='dev:password',
    debug=True,
    no_listing=True
)
server.serve_forever()
```

### Production Setup
```python
server = HTTPServer(
    port=80,
    root='/var/www/html',
    chroot=True,
    virtual_hosts=True,
    log='/var/log/access.log',
    pid_file='/var/run/fasthttp.pid',
    max_connections=100,
    timeout=30
)
server.serve_forever()
```

## Performance

FastHTTP is built for speed:

- **Zero-copy file serving** using sendfile() system call
- **Minimal overhead** - thin Python wrapper around optimized C code
- **Efficient memory usage** with directory listing cache
- **High concurrency** support with non-blocking I/O
- **Optimized compilation** with -O3 and platform-specific optimizations

Benchmark comparisons with other static file servers show FastHTTP performs competitively with nginx for static content while being much easier to deploy and configure.

## Requirements

- Python 3.7+
- Linux, macOS, or other POSIX-compatible OS
- C compiler (for building from source)

## License

FastHTTP is based on webfsd by Gerd Knorr, licensed under GPLv2.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Check the documentation
- Search existing issues
- Create a new issue with details about your problem

---

**FastHTTP** - Because serving static files should be fast and simple.