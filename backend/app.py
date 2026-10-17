"""Moneyfest server. Standard library only: nothing to install.

Run from the repo root:
    python3 backend/app.py
Then open http://127.0.0.1:8000

Settings (environment variables):
    MONEYFEST_WALLETS=fake|rgb   fake = in-memory wallets (default)
    MONEYFEST_AI=fake|qvac       fake = keyword rules (default), qvac = local model
    QVAC_URL                     default http://127.0.0.1:11434/v1/chat/completions
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))

import ai  # noqa: E402
from rules import Moneyfest  # noqa: E402
from wallets import FakeWallets, RgbWallets  # noqa: E402

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
HOST, PORT = "127.0.0.1", int(os.environ.get("PORT", "8000"))

if os.environ.get("MONEYFEST_WALLETS", "fake") == "rgb":
    wallets = RgbWallets()
else:
    wallets = FakeWallets(start_balances={"spending": 50000})  # 500 USDT to play with

app = Moneyfest(wallets, ai)


def cents(value):
    """Turn "12.50" or 12.5 from the page into 1250 cents."""
    return round(float(str(value).replace(",", ".")) * 100)


# Each route reads a JSON body and returns a JSON-able result.
ROUTES = {
    "/api/command": lambda b: app.command(b["text"]),
    "/api/rules": lambda b: app.set_rules(b["text"]),
    "/api/income": lambda b: app.receive_income(cents(b["amount"])),
    "/api/pay": lambda b: app.pay(b["merchant"], cents(b["amount"])),
    "/api/subscription": lambda b: app.subscription_due(b["name"], cents(b["amount"])),
    "/api/sweep": lambda b: app.sweep(),
    "/api/decide": lambda b: app.decide(str(b["id"]), bool(b["approve"])),
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/state":
            return self._send(200, app.state())
        if self.path in ("/", "/index.html"):
            with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        self._send(404, {"error": "not found"})

    def do_POST(self):
        route = ROUTES.get(self.path)
        if not route:
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, route(body))
        except Exception as e:  # show the error in the page instead of crashing
            self._send(400, {"error": str(e)})

    def log_message(self, *args):
        pass  # keep the terminal quiet


def watch_and_restart():
    """Run the server in a child process and restart it when a .py file changes.

    Page changes (web/) need no restart: the page is read fresh on every refresh.
    A restart resets the fake wallets. Turn this off with MONEYFEST_RELOAD=0.
    """
    import subprocess
    import time

    here = os.path.dirname(os.path.abspath(__file__))

    def stamps():
        return {f: os.path.getmtime(os.path.join(here, f)) for f in os.listdir(here) if f.endswith(".py")}

    env = dict(os.environ, MONEYFEST_CHILD="1")
    while True:
        before = stamps()
        child = subprocess.Popen([sys.executable, os.path.abspath(__file__)], env=env)
        try:
            while child.poll() is None and stamps() == before:
                time.sleep(1)
        except KeyboardInterrupt:
            child.terminate()
            return
        if child.poll() is None:
            print("Code changed: restarting...")
            child.terminate()
            child.wait()
        else:
            print("Server stopped with an error. Fix the code and save: it restarts by itself.")
            while stamps() == before:
                time.sleep(1)


if __name__ == "__main__":
    if os.environ.get("MONEYFEST_RELOAD", "1") != "0" and not os.environ.get("MONEYFEST_CHILD"):
        watch_and_restart()
        sys.exit(0)
    mode = f"wallets={os.environ.get('MONEYFEST_WALLETS', 'fake')}, ai={os.environ.get('MONEYFEST_AI', 'fake')}"
    print(f"Moneyfest running at http://{HOST}:{PORT}  ({mode})", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
