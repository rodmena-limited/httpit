# FastHTTP

Ultra-fast, lightweight HTTP server for Python. FastHTTP is a high-performance static file server built as a Python C extension, offering exceptional speed and efficiency.

## Installation

```bash
pip install fasthttp
```

## Quick Start

Serve files from the current directory on port 8000:

```bash
fasthttp
```

Serve files from a specific directory:

```bash
fasthttp /path/to/files
```

Serve on a custom port:

```bash
fasthttp 8080
```

Combine directory and port:

```bash
fasthttp /path/to/files 8080
```

## Features

- 🚀 **Blazing Fast** - Built in C with zero-copy sendfile() support
- 🪶 **Lightweight** - Minimal memory footprint and dependencies
- 🔧 **Easy to Use** - Simple command-line interface and Python API
- 📁 **Directory Listing** - Browse directories with built-in HTML interface
- 🔒 **Security** - Basic authentication and access control support
- 🌐 **Modern Standards** - HTTP/1.1, IPv6, Keep-Alive, Range requests
- 📊 **Production Ready** - Access logging, daemon mode, custom MIME types

## Command Line Usage

### Basic Commands

```bash
# Serve current directory on port 8000 (default)
fasthttp

# Serve on specific port
fasthttp 8080

# Serve specific directory
fasthttp /var/www/html

# Serve specific directory on specific port
fasthttp /var/www/html 8080
```

### Advanced Options

```bash
# Enable debug output
fasthttp -d

# Disable directory listing
fasthttp -F

# Enable access logging
fasthttp -l access.log

# Bind to specific IP
fasthttp -i 192.168.1.100

# Enable CORS headers
fasthttp -C

# Custom index file
fasthttp -I index.php

# Set connection timeout (seconds)
fasthttp -t 30

# Set maximum connections
fasthttp -c 100

# Run in background (daemon mode)
fasthttp -D

# Enable basic authentication
fasthttp -a username:password

# Serve specific virtual host
fasthttp -n www.example.com

# Custom mime types file
fasthttp -m /etc/mime.types
```

### Complete Example

```bash
# Production server with logging, authentication, and custom settings
fasthttp /var/www/html 443 \
  -D \
  -l /var/log/fasthttp/access.log \
  -a admin:secure_password \
  -F \
  -t 60 \
  -c 1000
```

## Python API

### Basic Usage

```python
from fasthttp import HTTPServer

# Create and start server
server = HTTPServer(port=8080, root="/var/www/html")
server.start()

# Check if running
if server.is_running():
    print("Server is running")

# Stop server
server.stop()
```

### Context Manager

```python
from fasthttp import HTTPServer

with HTTPServer(port=8080) as server:
    print(f"Serving at http://localhost:{server.port}")
    input("Press Enter to stop...")
```

### Advanced Configuration

```python
from fasthttp import HTTPServer

server = HTTPServer(
    port=8080,
    root="/var/www/html",
    host="www.example.com",      # Virtual host
    bind_ip="0.0.0.0",           # Bind address
    debug=True,                   # Debug output
    no_listing=True,             # Disable directory listing
    auth="user:pass",            # Basic auth
    log="access.log",            # Access log
    cors="*",                    # CORS headers
    timeout=60,                  # Connection timeout
    max_connections=1000,        # Max concurrent connections
    index="index.php"            # Index file
)

server.start()
```

### Running in Background Thread

```python
import threading
from fasthttp import HTTPServer

server = HTTPServer(port=8080)

# Start in background thread
thread = threading.Thread(target=server.serve_forever)
thread.daemon = True
thread.start()

# Your application continues running
# ...

# Stop when done
server.stop()
```

## Performance

FastHTTP is designed for maximum performance:

- **Zero-copy file serving** using sendfile() system call
- **Minimal memory allocations** during request handling
- **Efficient event loop** with epoll/kqueue support
- **Smart caching** for directory listings and file metadata

Benchmark results show FastHTTP can serve static files 2-5x faster than traditional Python web servers like http.server or SimpleHTTPServer.

## Use Cases

- **Static file serving** - Websites, documentation, downloads
- **Development server** - Quick testing and prototyping
- **Media streaming** - Video/audio files with range support
- **File sharing** - Simple LAN file server
- **CDN origin** - Backend for content delivery networks
- **Docker containers** - Minimal footprint for containerized apps

## Comparison with Alternatives

| Feature | FastHTTP | http.server | nginx | Apache |
|---------|----------|-------------|-------|---------|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Memory Usage | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Features | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Python Integration | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |

## Security Considerations

- FastHTTP is designed for serving static files only
- Always use `-F` flag to disable directory listing in production
- Use authentication (`-a`) for sensitive content
- Run as non-root user when possible
- Consider using a reverse proxy for HTTPS in production

## Troubleshooting

### Port Already in Use

If you see "Port already in use" error:

```bash
# Find process using the port
lsof -i :8000

# Or force kill any fasthttp processes
pkill -f fasthttp
```

### Permission Denied

If serving from system directories:

```bash
# Use sudo (not recommended)
sudo fasthttp /etc 8080

# Better: copy files to user directory
cp -r /etc/myapp ~/myapp
fasthttp ~/myapp
```

### No Output / Silent Exit

Run with debug flag to see errors:

```bash
fasthttp -d
```

## Contributing

FastHTTP is a Python wrapper around the webfsd project. For core server improvements, contribute to the webfsd project. For Python-specific enhancements, submit issues and PRs to the FastHTTP repository.

## License

GNU General Public License v2.0 (GPLv2)

## Credits

FastHTTP is built on top of [webfsd](http://linux.bytesex.org/misc/webfs.html) by Gerd Hoffmann.