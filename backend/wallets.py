"""Wallet layer: the only place where vouchers move.

Three wallets, one per role: the NGO, a family and a shop. Each is its own
RGB wallet. The rest of the app only calls the methods of `Wallets`, so the
RGB person can swap `FakeWallets` for `RgbWallets` without touching anything else.

Amounts are whole voucher units (1 FOOD = 1 unit). No floats.
"""

import itertools
import time

WALLET_NAMES = ["ngo", "family", "shop"]


class Wallets:
    """Interface. Real and fake wallets both implement these methods."""

    def issue(self, wallet, ticker, amount):
        """Create `amount` new voucher tokens in `wallet`. Returns the asset id."""
        raise NotImplementedError

    def balance(self, wallet):
        """Settled voucher balance of one wallet."""
        raise NotImplementedError

    def send(self, from_wallet, to_wallet, amount):
        """Move vouchers. Returns a transfer id; the transfer may still be settling."""
        raise NotImplementedError

    def status(self, transfer_id):
        """Return "settling", "settled" or "failed"."""
        raise NotImplementedError

    def refresh(self):
        """Ask every wallet to look for incoming transfers."""
        raise NotImplementedError


class FakeWallets(Wallets):
    """In-memory wallets for building the app before RGB works.

    Transfers take `settle_seconds` to arrive, like a real Mutinynet block.
    """

    def __init__(self, settle_seconds=3):
        self.balances = {name: 0 for name in WALLET_NAMES}
        self.asset_id = None
        self.settle_seconds = settle_seconds
        self.transfers = {}
        self._ids = itertools.count(1)

    def issue(self, wallet, ticker, amount):
        self.balances[wallet] += amount
        self.asset_id = self.asset_id or f"rgb:fake-{ticker.lower()}"
        return self.asset_id

    def balance(self, wallet):
        self.refresh()
        return self.balances[wallet]

    def send(self, from_wallet, to_wallet, amount):
        if amount <= 0:
            raise ValueError("Amount must be more than zero.")
        self.refresh()
        if self.balances[from_wallet] < amount:
            raise ValueError(f"Not enough settled vouchers in the {from_wallet} wallet. "
                             "If vouchers just arrived, wait a few seconds for them to settle.")
        self.balances[from_wallet] -= amount
        transfer_id = f"fake-{next(self._ids)}"
        self.transfers[transfer_id] = {"to": to_wallet, "amount": amount,
                                       "settles_at": time.time() + self.settle_seconds,
                                       "status": "settling"}
        return transfer_id

    def status(self, transfer_id):
        self.refresh()
        return self.transfers[transfer_id]["status"]

    def refresh(self):
        now = time.time()
        for t in self.transfers.values():
            if t["status"] == "settling" and now >= t["settles_at"]:
                t["status"] = "settled"
                self.balances[t["to"]] += t["amount"]


class RgbWallets(Wallets):
    """Real RGB wallets on Mutinynet: one RGB Lightning Node per role, started with kaleido-cli.

    TODO (RGB person + Claude, once the nodes run):
      - one node per name in WALLET_NAMES, each on its own port (see `kaleido node list`)
      - issue():   POST /issueassetnia on the NGO node
      - send():    receiver node POST /rgbinvoice -> sender node sends to that invoice
                   -> both nodes POST /refreshtransfers until Settled
      - balance(): POST /assetbalance with the asset id
    API reference (Swagger): https://rgb-tools.github.io/rgb-lightning-node
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("RgbWallets is not written yet; run with MONEYFEST_WALLETS=fake")
