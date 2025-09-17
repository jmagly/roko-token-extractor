#!/usr/bin/env python3
"""
Simple HTTP server for ROKO token data
Serves JSON files from the public directory with proper CORS headers and ETag support
"""

import os
import sys
import json
import hashlib
import argparse
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path

class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers and ETag support."""

    def get_etag_for_json(self, filepath):
        """Generate ETag based on JSON timestamp field."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Use the timestamp from the JSON content
                timestamp = data.get('timestamp', 0)
                # Also include file size for extra uniqueness
                file_size = os.path.getsize(filepath)
                # Create ETag from timestamp and size
                etag_source = f"{timestamp}-{file_size}"
                etag = hashlib.md5(etag_source.encode()).hexdigest()
                return f'"{etag}"', timestamp
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            # Fallback to file modification time
            stat = os.stat(filepath)
            etag_source = f"{stat.st_mtime}-{stat.st_size}"
            etag = hashlib.md5(etag_source.encode()).hexdigest()
            return f'"{etag}"', int(stat.st_mtime)

    def serve_json_file(self, path):
        """Serve a JSON file with ETag and cache headers."""
        etag, timestamp = self.get_etag_for_json(path)

        # Check If-None-Match header
        client_etag = self.headers.get('If-None-Match')
        if client_etag and client_etag == etag:
            # Content hasn't changed, return 304
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_header('Cache-Control', 'public, max-age=900, must-revalidate')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return

        # Serve the file with ETag
        try:
            with open(path, 'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('ETag', etag)
                # Cache for 15 minutes (same as update interval)
                self.send_header('Cache-Control', 'public, max-age=900, must-revalidate')
                self.send_header('Last-Modified', self.date_time_string(timestamp))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(content)
        except IOError:
            self.send_error(404, "File not found")

    def do_GET(self):
        """Handle GET requests with ETag support."""
        # Translate path to filesystem path
        path = self.translate_path(self.path)

        # Check if file exists
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return

        # Check if it's a directory
        if os.path.isdir(path):
            # Try to serve index file
            for index in ["index.html", "index.htm"]:
                index_path = os.path.join(path, index)
                if os.path.exists(index_path):
                    path = index_path
                    break
            else:
                # List directory
                super().do_GET()
                return

        # For JSON files (including symlinked files), use smart ETag
        if path.endswith('.json') or path.endswith('/price'):
            self.serve_json_file(path)
            return
        else:
            # For non-JSON files, use standard handling
            super().do_GET()

    def end_headers(self):
        """Add CORS headers to all responses (for non-JSON files)."""
        # Only add these if not already set (JSON files handle their own)
        if not self.path.endswith('.json'):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'public, max-age=3600')  # Cache other files for 1 hour
        super().end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'max-age=86400')  # Cache preflight for 24 hours
        self.end_headers()

    def log_message(self, format, *args):
        """Log HTTP requests with timestamp and cache status."""
        # Extract status code from format string
        status = format.split()[1] if ' ' in format else ''
        cache_indicator = ''
        if status == '304':
            cache_indicator = ' [CACHE HIT]'
        elif status == '200' and self.path.endswith('.json'):
            cache_indicator = ' [CACHE MISS]'

        sys.stdout.write("%s - - [%s] %s%s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args,
                          cache_indicator))
        sys.stdout.flush()

def run_server(port=8080, directory=None):
    """Run the HTTP server."""
    if directory:
        os.chdir(directory)

    handler = partial(CORSRequestHandler, directory=directory or '.')

    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)

    print(f"Starting ROKO data server on port {port}")
    print(f"Serving directory: {os.getcwd()}")
    print(f"Server URL: http://0.0.0.0:{port}")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ROKO Token Data Web Server')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port to serve on (default: 8080)')
    parser.add_argument('--directory', type=str,
                        default='/home/roctinam/production-deploy/roko-token-extractor/public',
                        help='Directory to serve')

    args = parser.parse_args()

    # Ensure the directory exists
    if not os.path.exists(args.directory):
        print(f"Error: Directory {args.directory} does not exist")
        sys.exit(1)

    run_server(port=args.port, directory=args.directory)