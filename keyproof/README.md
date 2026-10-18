# 🔑 KeyProof

**Prove you qualify for a flat without showing your documents.**

To rent a room, tenants send landlords their full bank statements, ID and contracts.
Landlords only need a few yes/no answers. KeyProof lets the tenant prove those answers
from documents the bank, the city office or the university already signed,
and lets the landlord trust them without seeing any private data.

Built during the *Agentic Dollars on Bitcoin* hackathon (Turin, 17–18 Oct 2026) by team **Moneyfest**.

## How it works

```
 Issuer (bank, comune, university)      signs the PDF + a small data card inside it
        │
 Tenant's laptop                        1. checks the PDF signature (not changed, trusted issuer,
        │                                  still valid, right issuer)
        │                               2. makes a zero-knowledge proof: "every ticked check passes"
        │                               3. issues an RGB token on Bitcoin with the proof attached
        ▼
 Landlord's laptop                      4. RGB wallet receives + validates the token
                                        5. checks the proof against ITS OWN rules and trusted issuers
                                        6. sees ✓ / ✗ per check, nothing else
                                        7. its agent asks for the deposit; tenant confirms; stablecoin moves on RGB
```

| Part | Job | Decides? |
|---|---|---|
| Issuer signature | the data is real | yes |
| ZK proof (circom + Groth16) | the data passes the rules, privately | yes |
| RGB on Bitcoin (on-chain) | who owns the approval, single use, timestamp; carries the deposit | yes |
| Local AI (QVAC, Qwen3.5 4B) | turns the landlord's sentence into checkboxes | **never** |
| Human | confirms sending the approval and paying | yes |

## The 5 checks a landlord can tick

| Check | Signed source | The landlord learns |
|---|---|---|
| Identity, 18+ | ID office / municipality | adult ✓, same person on all documents |
| Monthly income ≥ X | bank / payslip | income ≥ X ✓ (never the amount) |
| Occupation | university or employer | student / employed ✓, lasts until the lease ends |
| Savings ≥ X | bank balance certificate | savings ≥ X ✓ |
| Guarantor's income ≥ X | guarantor's bank | guarantor ✓ |

Only **digitally signed** documents are accepted. No valid signature, no approval:
no "looks real" guessing, no metadata checks.

## Status (Sunday 18 Oct, 01:00)

