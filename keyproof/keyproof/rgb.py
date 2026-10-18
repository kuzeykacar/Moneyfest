"""RGB on Bitcoin (Mutinynet, on-chain) for KeyProof, using rgb-lib 0.3.0b7. No Docker.

Three test wallets in data/wallets/<name>/ (git-ignored keys):
  issuer   - stands in for a stablecoin issuer; issues the demo stablecoin "tUSDT"
  tenant   - issues the approval token and pays the deposit
  landlord - receives the approval token and the deposit

Approval token = RGB UDA (one unique token). Its media file is the ZK proof (JSON), so the
contract on Bitcoin commits to the proof's hash. The landlord's wallet receives and validates
the token (client-side validation), then the landlord's page checks the proof itself.

TEST NETWORK ONLY. Never put real funds in these wallets.
"""

import hashlib
import json
import os
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
WALLET_DIR = os.path.join(ROOT, "wallets")
STATE_FILE = os.path.join(ROOT, "rgb_state.json")
NAMES = ["issuer", "tenant", "landlord"]
EXPLORER = "https://mutinynet.com"


class FakeRgb:
    """Same interface, in memory, ~3 s 'blocks'. For building the app without test bitcoin."""

    real = False

    def __init__(self, settle=3):
        self.settle = settle
        self.transfers = {}
        self.tokens = {}        # asset_id -> {"owner", "media", "details"}
        self.usd = {"issuer": 10000, "tenant": 2000, "landlord": 0}
        self.n = 0

    def _tick(self):
        now = time.time()
        for t in self.transfers.values():
            if t["status"] == "settling" and now >= t["at"]:
                t["status"] = "settled"
                if t["kind"] == "token":
                    self.tokens[t["asset"]]["owner"] = t["to"]
                elif t["kind"] == "creds":
                    pass
                else:
                    self.usd[t["to"]] += t["amount"]

    def issue_approval(self, proof_bytes, details):
        self.n += 1
        aid = f"rgb:fake-approval-{self.n}"
        self.tokens[aid] = {"owner": "tenant", "media": proof_bytes, "details": details,
                            "digest": hashlib.sha256(proof_bytes).hexdigest()}
        return aid

    def send_approval(self, asset_id):
        self.n += 1
        tid = f"fake-tx-{self.n}"
        self.transfers[tid] = {"kind": "token", "asset": asset_id, "to": "landlord",
                               "at": time.time() + self.settle, "status": "settling"}
        return tid

    def pay(self, amount):
        if self.usd["tenant"] < amount:
            raise ValueError("Not enough tUSDT in the tenant wallet.")
        self.n += 1
        tid = f"fake-tx-{self.n}"
        self.usd["tenant"] -= amount
        self.transfers[tid] = {"kind": "usd", "amount": amount, "to": "landlord",
                               "at": time.time() + self.settle, "status": "settling"}
        return tid

    def status(self, tid):
        self._tick()
        return self.transfers.get(tid, {}).get("status", "unknown")

    def landlord_token(self, asset_id):
        """What the landlord's wallet holds for this token, or None if not arrived."""
        self._tick()
        t = self.tokens.get(asset_id)
        if not t or t["owner"] != "landlord":
            return None
        return {"media": t["media"], "digest": t["digest"], "details": t["details"]}

    def balances(self):
        self._tick()
        return {"tenant": self.usd["tenant"], "landlord": self.usd["landlord"]}

    def send_credentials(self, creds):
        """creds: list of (name, media_bytes). Issuer wallet -> tenant wallet, one transaction."""
        self.n += 1
        tid = f"fake-tx-{self.n}"
        ids = []
        for name, media in creds:
            self.n += 1
            aid = f"rgb:fake-credential-{self.n}"
            self.tokens[aid] = {"owner": "issuer", "media": media, "details": {"name": name}, "kind": "cred",
                                "digest": hashlib.sha256(media).hexdigest()}
            ids.append(aid)
        self.transfers[tid] = {"kind": "creds", "assets": ids, "to": "tenant",
                               "at": time.time() + self.settle, "status": "settling"}
        return ids, tid

    def tenant_credentials(self):
        self._tick()
        for t in self.transfers.values():
            if t.get("kind") == "creds" and t["status"] == "settled":
                for a in t["assets"]:
                    self.tokens[a]["owner"] = "tenant"
        return [{"asset_id": a, "media": t["media"], "digest_ok": True}
                for a, t in self.tokens.items() if t.get("kind") == "cred" and t["owner"] == "tenant"]

    def link(self, tid):
        return None


