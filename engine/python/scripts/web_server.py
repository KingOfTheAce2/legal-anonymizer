#!/usr/bin/env python3
"""
HTTP server for running Legal Anonymizer in browser mode.

Provides REST API endpoints for anonymization when running without Tauri.
Also serves the React frontend build for a complete browser experience.

Start with: python scripts/web_server.py --port 8080
"""

import argparse
import json
import mimetypes
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anonymizer_engine.preset import Preset
from anonymizer_engine.layer1 import analyze_layer1_text
from langdetect import detect, DetectorFactory

# Ensure reproducible language detection
DetectorFactory.seed = 0

# Path to React dist folder (relative to this script)
STATIC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "apps", "desktop", "dist")
)


class CORSRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler with CORS support and static file serving."""

    def _set_cors_headers(self):
        """Set CORS headers for cross-origin requests."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json_response(self, data: Any, status: int = 200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_error_response(self, message: str, status: int = 400):
        """Send an error response."""
        self._send_json_response({"error": message}, status)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests — API routes then static files."""
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json_response({"status": "ok", "mode": "web"})

        elif parsed.path == "/api/info":
            self._send_json_response({
                "name": "Legal Anonymizer",
                "version": "0.1.0",
                "mode": "web",
                "layers_available": [1],
                "description": "GDPR-compliant document anonymization"
            })

        else:
            self._serve_static(parsed.path)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)

        if parsed.path == "/api/analyze":
            self._handle_analyze()
        else:
            self._send_error_response("Not found", 404)

    def _serve_static(self, path: str):
        """Serve static files from the React dist/ folder with SPA fallback."""
        if not os.path.isdir(STATIC_DIR):
            self._send_error_response(
                "Frontend not built. Run 'npm run build' in apps/desktop first.", 404
            )
            return

        # Normalize and prevent path traversal
        if path == "/":
            path = "/index.html"
        # Remove leading slash, normalize
        rel = os.path.normpath(path.lstrip("/"))
        # Security: ensure the resolved path is still under STATIC_DIR
        full = os.path.normpath(os.path.join(STATIC_DIR, rel))
        if not full.startswith(os.path.normpath(STATIC_DIR)):
            self._send_error_response("Forbidden", 403)
            return

        # If file exists, serve it; otherwise SPA fallback to index.html
        if not os.path.isfile(full):
            full = os.path.join(STATIC_DIR, "index.html")
            if not os.path.isfile(full):
                self._send_error_response("index.html not found", 404)
                return

        content_type, _ = mimetypes.guess_type(full)
        if content_type is None:
            content_type = "application/octet-stream"

        try:
            with open(full, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            self._send_error_response("File read error", 500)

    def _handle_analyze(self):
        """Handle text analysis request."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            text = data.get("text", "")
            preset_data = data.get("preset", {})

            if not text:
                self._send_error_response("No text provided")
                return

            # Build preset from request (use parse_preset-style filtering)
            import dataclasses
            known_fields = {f.name for f in dataclasses.fields(Preset)}
            filtered = {k: v for k, v in preset_data.items() if k in known_fields}
            # Fill defaults for required fields
            filtered.setdefault("preset_id", "web_default")
            filtered.setdefault("name", "Web Default")
            filtered.setdefault("layer", 1)
            filtered.setdefault("minimum_confidence", 75)
            filtered.setdefault("uncertainty_policy", "mask")
            filtered.setdefault("pseudonym_style", "neutral")
            filtered.setdefault("language_mode", "auto")
            filtered.setdefault("language", None)
            filtered.setdefault("entities_enabled", {})
            preset = Preset(**filtered)

            # Detect language
            language_mode = preset.language_mode
            if language_mode == "fixed" and preset.language:
                language = preset.language
            else:
                try:
                    language = detect(text)
                except Exception:
                    language = "en"

            # Process text using Layer 1
            redacted, findings, summary = analyze_layer1_text(text, preset, language)

            findings_list = []
            for f in findings:
                findings_list.append({
                    "entity_type": f.entity_type,
                    "detected_text": f.detected_text,
                    "start": f.start_pos,
                    "end": f.end_pos,
                    "confidence": f.confidence_score,
                    "action": f.redaction_action,
                    "pseudonym": f.pseudonym_value,
                })

            response = {
                "run_id": f"WEB_{id(findings)}",
                "run_folder": "(Web Mode)",
                "redacted_text": redacted,
                "summary": summary,
                "findings_count": len(findings),
                "language": language,
                "findings": findings_list,
            }

            self._send_json_response(response)

        except json.JSONDecodeError:
            self._send_error_response("Invalid JSON")
        except Exception as e:
            self._send_error_response(f"Processing error: {str(e)}", 500)

    def log_message(self, _format: str, *args):
        """Custom log format."""
        print(f"[WebServer] {args[0]} {args[1]} {args[2]}")


def main():
    parser = argparse.ArgumentParser(description="Legal Anonymizer Web Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    static_status = "available" if os.path.isdir(STATIC_DIR) else "NOT BUILT"

    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, CORSRequestHandler)

    print("=" * 60)
    print("  Legal Anonymizer Web Server")
    print(f"  Running at: http://{args.host}:{args.port}")
    print(f"  API endpoint: http://{args.host}:{args.port}/api/analyze")
    print(f"  Health check: http://{args.host}:{args.port}/health")
    print(f"  Frontend:     {static_status} ({STATIC_DIR})")
    print("=" * 60)
    print("\nPress Ctrl+C to stop.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.shutdown()


if __name__ == "__main__":
    main()