| Part | Status |
|---|---|
| Signed demo PDFs (5 + 1 edited fake) | ✅ independent tool (poppler `pdfsig`) reports "Signature is Valid" |
| Signature check (4 checks) | ✅ fake, untrusted issuer, wrong issuer, appended content all rejected |
| ZK circuit (45k constraints) + Groth16 setup | ✅ proof ~8 s in the browser, 0.7 KB; easier rules or edited data are rejected |
| Local AI (QVAC) filling the landlord form | ✅ keyword rules as backup if QVAC is off |
| Web app: landlord + tenant panels | ✅ full flow tested end to end with simulated RGB |
| Real RGB wallets on Mutinynet | ✅ funded (faucet), RGB slots created, 10,000 TUSDT issued, 2,000 sent to the tenant |
| Approval token + deposit on real RGB | ✅ settled on Mutinynet ([approval](https://mutinynet.com/tx/01bc272eb2a29629ac95907cca4377dcdf17f83af8d793ecd02324b69daa6655), [deposit](https://mutinynet.com/tx/899d3dc81d352a13112b651381921eeb1b1f4fb7f9d3210bcf1811b8b66e83ba)) |
| Wallet page (`/wallets.html`) | ✅ balances, assets, transactions; every spend needs a Confirm |

## What is real, what is demo

- **Real:** PDF signatures (CMS / adbe.pkcs7.detached, checkable with any PDF tool), the 4 signature checks,
  EdDSA-Poseidon signatures on the data cards, the circom circuit and Groth16 proofs (made in the tenant's
  browser, verified in the landlord's browser), RGB transfers on Bitcoin Mutinynet (rgb-lib, on-chain),
  the local AI with QVAC.
- **Demo:** the issuers (Banca Demo, Demo Comune di Torino, Demo Politecnico, Demo Employer) and the trust root
  are ours, the people are fictional, the stablecoin `TUSDT` is our test token, and the ZK trusted setup is a
  single-team ceremony. Real issuers already sign PDFs; the next step is proving facts about their existing
  signatures directly (as PSE's zkPDF does) instead of our data card. One server plays both laptops in the demo,
  but the landlord side only ever receives what arrives in its RGB wallet.

## Run it (Mac)

1. Once: double-click `scripts/setup_mac.command` (makes `.venv` with `cryptography` + `rgb-lib`).
2. Local AI: keep `scripts/start_ai.command` running (reuses the QVAC install from `../scripts/setup_ai.command`).
3. App:
   - `scripts/run_demo.command`: simulated RGB, no bitcoin needed.
   - `scripts/run_real.command`: real RGB on Mutinynet (wallets must be funded first, see below).
4. Open **http://127.0.0.1:8010** (EN/IT/TR). Phones on the same Wi-Fi can open tenant links (the QR uses the Wi-Fi address);
   landlord, wallets and admin only work on the host computer. `/admin.html`: wallets, issuer, developer view, start over, presenter mode.

**Test flow:** "Create a tenant check" → describe the tenant, the local AI fills the form → add the flat (address, type, move-in, rent, deposit) → Publish →
share the link / code / QR → tenant opens it, sees the flat → drags the signed PDFs from `demo_docs/` (the `_EDITED` one is rejected) →
"Create my private proof" → send (RGB approval token) → landlord sees ✓ → tenant pays the deposit (RGB stablecoin) →
both see the completion screen, a printable receipt (`/receipt.html`) and the downloadable ZK proof.

### Real RGB setup (already done on Kuzey's Mac)
- Wallets live in `data/wallets/{issuer,tenant,landlord}` (git-ignored, **never commit them**).
- Fund the issuer wallet from https://faucet.mutinynet.com, then use the wallet page (or `scripts/rgb_setup.command`)
  to share sats, create RGB slots, and issue the stablecoin. Each spend shows its cost first.
- Indexer: `https://esplora.signet.kaleidoswap.com` (KaleidoSwap's Mutinynet server; mutinynet.com rate-limits us).
  RGB proxy: `rpcs://proxy.kaleidoswap.com/json-rpc`.
- Optional: `scripts/rgb_invoice.command` prints an RGB invoice for KaleidoSwap's test-USDT faucet
  (https://faucet.mutinynet.kaleidoswap.com); `keyproof/rgb_setup.py usdt` then uses that USDT for the deposit.

## Developers

```
python3 keyproof/make_demo.py                          # demo trust root, issuers, signed PDFs (writes data/issuer_keys, git-ignored)
circom circuits/keyproof.circom --r1cs --wasm -o build  # circuit (circom 2.2.2)
node tools/setup_zk.cjs                                # Groth16 trusted setup -> web/zk/keyproof_final.zkey
node tools/witness_test.cjs build/cards.json           # circuit accepts real documents, rejects bad ones
node tools/prove_test.cjs                              # full proof + verify
node tools/e2e.cjs out.png                             # browser end-to-end test (app on :8010)
```

| Folder | What |
|---|---|
| `keyproof/` | Python: `pdfsig.py` (sign/verify PDFs), `zkcrypto.py` (Poseidon, Baby Jubjub, EdDSA), `ai.py` (QVAC), `rgb.py` + `rgb_setup.py` (rgb-lib wallets), `app.py` (server) |
| `circuits/` | `keyproof.circom`: the 5 checks + EdDSA-Poseidon signature checks |
| `web/` | `index.html` (landlord + tenant), `wallets.html`, `zk/` (snarkjs, wasm, zkey, verification key) |
| `demo_docs/` | signed demo PDFs + the edited fake |
| `trust/` | demo root and issuer certificates (public) |
| `docs/PITCH.md` | 3-minute demo script and jury Q&A |
| `vendor/asn1crypto` | vendored pure-Python dependency (MIT) |

## Team Moneyfest
Kuzey Can Kacar · Irem Sengor · Ege Arca Akcay · Kerem Alp Yildiz