class RealRgb:
    """rgb-lib wallets on Mutinynet."""

    real = True

    def __init__(self, refresh_seconds=20):
        import rgb_lib as R  # noqa: only needed in real mode
        self.R = R
        self.network = R.BitcoinNetwork.SIGNET_CUSTOM
        self.indexer = os.environ.get("RGB_INDEXER", "https://esplora.signet.kaleidoswap.com")
        self.proxy = os.environ.get("RGB_PROXY", "rpcs://proxy.kaleidoswap.com/json-rpc")
        self.fee = int(os.environ.get("RGB_FEE_RATE", "2"))
        self.lock = threading.RLock()
        self.nodes = {n: self._open(n) for n in NAMES}
        self.state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}
        self.transfers = {}
        self.pending_until = 0      # refresh RGB transfers only while something is moving
        self._overview = (0, None)  # cached wallet page data (mutinynet.com rate-limits us)
        threading.Thread(target=self._loop, args=(refresh_seconds,), daemon=True).start()

    # ------------------------------------------------------------- wallets
    def _keys(self, name):
        R = self.R
        path = os.path.join(WALLET_DIR, name, "keys.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            k = R.generate_keys(self.network, R.WitnessVersion.TAPROOT)
            with open(path, "w") as f:
                json.dump({"account_xpub_vanilla": k.account_xpub_vanilla,
                           "account_xpub_colored": k.account_xpub_colored,
                           "master_fingerprint": k.master_fingerprint, "mnemonic": k.mnemonic}, f)
            os.chmod(path, 0o600)
        d = json.load(open(path))
        return R.SinglesigKeys(account_xpub_vanilla=d["account_xpub_vanilla"],
                               account_xpub_colored=d["account_xpub_colored"], vanilla_keychain=None,
                               master_fingerprint=d["master_fingerprint"], mnemonic=d["mnemonic"],
                               witness_version=R.WitnessVersion.TAPROOT)

    def _open(self, name):
        R = self.R
        data = R.WalletData(data_dir=os.path.join(WALLET_DIR, name), bitcoin_network=self.network,
                            database_type=R.DatabaseType.SQLITE, max_allocations_per_utxo=5,
                            supported_schemas=[R.AssetSchema.NIA, R.AssetSchema.UDA])
        w = R.Wallet(data, self._keys(name))
        online = w.go_online(R.OnlineOptions(indexer_url=self.indexer, skip_consistency_check=False,
                                             vanilla_sync_lookback=20))
        return {"wallet": w, "online": online}

    def _save(self):
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=1)

    def refresh(self):
        with self.lock:
            for name, n in self.nodes.items():
                try:
                    t0 = time.time()
                    n["wallet"].refresh(n["online"], None, [], False)
                    if time.time() - t0 > 5:
                        print(f"refresh {name} took {time.time() - t0:.0f}s", flush=True)
                except Exception as e:
                    print(f"refresh {name}: {e}", flush=True)

    def _loop(self, s):
        while True:
            time.sleep(s)
            if time.time() < self.pending_until:
                self.refresh()

    def busy(self, seconds=900):
        """Something was sent: keep refreshing for a while so it settles."""
        self.pending_until = max(self.pending_until, time.time() + seconds)

    def _transfer(self, sender, receiver, asset_id, assignment, receive_asset_id):
        R = self.R
        expiry = int(time.time()) + 3600
        # A wallet that doesn't know a unique token yet must ask for "any" assignment.
        recv_assignment = assignment if not assignment.is_non_fungible() else R.Assignment.ANY()
        rd = self.nodes[receiver]["wallet"].blind_receive(receive_asset_id, recv_assignment, expiry, [self.proxy], 1)
        rec = R.Recipient(recipient_id=rd.recipient_id, witness_data=None, assignment=assignment,
                          transport_endpoints=[self.proxy])
        s = self.nodes[sender]
        res = s["wallet"].send(s["online"], {asset_id: [rec]}, False, self.fee, 1, expiry)
        self.transfers[res.txid] = {"to": receiver, "asset": asset_id, "recipient_id": rd.recipient_id}
        self.busy()
        return res.txid

    # ------------------------------------------------------------- interface
    def issue_approval(self, proof_bytes, details):
        media_dir = os.path.join(ROOT, "proofs")
        os.makedirs(media_dir, exist_ok=True)
        path = os.path.join(media_dir, hashlib.sha256(proof_bytes).hexdigest()[:16] + ".json")
        with open(path, "wb") as f:
            f.write(proof_bytes)
        with self.lock:
            asset = self.nodes["tenant"]["wallet"].issue_asset_uda(
                "KEYOK", "KeyProof approval", json.dumps(details, separators=(",", ":")), 0, path, [])
        return asset.asset_id

    def send_approval(self, asset_id):
        with self.lock:
            return self._transfer("tenant", "landlord", asset_id, self.R.Assignment.NON_FUNGIBLE(), None)

    def pay(self, amount):
        usd = self.state.get("usd_asset")
        if not usd:
            raise ValueError("Demo stablecoin not issued yet: run scripts/rgb_setup.command")
        with self.lock:
            bal = self.nodes["tenant"]["wallet"].get_asset_balance(usd).spendable
            if bal < amount:
                raise ValueError(f"Not enough tUSDT in the tenant wallet ({bal} spendable).")
            return self._transfer("tenant", "landlord", usd, self.R.Assignment.FUNGIBLE(amount), None)

    def status(self, tid):
        t = self.transfers.get(tid)
        if not t:
            return "unknown"
        R = self.R
        with self.lock:
            for tr in self.nodes[t["to"]]["wallet"].list_transfers(t["asset"]):
                if tr.recipient_id == t["recipient_id"]:
                    if tr.status == R.TransferStatus.SETTLED:
                        return "settled"
                    if tr.status == R.TransferStatus.FAILED:
                        return "failed"
        return "settling"

    def landlord_token(self, asset_id):
        """Read the token from the landlord's own wallet: it only appears after rgb-lib validated it."""
        R = self.R
        with self.lock:
            try:
                bal = self.nodes["landlord"]["wallet"].get_asset_balance(asset_id)
            except Exception:
                return None
            if bal.settled < 1:
                return None
            assets = self.nodes["landlord"]["wallet"].list_assets([R.AssetSchema.UDA]).uda or []
            for a in assets:
                if a.asset_id == asset_id:
                    media = a.media or (a.token.media if a.token else None)
                    if media is None:
                        return None
                    with open(media.file_path, "rb") as f:
                        data = f.read()
                    return {"media": data, "digest": media.digest, "details": json.loads(a.details or "{}")}
        return None

    def send_credentials(self, creds):
        """The issuer wallet (standing in for bank / comune / university) issues one unique RGB token per
        credential, with the signed data card as its media, and sends them all to the tenant in ONE transaction."""
        R = self.R
        media_dir = os.path.join(ROOT, "credentials")
        os.makedirs(media_dir, exist_ok=True)
        expiry = int(time.time()) + 3600
        with self.lock:
            iss, ten = self.nodes["issuer"], self.nodes["tenant"]
            ids, recipient_map, recips = [], {}, []
            for name, media in creds:
                path = os.path.join(media_dir, hashlib.sha256(media).hexdigest()[:16] + ".json")
                with open(path, "wb") as f:
                    f.write(media)
                a = iss["wallet"].issue_asset_uda("KPCRED", name, json.dumps({"app": "KeyProof credential"}), 0, path, [])
                rd = ten["wallet"].blind_receive(None, R.Assignment.ANY(), expiry, [self.proxy], 1)
                recipient_map[a.asset_id] = [R.Recipient(recipient_id=rd.recipient_id, witness_data=None,
                                                         assignment=R.Assignment.NON_FUNGIBLE(),
                                                         transport_endpoints=[self.proxy])]
                ids.append(a.asset_id)
                recips.append(rd.recipient_id)
            res = iss["wallet"].send(iss["online"], recipient_map, False, self.fee, 1, expiry)
            for aid, rid in zip(ids, recips):
                self.transfers.setdefault(res.txid + ":" + aid, {"to": "tenant", "asset": aid, "recipient_id": rid})
            self.transfers[res.txid] = {"to": "tenant", "asset": ids[0], "recipient_id": recips[0]}
        self.busy()
        return ids, res.txid

    def tenant_credentials(self):
        """Credential tokens the tenant's wallet holds (only after rgb-lib validated them)."""
        R = self.R
        out = []
        with self.lock:
            w = self.nodes["tenant"]["wallet"]
            for a in (w.list_assets([R.AssetSchema.UDA]).uda or []):
                if a.ticker != "KPCRED" or a.balance.settled < 1:
                    continue
                media = a.media or (a.token.media if a.token else None)
                if not media:
                    continue
                data = open(media.file_path, "rb").read()
                out.append({"asset_id": a.asset_id, "media": data,
                            "digest_ok": hashlib.sha256(data).hexdigest() == media.digest})
        return out

    def balances(self):
        usd = self.state.get("usd_asset")
        if not usd:
            return {"tenant": 0, "landlord": 0}
        out = {}
        with self.lock:
            for n in ("tenant", "landlord"):
                try:
                    out[n] = self.nodes[n]["wallet"].get_asset_balance(usd).settled
                except Exception:
                    out[n] = 0
        return out

    def link(self, tid):
        return f"{EXPLORER}/tx/{tid}"

    # ------------------------------------------------------------- wallet page
    def overview(self, sync=False):
        """Everything the wallet page shows. Syncs with the network at most every 60 s."""
        now = time.time()
        if self._overview[1] is not None and not sync and now - self._overview[0] < 60:
            return self._overview[1]
        data = self._overview_now(sync=True)
        self._overview = (now, data)
        return data

    def _overview_now(self, sync):
        R = self.R
        out = []
        with self.lock:
            for name, n in self.nodes.items():
                w, online = n["wallet"], n["online"]
                b = w.get_btc_balance(online, not sync)
                assets = []
                lst = w.list_assets([R.AssetSchema.NIA, R.AssetSchema.UDA])
                for a in (lst.nia or []):
                    assets.append({"id": a.asset_id, "kind": "token", "ticker": a.ticker, "name": a.name,
                                   "settled": a.balance.settled, "future": a.balance.future})
                for a in (lst.uda or []):
                    assets.append({"id": a.asset_id, "kind": "unique token", "ticker": a.ticker, "name": a.name,
                                   "settled": a.balance.settled, "future": a.balance.future})
                txs = []
                try:
                    for t in w.list_transactions(online, True)[-8:]:  # uses the sync above
                        txs.append({"txid": t.txid, "received": t.received, "sent": t.sent,
                                    "fee": t.fee, "confirmed": t.confirmation_time is not None})
                except Exception as e:
                    print("list_transactions:", e, flush=True)
                try:
                    unspents = w.list_unspents(online, False, True)
                    slots = sum(1 for u in unspents if u.utxo.colorable)
                    free = sum(1 for u in unspents if u.utxo.colorable and not u.rgb_allocations)
                except Exception:
                    slots = free = None
                out.append({"name": name, "address": w.get_address(),
                            "btc": {"spendable": b.vanilla.spendable, "future": b.vanilla.future,
                                    "colored": b.colored.spendable, "colored_future": b.colored.future},
                            "rgb_slots": slots, "rgb_slots_free": free, "assets": assets,
                            "txs": list(reversed(txs))})
        return out

    def send_btc(self, frm, to, amount):
        print(f"send_btc {frm}->{to} {amount}: waiting for wallet lock", flush=True)
        with self.lock:
            print("send_btc: got lock, sending", flush=True)
            n = self.nodes[frm]
            txid = n["wallet"].send_btc(n["online"], self.nodes[to]["wallet"].get_address(), int(amount), self.fee, True)
        self._overview = (0, None)
        return txid

    def create_utxos(self, name, num, size):
        with self.lock:
            n = self.nodes[name]
            made = n["wallet"].create_utxos(n["online"], True, int(num), int(size), self.fee, True)
        self._overview = (0, None)
        return made

    def issue_usd(self, amount):
        with self.lock:
            a = self.nodes["issuer"]["wallet"].issue_asset_nia("TUSDT", "Demo test stablecoin (not real money)",
                                                               0, [int(amount)])
            self.state["usd_asset"] = a.asset_id
            self._save()
            return a.asset_id

    def send_usd(self, frm, to, amount):
        usd = self.state.get("usd_asset")
        if not usd:
            raise ValueError("No stablecoin chosen yet.")
        with self.lock:
            return self._transfer(frm, to, usd, self.R.Assignment.FUNGIBLE(int(amount)), None)


def make(mode):
    return RealRgb() if mode == "rgb" else FakeRgb()
