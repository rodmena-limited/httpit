# httpit

Ultra-fast, lightweight HTTP server for Python. httpit is a high-performance static file server built as a Python C extension, offering exceptional speed and efficiency.

## Installation

```bash
pip install httpit
```

## Quick Start

Serve files from the current directory on port 8000:

```bash
httpit
```

Serve files from a specific directory:

```bash
httpit /path/to/files
```

Serve on a custom port:

```bash
httpit 8080
```

Combine directory and port:

```bash
httpit /path/to/files 8080
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
httpit

# Serve on specific port
httpit 8080

# Serve specific directory
httpit /var/www/html

# Serve specific directory on specific port
httpit /var/www/html 8080
```

### Advanced Options

```bash
# Enable debug output
httpit -d

# Disable directory listing
httpit -F

# Enable access logging
httpit -l access.log

# Bind to specific IP
httpit -i 192.168.1.100

# Enable CORS headers
httpit -C

# Custom index file
httpit -I index.php

# Set connection timeout (seconds)
httpit -t 30

# Set maximum connections
httpit -c 100

# Run in background (daemon mode)
httpit -D

# Enable basic authentication
httpit -a username:password

# Serve specific virtual host
httpit -n www.example.com

# Custom mime types file
httpit -m /etc/mime.types
```

### Complete Example

```bash
# Production server with logging, authentication, and custom settings
httpit /var/www/html 443 \
  -D \
  -l /var/log/httpit/access.log \
  -a admin:secure_password \
  -F \
  -t 60 \
  -c 1000
```

## Python API

### Basic Usage

```python
from httpit import HTTPServer

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
from httpit import HTTPServer

with HTTPServer(port=8080) as server:
    print(f"Serving at http://localhost:{server.port}")
    input("Press Enter to stop...")
```

### Advanced Configuration

```python
from httpit import HTTPServer

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
from httpit import HTTPServer

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

httpit is designed for maximum performance:

- **Zero-copy file serving** using sendfile() system call
- **Minimal memory allocations** during request handling
- **Efficient event loop** with epoll/kqueue support
- **Smart caching** for directory listings and file metadata

Benchmark results show httpit can serve static files 2-5x faster than traditional Python web servers like http.server or SimpleHTTPServer.

## Use Cases

- **Static file serving** - Websites, documentation, downloads
- **Development server** - Quick testing and prototyping
- **Media streaming** - Video/audio files with range support
- **File sharing** - Simple LAN file server
- **CDN origin** - Backend for content delivery networks
- **Docker containers** - Minimal footprint for containerized apps

## Comparison with Alternatives

| Feature | httpit | http.server | nginx | Apache |
|---------|----------|-------------|-------|---------|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Memory Usage | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Features | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Python Integration | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |

## Security Considerations

- httpit is designed for serving static files only
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

# Or force kill any httpit processes
pkill -f httpit
```

### Permission Denied

If serving from system directories:

```bash
# Use sudo (not recommended)
sudo httpit /etc 8080

# Better: copy files to user directory
cp -r /etc/myapp ~/myapp
httpit ~/myapp
```

### No Output / Silent Exit

Run with debug flag to see errors:

```bash
httpit -d
```

## Contributing

httpit is a high-performance HTTP server for Python. For feature requests and issues, submit PRs to the [httpit repository](https://github.com/rodmena-limited/fasthttp) or visit https://httpit.rodmena.co.uk

## License

GNU General Public License v2.0 (GPLv2)

## Credits

- **httpit** is developed and maintained by [RODMENA LIMITED](https://rodmena.co.uk)
- High-performance C-based HTTP server with Python integration
- Visit https://httpit.rodmena.co.uk for documentation and support

## About RODMENA LIMITED

[RODMENA LIMITED](https://rodmena.co.uk) specializes in high-performance software solutions and web technologies. Visit us at https://rodmena.co.uk for more information about our services and products.
