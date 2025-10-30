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
from pathlib import Path


def main():
    # Parse port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    # Check if docs directory exists
    docs_dir = Path(__file__).parent.parent / "docs"
    if not docs_dir.exists():
        print(f"❌ Error: Documentation directory not found at {docs_dir}")
        print("   Please run 'wdlatlas generate' first to generate the documentation.")
        sys.exit(1)

    # Change to docs directory
    import os

    os.chdir(docs_dir)

    # Create server
    Handler = http.server.SimpleHTTPRequestHandler

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"🚀 Starting HTTP server for WDL documentation...")
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
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Error: Port {port} is already in use.")
            print(f"   Try a different port: python {sys.argv[0]} 8001")
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
