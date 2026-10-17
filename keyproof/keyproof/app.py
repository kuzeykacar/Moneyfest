"""KeyProof demo server: one page with the tenant's side and the landlord's side.

    python3 keyproof/app.py                      # fake RGB, keyword AI
    KEYPROOF_RGB=rgb KEYPROOF_AI=qvac .rgb-venv/bin/python keyproof/app.py   # real RGB + local AI

In real life each side runs on its own device. Here one server plays both, but the two sides
keep separate data: the landlord's side never receives the documents or the card values, only
what arrives in the landlord's RGB wallet (the token with the proof).

Stdlib only (plus cryptography, and rgb-lib in real mode). Restarts itself when a .py file changes.
"""

import base64
import datetime as dt
import hashlib
import json
import os
import secrets
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))

from cryptography import x509  # noqa: E402

import ai  # noqa: E402
import pdfsig  # noqa: E402
import rgb  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEB = os.path.join(ROOT, "web")
PORT = int(os.environ.get("PORT", "8010"))
TODAY = os.environ.get("KEYPROOF_TODAY", "2026-10-18")
SLOT_OF_TYPE = {1: "identity", 2: "income", 3: "occupation", 4: "savings", 5: "guarantor"}


def load_trust():
    root = x509.load_pem_x509_certificate(open(os.path.join(ROOT, "trust", "root.pem"), "rb").read())
    revoked = json.load(open(os.path.join(ROOT, "trust", "revoked.json")))
    issuers = []
    d = os.path.join(ROOT, "trust", "issuers")
    for f in sorted(os.listdir(d)):
        cert = x509.load_pem_x509_certificate(open(os.path.join(d, f), "rb").read())
        try:
            cert.verify_directly_issued_by(root)
        except Exception:
            continue
        if cert.serial_number in revoked:
            continue
        meta = pdfsig.issuer_info(cert)
        org = cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value
        issuers.append({"name": org, "role": meta["role"], "docTypes": meta["docTypes"], "zk": meta["zk"]})
    return root, revoked, issuers


