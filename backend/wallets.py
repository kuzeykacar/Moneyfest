"""Wallet layer: the only place where money moves.

Every envelope is its own RGB wallet. The rest of the app only calls the
functions of the `Wallets` interface below, so the RGB person can replace
`FakeWallets` with real rgb-lib code without touching anything else.

Amounts are always integers in cents (1250 = 12.50 USDT), never floats.
"""

import itertools
import time

# The wallets Moneyfest uses. "shop" stands for the outside world: shops and
# subscription services we pay. In the demo it is a separate wallet we control.
WALLET_NAMES = ["spending", "subscriptions", "savings", "shop"]


class Wallets:
    """Interface. Real and fake wallets both implement these four methods."""

    def balance(self, wallet):
        """Return the settled USDT balance of one wallet, in cents."""
        raise NotImplementedError

    def send(self, from_wallet, to_wallet, amount):
        """Move `amount` cents from one wallet to another.

        Returns a transfer id (string). The transfer may still be settling.
        """
        raise NotImplementedError

    def status(self, transfer_id):
        """Return "settling", "settled" or "failed"."""
        raise NotImplementedError

    def refresh(self):
        """Ask every wallet to check for new incoming transfers."""
        raise NotImplementedError


class FakeWallets(Wallets):
    """In-memory wallets for building the UI and rules before RGB works.

    Transfers take `settle_seconds` to settle, like a real Mutinynet block.
    """

    def __init__(self, start_balances=None, settle_seconds=3):
        self.balances = {name: 0 for name in WALLET_NAMES}
        if start_balances:
            self.balances.update(start_balances)
        self.settle_seconds = settle_seconds
        self.transfers = {}
        self._ids = itertools.count(1)

    def balance(self, wallet):
        self.refresh()
        return self.balances[wallet]

    def send(self, from_wallet, to_wallet, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.refresh()
        if self.balances[from_wallet] < amount:
            raise ValueError(f"Not enough settled money in {from_wallet}. "
                             "If you just moved money there, wait a few seconds for it to settle.")
        # The sender's money leaves at once, the receiver gets it when it settles.
        self.balances[from_wallet] -= amount
        transfer_id = f"fake-{next(self._ids)}"
        self.transfers[transfer_id] = {
            "to": to_wallet,
            "amount": amount,
            "settles_at": time.time() + self.settle_seconds,
            "status": "settling",
        }
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
    """Real RGB wallets on Mutinynet, using rgb-lib (Python bindings).

    TODO (RGB person): implement with rgb-lib-python.
      - one rgb-lib Wallet per name in WALLET_NAMES, each with its own data
        folder under data/wallets/<name> (git-ignored, back it up!)
      - send(): receiver creates an invoice (blind_receive or witness_receive),
        sender calls send(), then both refresh until the transfer is Settled
      - balance(): get_asset_balance(asset_id).settled, converted to cents
    Function list: github.com/RGB-Tools/rgb-lib/blob/master/bindings/uniffi/src/rgb-lib.udl
    Stuck transfers: github.com/RGB-Tools/rgb-lib/tree/master/docs
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("RgbWallets is not written yet; run with MONEYFEST_WALLETS=fake")
