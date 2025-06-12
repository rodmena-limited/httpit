#!/usr/bin/env python3
"""
Command-line interface for httpit server
"""

import argparse
import os
import sys
from pathlib import Path

from fasthttp import HTTPServer, __version__


def main():
    """Main entry point for command-line interface."""
    parser = argparse.ArgumentParser(
        description='httpit - Ultra-fast lightweight HTTP server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  httpit                    # Serve current directory on port 8000
  httpit 8080              # Serve current directory on port 8080
  httpit /path/to/files    # Serve specific directory on port 8000
  httpit . 3000            # Serve current directory on port 3000
  httpit -p 8080 -r /var/www --no-listing
  httpit -b user:pass -p 443 --ssl  # Basic auth on HTTPS
""")
    
    # Positional arguments for compatibility
    parser.add_argument('path_or_port', nargs='?', default='.',
                        help='Directory path or port number (default: current directory)')
    parser.add_argument('port_arg', nargs='?', type=int,
                        help='Port number when first argument is a path')
    
    # Network options
    parser.add_argument('-4', '--ipv4-only', action='store_true',
                        help='Use IPv4 only')
    parser.add_argument('-6', '--ipv6-only', action='store_true',
                        help='Use IPv6 only')
    parser.add_argument('-p', '--port', type=int, default=8000,
                        help='Port to listen on (default: 8000)')
    parser.add_argument('-i', '--bind-ip', type=str,
                        help='Bind to specific IP address')
    
    # Server behavior
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug output')
    parser.add_argument('-F', '--foreground', action='store_true', default=True,
                        help='Do not fork into background (default: True)')
    parser.add_argument('--no-foreground', dest='foreground', action='store_false',
                        help='Fork into background (daemon mode)')
    parser.add_argument('-s', '--syslog', action='store_true',
                        help='Enable syslog for start/stop/errors')
    parser.add_argument('-t', '--timeout', type=int, default=60,
                        help='Network timeout in seconds (default: 60)')
    parser.add_argument('-c', '--max-connections', type=int, default=32,
                        help='Maximum concurrent connections (default: 32)')
    
    # HTTP options
    parser.add_argument('-O', '--cors', type=str,
                        help='Set CORS header value')
    parser.add_argument('-n', '--host', type=str,
                        help='Server hostname')
    parser.add_argument('-N', '--canonical-name', action='store_true',
                        help='Use canonical name for host')
    parser.add_argument('-v', '--virtual-hosts', action='store_true',
                        help='Enable virtual hosts')
    
    # Directory options
    parser.add_argument('-r', '--root', type=str, default='.',
                        help='Document root directory (default: current directory)')
    parser.add_argument('-R', '--chroot', action='store_true',
                        help='Chroot to document root directory')
    parser.add_argument('-f', '--index', type=str,
                        help='Index file name')
    parser.add_argument('-j', '--no-listing', action='store_true',
                        help='Disable directory listings')
    parser.add_argument('-a', '--max-cached-dirs', type=int, default=128,
                        help='Maximum cached directories (default: 128)')
    
    # Logging
    parser.add_argument('-l', '--log', type=str,
                        help='Log file path')
    parser.add_argument('-L', '--flush-log', action='store_true',
                        help='Flush log after every line')
    
    # Files and security
    parser.add_argument('-m', '--mime-file', type=str,
                        help='MIME types file path')
    parser.add_argument('-k', '--pid-file', type=str,
                        help='PID file path')
    parser.add_argument('-b', '--auth', type=str,
                        help='Basic authentication (user:pass)')
    
    # Advanced features
    parser.add_argument('-e', '--expire-seconds', type=int, default=0,
                        help='Set expires header for cache control')
    parser.add_argument('-x', '--cgi-dir', type=str,
                        help='CGI script directory (relative to root)')
    parser.add_argument('-~', '--user-dir', type=str, dest='user_dir',
                        help='User home directory for ~user expansion')
    
    # Version
    parser.add_argument('--version', action='version',
                        version=f'httpit {__version__}')
    
    args = parser.parse_args()
    
    # Handle positional arguments for compatibility
    # If first argument is a number, treat it as port
    try:
        port_from_pos = int(args.path_or_port)
        # First argument is a port number
        port = port_from_pos
        root = '.'
    except ValueError:
        # First argument is a path
        root = args.path_or_port
        port = args.port_arg if args.port_arg else args.port
    
    # Override with named arguments if provided
    if args.port != 8000:  # User explicitly set --port
        port = args.port
    if args.root != '.':   # User explicitly set --root
        root = args.root
    
    # Resolve path
    root = os.path.abspath(root)
    
    # Validate
    if not os.path.exists(root):
        print(f"Error: Directory '{root}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    if not 1 <= port <= 65535:
        print(f"Error: Invalid port number {port}", file=sys.stderr)
        sys.exit(1)
    
    # Handle log file with flush option
    log_file = args.log
    flush_log = args.flush_log
    if args.flush_log and not args.log:
        print("Warning: --flush-log has no effect without --log", file=sys.stderr)
    
    # Check auth format
    if args.auth and ':' not in args.auth:
        print("Error: Authentication must be in 'user:pass' format", file=sys.stderr)
        sys.exit(1)
    
    # Create and start server
    try:
        server = HTTPServer(
            # Basic options
            port=port,
            root=root,
            # Network options
            ipv4_only=args.ipv4_only,
            ipv6_only=args.ipv6_only,
            bind_ip=args.bind_ip,
            # Server behavior
            debug=args.debug,
            foreground=args.foreground,
            syslog=args.syslog,
            timeout=args.timeout,
            max_connections=args.max_connections,
            # HTTP options
            cors=args.cors,
            host=args.host,
            canonical_name=args.canonical_name,
            virtual_hosts=args.virtual_hosts,
            # Directory options
            index=args.index,
            no_listing=args.no_listing,
            max_cached_dirs=args.max_cached_dirs,
            chroot=args.chroot,
            # Logging
            log=log_file,
            flush_log=flush_log,
            # Files and security
            mime_file=args.mime_file,
            pid_file=args.pid_file,
            auth=args.auth,
            # Advanced features
            expire_seconds=args.expire_seconds,
            cgi_dir=args.cgi_dir,
            user_dir=args.user_dir
        )
        
        print(f"Starting httpit server...")
        print(f"Serving directory: {root}")
        print(f"Listening on port: {port}")
        
        # Print enabled features
        if args.bind_ip:
            print(f"Bound to IP: {args.bind_ip}")
        if args.host:
            print(f"Hostname: {args.host}")
        if args.ipv4_only:
            print("IPv4 only mode")
        if args.ipv6_only:
            print("IPv6 only mode")
        if args.debug:
            print("Debug mode enabled")
        if args.no_listing:
            print("Directory listing: disabled")
        if args.auth:
            print("Basic authentication: enabled")
        if args.virtual_hosts:
            print("Virtual hosts: enabled")
        if args.chroot:
            print("Chroot: enabled")
        if args.cors:
            print(f"CORS header: {args.cors}")
        if args.expire_seconds:
            print(f"Cache expires: {args.expire_seconds} seconds")
        if args.cgi_dir:
            print(f"CGI directory: {args.cgi_dir}")
        if log_file:
            print(f"Logging to: {log_file}")
            
        print(f"\nServer running at http://localhost:{port}/")
        print("Press Ctrl+C to stop the server")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()