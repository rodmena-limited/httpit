#!/usr/bin/env python3
"""
Command-line interface for FastHTTP server
"""

import argparse
import os
import sys
from pathlib import Path

from fasthttp import HTTPServer, __version__


def main():
    """Main entry point for command-line interface."""
    parser = argparse.ArgumentParser(
        description='FastHTTP - Ultra-fast lightweight HTTP server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fasthttp                    # Serve current directory on port 8000
  fasthttp 8080              # Serve current directory on port 8080
  fasthttp /path/to/files    # Serve specific directory on port 8000
  fasthttp . 3000            # Serve current directory on port 3000
  fasthttp -p 8080 -r /var/www --no-listing
""")
    
    # Positional arguments for compatibility
    parser.add_argument('path_or_port', nargs='?', default='.',
                        help='Directory path or port number (default: current directory)')
    parser.add_argument('port_arg', nargs='?', type=int,
                        help='Port number when first argument is a path')
    
    # Named arguments
    parser.add_argument('-p', '--port', type=int, default=8000,
                        help='Port to listen on (default: 8000)')
    parser.add_argument('-r', '--root', type=str, default='.',
                        help='Document root directory (default: current directory)')
    parser.add_argument('-n', '--host', type=str,
                        help='Server hostname')
    parser.add_argument('-f', '--index', type=str, default='index.html',
                        help='Index file name (default: index.html)')
    parser.add_argument('-l', '--log', type=str,
                        help='Log file path')
    parser.add_argument('-j', '--no-listing', action='store_true',
                        help='Disable directory listings')
    parser.add_argument('-c', '--max-connections', type=int, default=32,
                        help='Maximum concurrent connections (default: 32)')
    parser.add_argument('-t', '--timeout', type=int, default=60,
                        help='Network timeout in seconds (default: 60)')
    parser.add_argument('-v', '--version', action='version',
                        version=f'FastHTTP {__version__}')
    
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
    
    # Create and start server
    try:
        server = HTTPServer(
            port=port,
            root=root,
            host=args.host,
            index=args.index,
            log=args.log,
            listing=not args.no_listing,
            max_connections=args.max_connections,
            timeout=args.timeout
        )
        
        print(f"Starting FastHTTP server...")
        print(f"Serving directory: {root}")
        print(f"Listening on port: {port}")
        if args.host:
            print(f"Hostname: {args.host}")
        print(f"Directory listing: {'disabled' if args.no_listing else 'enabled'}")
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