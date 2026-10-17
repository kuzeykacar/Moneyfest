"""One-time setup of the KeyProof RGB wallets on Mutinynet.

    .rgb-venv/bin/python keyproof/rgb_setup.py status
    .rgb-venv/bin/python keyproof/rgb_setup.py auto

`auto` (safe to repeat):
  1. finds test bitcoin: in the issuer wallet, or in the Moneyfest NGO wallet if it was funded there
  2. shares it with the tenant and landlord wallets
  3. creates the UTXOs RGB assets sit on
  4. issues 10,000 demo stablecoin "tUSDT" and sends 2,000 to the tenant (for the deposit)
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import rgb  # noqa: E402

SHARE = 40_000
MIN = 15_000
MONEYFEST_NGO = os.path.expanduser(os.environ.get("MONEYFEST_DIR", "~/Moneyfest")) + "/data/wallets/ngo"


def say(m):
    print(m, flush=True)


def btc(n):
    b = n["wallet"].get_btc_balance(n["online"], False)
    return b.vanilla.spendable, b.colored.spendable, b.vanilla.future


def status(r):
    for name, n in r.nodes.items():
        v, c, fut = btc(n)
        say(f"{name:9} {n['wallet'].get_address()}  vanilla {v}  (incoming {fut - v})  colored {c}")
    say("state: " + json.dumps(r.state))


def wait(cond, what, timeout=900):
    say(f"waiting for {what} (a Mutinynet block comes about every 30 s)...")
    t = time.time()
    while time.time() - t < timeout:
        if cond():
            return True
        time.sleep(10)
    say(f"timed out waiting for {what}")
    return False


def moneyfest_source(r):
    """The Moneyfest NGO wallet, if the team funded that address instead."""
    if not os.path.exists(os.path.join(MONEYFEST_NGO, "keys.json")):
        return None
    R = r.R
    keys = json.load(open(os.path.join(MONEYFEST_NGO, "keys.json")))
    data = R.WalletData(data_dir=MONEYFEST_NGO, bitcoin_network=r.network, database_type=R.DatabaseType.SQLITE,
                        max_allocations_per_utxo=5, supported_schemas=[R.AssetSchema.NIA])
    w = R.Wallet(data, R.SinglesigKeys(account_xpub_vanilla=keys["account_xpub_vanilla"],
                                       account_xpub_colored=keys["account_xpub_colored"], vanilla_keychain=None,
                                       master_fingerprint=keys["master_fingerprint"], mnemonic=keys["mnemonic"],
                                       witness_version=R.WitnessVersion.TAPROOT))
    online = w.go_online(R.OnlineOptions(indexer_url=r.indexer, skip_consistency_check=False,
                                         vanilla_sync_lookback=20))
    return {"wallet": w, "online": online}


def auto(r):
    issuer = r.nodes["issuer"]
    total = sum(btc(n)[0] + btc(n)[1] for n in r.nodes.values())
    if total < 3 * MIN:
        src = moneyfest_source(r)
        if src and btc(src)[0] >= 2 * SHARE + 5000:
            for name in ("issuer", "tenant", "landlord"):
                txid = src["wallet"].send_btc(src["online"], r.nodes[name]["wallet"].get_address(), SHARE, r.fee, False)
                say(f"Moneyfest NGO wallet -> {name}: {SHARE} sats ({txid})")
        else:
            say("\nNo test bitcoin yet. Send 150,000 sats from https://faucet.mutinynet.com to the issuer wallet:")
            say(f"  {issuer['wallet'].get_address()}")
            if not wait(lambda: btc(issuer)[0] >= 3 * MIN, "faucet bitcoin"):
                return
            for name in ("tenant", "landlord"):
                v, c, fut = btc(r.nodes[name])
                if v + c < MIN and fut < MIN:
                    txid = issuer["wallet"].send_btc(issuer["online"], r.nodes[name]["wallet"].get_address(),
                                                     SHARE, r.fee, False)
                    say(f"issuer -> {name}: {SHARE} sats ({txid})")
    for name, n in r.nodes.items():
        wait(lambda n=n: sum(btc(n)[:2]) >= MIN, f"{name} bitcoin to confirm")

    for name, n in r.nodes.items():
        if btc(n)[1] == 0:
            try:
                made = n["wallet"].create_utxos(n["online"], True, 5, 2000, r.fee, False)
                say(f"{name}: created {made} UTXOs for RGB")
            except Exception as e:
                say(f"{name}: create_utxos: {e}")
    wait(lambda: all(btc(n)[1] > 0 for n in r.nodes.values()), "UTXOs to confirm")

    if not r.state.get("usd_asset"):
        a = issuer["wallet"].issue_asset_nia("TUSDT", "Demo test stablecoin (not real money)", 0, [10_000])
        r.state["usd_asset"] = a.asset_id
        r._save()
        say(f"issued 10,000 tUSDT: {a.asset_id}")
    usd = r.state["usd_asset"]
    try:
        have = r.nodes["tenant"]["wallet"].get_asset_balance(usd).settled
    except Exception:
        have = 0
    if have == 0 and not r.state.get("tenant_funded"):
        txid = r._transfer("issuer", "tenant", usd, r.R.Assignment.FUNGIBLE(2000), None)
        r.state["tenant_funded"] = txid
        r._save()
        say(f"sent 2,000 tUSDT to the tenant: {txid}")
        wait(lambda: (r.refresh() or True) and r.status(txid) == "settled", "tUSDT to settle")
    status(r)
    say("\nSetup complete. Start the real app with scripts/run_real.command")


def invoice(r):
    """An RGB 'witness' invoice for the tenant: paste it in https://faucet.mutinynet.kaleidoswap.com
    to receive KaleidoSwap's test USDT (works on an empty wallet; the faucet also sends the sats for the UTXO)."""
    R = r.R
    rd = r.nodes["tenant"]["wallet"].witness_receive(None, R.Assignment.ANY(), int(time.time()) + 86400,
                                                       [r.proxy], 1)
    say("\nTenant RGB invoice for the KaleidoSwap faucet (choose USDT, option Witness):\n")
    say(rd.invoice)
    with open(os.path.join(rgb.ROOT, "tenant_invoice.txt"), "w") as f:
        f.write(rd.invoice + "\n")
    say("\nBitcoin address for https://faucet.mutinynet.com (issuer wallet):")
    say(r.nodes["issuer"]["wallet"].get_address())


def adopt_usdt(r):
    """Use KaleidoSwap's test USDT for the deposit if the tenant received it."""
    r.refresh()
    R = r.R
    nia = r.nodes["tenant"]["wallet"].list_assets([R.AssetSchema.NIA]).nia or []
    for a in nia:
        if a.ticker.upper().startswith("USDT") and a.balance.settled > 0:
            r.state["usd_asset"] = a.asset_id
            r.state["usd_ticker"] = a.ticker
            r._save()
            say(f"Deposit will use KaleidoSwap test {a.ticker}: {a.asset_id} (tenant has {a.balance.settled})")
            return True
    say("No settled USDT in the tenant wallet yet.")
    return False


if __name__ == "__main__":
    r = rgb.RealRgb(refresh_seconds=3600)
    cmd = (sys.argv[1:] or ["status"])[0]
    {"status": status, "auto": auto, "invoice": invoice, "usdt": adopt_usdt}[cmd](r)
