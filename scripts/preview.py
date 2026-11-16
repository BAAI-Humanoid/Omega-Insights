#!/usr/bin/env python3
"""Serve dist under the configured GitHub Pages project path."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BASE = json.loads((ROOT / "site.json").read_text(encoding="utf-8")).get("base_path", "").rstrip("/")


class Handler(SimpleHTTPRequestHandler):
    def route(self):
        route = urlsplit(self.path).path
        if BASE and route in ("/", BASE):
            self.send_response(302)
            self.send_header("Location", BASE + "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return False
        if BASE and not route.startswith(BASE + "/"):
            self.send_error(404)
            return False
        return True

    def translate_path(self, path):
        return super().translate_path(path[len(BASE):] if BASE else path)

    def do_GET(self):
        if self.route():
            super().do_GET()

    def do_HEAD(self):
        if self.route():
            super().do_HEAD()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not (DIST / "index.html").is_file():
        raise SystemExit("Run python scripts/build.py first.")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(DIST)))
    print(f"Preview: http://127.0.0.1:{server.server_port}{BASE}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