class Demo:
    def __init__(self):
        self.lock = threading.RLock()
        self.root, self.revoked, self.trusted = load_trust()
        self.rgb = rgb.make(os.environ.get("KEYPROOF_RGB", "fake"))
        self.reset()

    def reset(self):
        self.request = None
        self.tenant = {"docs": {}, "log": [], "approval": None, "deposit": None, "pending_payment": None}
        self.landlord = {"log": [], "result": None, "deposit": None, "seen": None}

    def log(self, side, text, link=None):
        getattr(self, side)["log"].insert(0, {"t": time.strftime("%H:%M:%S"), "text": text, "link": link})

    # ------------------------------------------------------------- landlord
    def parse(self, text):
        out = ai.landlord_rules(text)
        return out

    def publish(self, rules, rent, deposit):
        rules = dict(rules)
        rules["today"] = TODAY
        rules["maxAgeDays"] = 90
        rules["requestId"] = str(secrets.randbits(60))
        self.request = {"rules": rules, "rent": int(rent or 0), "deposit": int(deposit or 0),
                        "published": time.strftime("%H:%M:%S")}
        self.landlord.update(result=None, deposit=None, seen=None)
        self.tenant.update(approval=None, deposit=None, pending_payment=None)
        ticked = [k for k, v in rules["checks"].items() if v]
        self.log("landlord", f"Published request #{rules['requestId'][-6:]}: checks {', '.join(ticked)}.")
        return self.request

    def inbox(self):
        """Look in the landlord's RGB wallet for the approval token."""
        appr = self.tenant.get("approval")
        if not appr:
            return {"arrived": False}
        tok = self.rgb.landlord_token(appr["asset_id"])
        if not tok:
            return {"arrived": False, "status": self.rgb.status(appr["tid"])}
        media = tok["media"]
        digest_ok = hashlib.sha256(media).hexdigest() == tok["digest"]
        if self.landlord["seen"] != appr["asset_id"]:
            self.landlord["seen"] = appr["asset_id"]
            self.log("landlord", "Approval token arrived in my RGB wallet and passed RGB validation.",
                     self.rgb.link(appr["tid"]))
        return {"arrived": True, "asset_id": appr["asset_id"], "digest_ok": digest_ok,
                "proof": json.loads(media), "details": tok["details"]}

    def result(self, body):
        prev = self.landlord.get("result")
        if prev and prev.get("ok") and prev.get("asset_id") == body.get("asset_id"):
            return prev                # already verified this token (e.g. page reloaded): don't ask twice
        self.landlord["result"] = body
        if body.get("ok"):
            self.log("landlord", "Proof verified: every requested check passed. I never saw the documents.")
            dep = self.request and self.request["deposit"]
            if dep:
                self.landlord["deposit"] = {"amount": dep, "status": "requested"}
                self.tenant["pending_payment"] = {"amount": dep, "to": "landlord"}
                self.log("landlord", f"My agent requested the deposit: {dep} tUSDT.")
                self.log("tenant", f"The landlord approved you and asks for a deposit of {dep} tUSDT. Confirm to pay.")
        else:
            self.log("landlord", "Proof rejected: " + body.get("reason", "invalid"))
        return body

    # ------------------------------------------------------------- tenant
    def upload(self, filename, data):
        r = pdfsig.verify_pdf(data, self.root, self.revoked)
        card = r.get("card")
        slot = SLOT_OF_TYPE.get(card["type"]) if card else None
        entry = {"file": filename, "ok": r["ok"], "checks": r["checks"], "issuer": r["issuer"], "slot": slot,
                 "card": card}
        if r["ok"]:
            self.tenant["docs"][slot] = entry
            self.log("tenant", f"{filename}: signature valid ({r['issuer']}). Kept on this device.")
        else:
            failed = next(c for c in r["checks"] if not c["ok"])
            self.log("tenant", f"{filename}: REJECTED, {failed['check']}: {failed['detail']}.")
        return entry

    def send_approval(self, proof, public_signals):
        req = self.request
        body = json.dumps({"proof": proof, "publicSignals": public_signals, "requestId": req["rules"]["requestId"]},
                          separators=(",", ":")).encode()
        details = {"app": "KeyProof", "request": req["rules"]["requestId"],
                   "checks": [k for k, v in req["rules"]["checks"].items() if v]}
        key = hashlib.sha256(body).hexdigest()
        issued = self.tenant.setdefault("issued", {})
        if key in issued:              # a retry after a failed send: reuse the token, don't issue a new one
            asset_id = issued[key]
        else:
            asset_id = self.rgb.issue_approval(body, details)
            issued[key] = asset_id
            self.log("tenant", f"Issued approval token on RGB ({asset_id[:22]}...), proof attached.")
        tid = self.rgb.send_approval(asset_id)
        self.tenant["approval"] = {"asset_id": asset_id, "tid": tid, "status": "settling"}
        self.log("tenant", "Sent the approval token to the landlord's wallet (on-chain).", self.rgb.link(tid))
        return self.tenant["approval"]

    def pay(self, yes):
        p = self.tenant.get("pending_payment")
        if not p:
            raise ValueError("No payment waiting.")
        self.tenant["pending_payment"] = None
        if not yes:
            self.log("tenant", "Deposit cancelled.")
            return None
        tid = self.rgb.pay(p["amount"])
        self.tenant["deposit"] = {"amount": p["amount"], "tid": tid, "status": "settling"}
        self.landlord["deposit"] = {"amount": p["amount"], "tid": tid, "status": "settling"}
        self.log("tenant", f"Paid the deposit: {p['amount']} tUSDT (RGB, on-chain).", self.rgb.link(tid))
        return self.tenant["deposit"]

    # ------------------------------------------------------------- state
    def state(self):
        appr = self.tenant.get("approval")
        if appr and appr["status"] != "settled":
            appr["status"] = self.rgb.status(appr["tid"])
        for side in ("tenant", "landlord"):
            d = getattr(self, side).get("deposit")
            if d and d.get("tid") and d["status"] != "settled":
                d["status"] = self.rgb.status(d["tid"])
                if d["status"] == "settled" and side == "landlord":
                    self.log("landlord", f"Deposit received: {d['amount']} tUSDT.", self.rgb.link(d["tid"]))
        tenant_docs = {k: {kk: vv for kk, vv in v.items()} for k, v in self.tenant["docs"].items()}
        return {
            "mode": {"rgb": "real" if self.rgb.real else "simulated",
                     "ai": "qvac" if not ai.USE_FAKE else "keywords"},
            "request": self.request,
            "tenant": {"docs": tenant_docs, "log": self.tenant["log"][:30], "approval": appr,
                       "deposit": self.tenant["deposit"], "pending_payment": self.tenant["pending_payment"]},
            "landlord": {"log": self.landlord["log"][:30], "result": self.landlord["result"],
                         "deposit": self.landlord["deposit"]},
            "balances": self.rgb.balances(),
            "trusted": self.trusted,
        }


DEMO = Demo()


