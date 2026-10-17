"""One-time setup of the three real RGB wallets on Mutinynet.

Run with the project's rgb-lib Python:
    .rgb-venv/bin/python backend/rgb_setup.py status   # addresses and balances
    .rgb-venv/bin/python backend/rgb_setup.py auto     # fund, create UTXOs, issue FOOD (repeatable)

Only the NGO wallet needs test bitcoin from https://faucet.mutinynet.com.
`auto` then shares it with the family and shop wallets, creates the UTXOs
RGB tokens sit on, and issues the FOOD vouchers once.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from rgb_wallets import ASSET_FILE, FEE_RATE, WALLET_NAMES, RgbNode  # noqa: E402

SHARE_SATS = 30_000        # test sats sent from the NGO to the family and the shop
MIN_SATS = 20_000          # a wallet with less vanilla than this needs funding
ISSUE = int(os.environ.get("ISSUE_AMOUNT", "1000"))


def say(msg):
    print(msg, flush=True)


def status(nodes):
    for name, n in nodes.items():
        b = n.btc()
        say(f"{name:7} address {n.address()}  vanilla {b['vanilla']} sats "
            f"(incoming {b['vanilla_future'] - b['vanilla']})  colored {b['colored']} sats")
    say("asset: " + (open(ASSET_FILE).read().strip() if os.path.exists(ASSET_FILE) else "not issued yet"))


def wait_for(cond, what, timeout=600):
    say(f"waiting for {what} (Mutinynet blocks come about every 30 s)...")
    start = time.time()
    while time.time() - start < timeout:
        if cond():
            return True
        time.sleep(10)
    say(f"timed out waiting for {what}")
    return False


def auto(nodes):
    ngo = nodes["ngo"]
    if ngo.btc()["vanilla"] + ngo.btc()["colored"] < MIN_SATS:
        say(f"\nNGO wallet needs test bitcoin. Send at least 100000 sats from https://faucet.mutinynet.com to:\n  {ngo.address()}")
        if not wait_for(lambda: ngo.btc()["vanilla"] >= MIN_SATS, "faucet bitcoin to arrive"):
            return

    for name in ("family", "shop"):
        n = nodes[name]
        b = n.btc()
        if b["vanilla"] + b["colored"] < MIN_SATS and b["vanilla_future"] < MIN_SATS:
            txid = ngo.wallet.send_btc(ngo.online, n.address(), SHARE_SATS, FEE_RATE, False)
            say(f"sent {SHARE_SATS} sats NGO -> {name}: {txid}")
    for name in ("family", "shop"):
        n = nodes[name]
        wait_for(lambda n=n: n.btc()["vanilla"] + n.btc()["colored"] >= MIN_SATS, f"{name} bitcoin to confirm")

    for name, n in nodes.items():
        if n.btc()["colored"] == 0:
            try:
                made = n.create_utxos()
                say(f"{name}: created {made} UTXOs for RGB")
            except Exception as e:
                say(f"{name}: create_utxos: {e}")
    wait_for(lambda: all(n.btc()["colored"] > 0 for n in nodes.values()), "UTXOs to confirm")

    if not os.path.exists(ASSET_FILE):
        from rgb_wallets import RgbWallets
        w = RgbWallets.__new__(RgbWallets)  # reuse the issue() code without starting threads
        w.nodes, w.asset_id = nodes, None
        import threading
        w.lock = threading.RLock()
        asset_id = w.issue("ngo", "FOOD", ISSUE)
        say(f"issued {ISSUE} FOOD: {asset_id}")
    status(nodes)
    say("\nSetup complete. Start the real app with scripts/run_real.command")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    nodes = {name: RgbNode(name) for name in WALLET_NAMES}
    status(nodes) if cmd == "status" else auto(nodes)
