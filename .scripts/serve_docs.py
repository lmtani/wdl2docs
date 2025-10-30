#!/usr/bin/env python3
"""
Simple HTTP server for viewing generated documentation.

This script starts a local HTTP server to view the generated HTML documentation.
This is necessary because the documentation uses ES6 modules, which require
proper HTTP headers (CORS) that are not available when opening files directly
in the browser using the file:// protocol.

Usage:
    python serve_docs.py [port]

Default port: 8000
"""

import http.server
import socketserver
import sys
import webbrowser
import socket
from pathlib import Path


def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return False
        except OSError:
            return True


def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None


def main():
    # Parse port from command line or use default
    requested_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    # Check if requested port is in use
    if is_port_in_use(requested_port):
        print(f"⚠️  Warning: Port {requested_port} is already in use.")
        alternative_port = find_available_port(requested_port + 1)
        if alternative_port:
            print(f"✓ Using alternative port: {alternative_port}")
            port = alternative_port
        else:
            print(f"❌ Error: Could not find an available port.")
            print(f"   Please specify a different port: python {sys.argv[0]} <port>")
            sys.exit(1)
    else:
        port = requested_port

    # Check if docs directory exists
    docs_dir = Path(__file__).parent.parent / "docs"
    if not docs_dir.exists():
        print(f"❌ Error: Documentation directory not found at {docs_dir}")
        print("   Please run 'wdlatlas generate' first to generate the HTMLs.")
        sys.exit(1)

    # Change to docs directory
    import os

    os.chdir(docs_dir)

    # Create server with SO_REUSEADDR to allow port reuse
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Custom TCPServer class that allows address reuse
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    try:
        with ReusableTCPServer(("", port), Handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"🚀 Starting HTTP server for WDL Atlas...")
            print(f"📁 Serving directory: {docs_dir}")
            print(f"🌐 Open your browser at: {url}")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print()

            # Try to open browser automatically
            try:
                webbrowser.open(url)
                print("✓ Browser opened automatically")
            except:
                print("ℹ️  Could not open browser automatically. Please open manually.")

            print()
            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