def wallet_action(body):
    """Spending actions from the wallet page. Each one is only called after the user clicked Confirm."""
    r = DEMO.rgb
    if not r.real:
        raise ValueError("Wallet actions need real RGB mode (scripts/run_real.command).")
    a = body.get("action")
    if a == "send_btc":
        amount = int(body["amount"])
        if not 1000 <= amount <= 60000:
            raise ValueError("Amount must be between 1,000 and 60,000 sats.")
        txid = r.send_btc(body["from"], body["to"], amount)
        return {"txid": txid, "link": r.link(txid)}
    if a == "create_utxos":
        made = r.create_utxos(body["wallet"], int(body.get("num", 3)), int(body.get("size", 1500)))
        return {"created": made}
    if a == "issue_usd":
        if r.state.get("usd_asset"):
            raise ValueError("The demo stablecoin is already issued.")
        return {"asset_id": r.issue_usd(int(body.get("amount", 10000)))}
    if a == "send_usd":
        txid = r.send_usd(body["from"], body["to"], int(body["amount"]))
        return {"txid": txid, "link": r.link(txid)}
    raise ValueError("Unknown action.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/state":
            with DEMO.lock:
                return self._send(200, DEMO.state())
        if path == "/api/ping":
            return self._send(200, {"ok": True, "threads": [t.name for t in threading.enumerate()]})
        if path == "/api/wallets":
            if not DEMO.rgb.real:
                return self._send(200, {"real": False})
            return self._send(200, {"real": True, "wallets": DEMO.rgb.overview(sync="sync=1" in self.path), "fee_rate": DEMO.rgb.fee,
                                    "usd_asset": DEMO.rgb.state.get("usd_asset"), "explorer": rgb.EXPLORER})
        if path == "/api/landlord/inbox":
            with DEMO.lock:
                return self._send(200, DEMO.inbox())
        if path.startswith("/demo_docs/"):
            f = os.path.join(ROOT, "demo_docs", os.path.basename(path))
            if os.path.exists(f):
                return self._send(200, open(f, "rb").read(), "application/pdf")
        if path == "/":
            path = "/index.html"
        f = os.path.normpath(os.path.join(WEB, path.lstrip("/")))
        if f.startswith(WEB) and os.path.isfile(f):
            ctype = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json",
                     ".wasm": "application/wasm", ".css": "text/css"}.get(os.path.splitext(f)[1],
                                                                          "application/octet-stream")
            return self._send(200, open(f, "rb").read(), ctype)
        self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        path = self.path
        try:
            with DEMO.lock:
                if path == "/api/landlord/parse":
                    out = DEMO.parse(body.get("text", ""))
                elif path == "/api/landlord/publish":
                    out = DEMO.publish(body["rules"], body.get("rent"), body.get("deposit"))
                elif path == "/api/landlord/result":
                    out = DEMO.result(body)
                elif path == "/api/tenant/upload":
                    out = DEMO.upload(body.get("filename", "document.pdf"), base64.b64decode(body["pdf"]))
                elif path == "/api/tenant/sample":
                    name = os.path.basename(body["name"])
                    out = DEMO.upload(name, open(os.path.join(ROOT, "demo_docs", name), "rb").read())
                elif path == "/api/tenant/send":
                    out = DEMO.send_approval(body["proof"], body["publicSignals"])
                elif path == "/api/tenant/pay":
                    out = DEMO.pay(bool(body.get("yes")))
                elif path == "/api/wallets/action":
                    out = wallet_action(body)
                elif path == "/api/reset":
                    DEMO.reset()
                    out = {"ok": True}
                else:
                    return self._send(404, {"error": "not found"})
            self._send(200, out)
        except Exception as e:
            traceback.print_exc()
            self._send(400, {"error": str(e)})


def _watch():
    files = {}
    for d in (os.path.dirname(__file__),):
        for f in os.listdir(d):
            if f.endswith(".py"):
                files[os.path.join(d, f)] = os.path.getmtime(os.path.join(d, f))
    while True:
        time.sleep(1)
        for f, m in files.items():
            if os.path.exists(f) and os.path.getmtime(f) != m:
                print("code changed, restarting", flush=True)
                os.execv(sys.executable, [sys.executable] + sys.argv)


if __name__ == "__main__":
    import faulthandler
    _tb = open(os.path.join(ROOT, "data", "stacks.txt"), "w")
    faulthandler.dump_traceback_later(45, repeat=True, file=_tb)   # if a call hangs, see where
    threading.Thread(target=_watch, daemon=True).start()
    print(f"KeyProof running at http://127.0.0.1:{PORT}  (rgb={'real' if DEMO.rgb.real else 'simulated'}, "
          f"ai={'qvac' if not ai.USE_FAKE else 'keywords'})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
