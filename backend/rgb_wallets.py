"""Real RGB wallets on Mutinynet, using rgb-lib 0.3.0b7 (Python bindings). No Docker.

Three wallets (ngo, family, shop) live in data/wallets/<name>/ (git-ignored).
Each wallet's test keys are stored in data/wallets/<name>/keys.json so the demo
survives restarts. TEST NETWORK ONLY: never put real funds in these wallets.

Transfers use blind receive: the receiver makes an invoice for a UTXO it owns,
the sender sends, both refresh until the transfer is SETTLED.
"""

import json
import os
import threading
import time

import rgb_lib as R

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
WALLET_DIR = os.path.join(ROOT, "wallets")
ASSET_FILE = os.path.join(ROOT, "asset.json")

NETWORK = R.BitcoinNetwork.SIGNET_CUSTOM          # Mutinynet
INDEXER = os.environ.get("RGB_INDEXER", "https://mutinynet.com/api")
PROXY = os.environ.get("RGB_PROXY", "rpcs://proxy.kaleidoswap.com/json-rpc")
FEE_RATE = int(os.environ.get("RGB_FEE_RATE", "2"))  # sat/vB
MIN_CONF = 1
WITNESS = R.WitnessVersion.TAPROOT

WALLET_NAMES = ["ngo", "family", "shop"]


def _keys(name):
    """Load this wallet's test keys, creating them the first time."""
    path = os.path.join(WALLET_DIR, name, "keys.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        k = R.generate_keys(NETWORK, WITNESS)
        with open(path, "w") as f:
            json.dump({"account_xpub_vanilla": k.account_xpub_vanilla,
                       "account_xpub_colored": k.account_xpub_colored,
                       "master_fingerprint": k.master_fingerprint,
                       "mnemonic": k.mnemonic}, f)
        os.chmod(path, 0o600)
    with open(path) as f:
        d = json.load(f)
    return R.SinglesigKeys(account_xpub_vanilla=d["account_xpub_vanilla"],
                           account_xpub_colored=d["account_xpub_colored"],
                           vanilla_keychain=None,
                           master_fingerprint=d["master_fingerprint"],
                           mnemonic=d["mnemonic"],
                           witness_version=WITNESS)


class RgbNode:
    """One rgb-lib wallet plus its online handle."""

    def __init__(self, name):
        self.name = name
        data = R.WalletData(data_dir=os.path.join(WALLET_DIR, name),
                            bitcoin_network=NETWORK,
                            database_type=R.DatabaseType.SQLITE,
                            max_allocations_per_utxo=5,
                            supported_schemas=[R.AssetSchema.NIA])
        self.wallet = R.Wallet(data, _keys(name))
        self.online = self.wallet.go_online(R.OnlineOptions(indexer_url=INDEXER,
                                                            skip_consistency_check=False,
                                                            vanilla_sync_lookback=20))

    def address(self):
        return self.wallet.get_address()

    def btc(self):
        b = self.wallet.get_btc_balance(self.online, False)
        return {"vanilla": b.vanilla.spendable, "colored": b.colored.spendable,
                "vanilla_future": b.vanilla.future}

    def create_utxos(self, num=5, size=2000):
        return self.wallet.create_utxos(self.online, True, num, size, FEE_RATE, False)

    def refresh(self):
        return self.wallet.refresh(self.online, None, [], False)


class RgbWallets:
    """Same interface as FakeWallets in wallets.py: issue, balance, send, status, refresh."""

    def __init__(self, background_refresh_seconds=10):
        self.nodes = {name: RgbNode(name) for name in WALLET_NAMES}
        self.lock = threading.RLock()
        self.asset_id = None
        if os.path.exists(ASSET_FILE):
            with open(ASSET_FILE) as f:
                self.asset_id = json.load(f).get("asset_id")
        self.transfers = {}   # transfer id -> {receiver, recipient_id}
        self._stop = False
        threading.Thread(target=self._refresh_loop, args=(background_refresh_seconds,), daemon=True).start()

    # ---------------------------------------------------------------- interface
    def issue(self, wallet, ticker, amount):
        if self.asset_id:
            raise ValueError(f"{ticker} vouchers are already issued on RGB ({self.asset_id}). "
                             "This demo token has a fixed supply.")
        with self.lock:
            asset = self.nodes[wallet].wallet.issue_asset_nia(ticker, f"{ticker} aid voucher", 0, [amount])
            self.asset_id = asset.asset_id
            with open(ASSET_FILE, "w") as f:
                json.dump({"asset_id": self.asset_id, "ticker": ticker}, f)
            return self.asset_id

    def balance(self, wallet):
        if not self.asset_id:
            return 0
        with self.lock:
            try:
                return self.nodes[wallet].wallet.get_asset_balance(self.asset_id).settled
            except Exception:
                return 0   # this wallet has not seen the asset yet

    def send(self, from_wallet, to_wallet, amount):
        if amount <= 0:
            raise ValueError("Amount must be more than zero.")
        if not self.asset_id:
            raise ValueError("No vouchers issued yet.")
        with self.lock:
            sender, receiver = self.nodes[from_wallet], self.nodes[to_wallet]
            spendable = sender.wallet.get_asset_balance(self.asset_id).spendable
            if spendable < amount:
                raise ValueError(f"Not enough settled vouchers in the {from_wallet} wallet "
                                 f"({spendable} spendable). Recent transfers may still be settling.")
            expiry = int(time.time()) + 3600
            rd = receiver.wallet.blind_receive(self.asset_id, R.Assignment.FUNGIBLE(amount),
                                               expiry, [PROXY], MIN_CONF)
            recipient = R.Recipient(recipient_id=rd.recipient_id, witness_data=None,
                                    assignment=R.Assignment.FUNGIBLE(amount), transport_endpoints=[PROXY])
            result = sender.wallet.send(sender.online, {self.asset_id: [recipient]}, False,
                                        FEE_RATE, MIN_CONF, expiry)
            tid = result.txid
            self.transfers[tid] = {"from": from_wallet, "to": to_wallet, "recipient_id": rd.recipient_id}
            return tid

    def status(self, transfer_id):
        t = self.transfers.get(transfer_id)
        if not t:
            return "unknown"
        with self.lock:
            for tr in self.nodes[t["to"]].wallet.list_transfers(self.asset_id):
                if tr.recipient_id == t["recipient_id"]:
                    if tr.status == R.TransferStatus.SETTLED:
                        return "settled"
                    if tr.status == R.TransferStatus.FAILED:
                        return "failed"
                    return "settling"
        return "settling"

    def refresh(self):
        with self.lock:
            for node in self.nodes.values():
                try:
                    node.refresh()
                except Exception as e:  # keep going: one wallet failing must not stop the others
                    print(f"refresh {node.name}: {e}", flush=True)

    def _refresh_loop(self, seconds):
        while not self._stop:
            time.sleep(seconds)
            self.refresh()
