"""OSWE-LAB: SSRF via URL fetch → internal-only admin service with flag."""
from __future__ import annotations

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Flask, request, Response

app = Flask(__name__)

FLAG = "OSWE{ssrf_chaining_lab_flag}"
if os.path.exists("/flag.txt"):
    with open("/flag.txt") as f:
        FLAG = f.read().strip()

INTERNAL_PORT = 9999
INTERNAL_TOKEN = "internal-only-secret"


class InternalHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        # Only meaningful when reached via SSRF (or loopback from container)
        if self.path.startswith("/internal/flag"):
            body = f"INTERNAL FLAG: {FLAG}\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode())
            return
        if self.path.startswith("/internal/secret"):
            body = f"token={INTERNAL_TOKEN}\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body.encode())
            return
        self.send_response(404)
        self.end_headers()


def start_internal():
    srv = HTTPServer(("127.0.0.1", INTERNAL_PORT), InternalHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()


@app.get("/")
def index():
    return f"""<!DOCTYPE html>
<html><body>
<h1>OSWE-LAB · SSRF Chaining</h1>
<p>POST <code>/fetch</code> with form/json field <code>url</code>. Server fetches URL and returns body
(naive SSRF — no allow-list).</p>
<p>Internal service binds <strong>127.0.0.1:{INTERNAL_PORT}</strong> only
(not published to host). Reach it via SSRF:</p>
<pre>
curl -s -X POST http://HOST:8115/fetch -d 'url=http://127.0.0.1:{INTERNAL_PORT}/internal/flag'
</pre>
<p>Also try: <code>/internal/secret</code> then chain mentally to other labs.</p>
<p>Health: <a href="/health">/health</a></p>
</body></html>"""


@app.get("/health")
def health():
    return {"status": "ok", "lab": "ssrf-chaining"}


@app.route("/fetch", methods=["GET", "POST"])
def fetch():
    url = (
        request.values.get("url")
        or (request.get_json(silent=True) or {}).get("url")
        or ""
    )
    if not url:
        return "Provide url= parameter\n", 400
    try:
        # VULNERABLE: attacker-controlled URL fetch, no blocklist
        req = Request(url, headers={"User-Agent": "OSWE-LAB-SSRF/1.0"})
        with urlopen(req, timeout=5) as resp:
            data = resp.read(65536)
            ctype = resp.headers.get("Content-Type", "text/plain")
        return Response(data, mimetype=ctype)
    except Exception as e:
        return f"fetch error: {e}\n", 502


@app.get("/public")
def public():
    return "public ok — no flag here\n"


if __name__ == "__main__":
    start_internal()
    # Write flag for container consistency
    try:
        open("/flag.txt", "w").write(FLAG + "\n")
    except OSError:
        pass
    app.run(host="0.0.0.0", port=8080)
