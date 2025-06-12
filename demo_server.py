#!/usr/bin/env python3
"""
Demo of FastHTTP Python API
"""

from fasthttp import HTTPServer

# Create server instance
server = HTTPServer(
    port=8080,
    root=".",
    index="index.html",
    listing=True,
    max_connections=100,
    timeout=30
)

print("Starting FastHTTP server...")
print("Server will listen on http://localhost:8080")
print("Press Ctrl+C to stop")

# Start server and block until interrupted
server.serve_forever()