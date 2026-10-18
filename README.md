# KeyProof

**Prove you qualify for a flat without handing over your documents.**

Team **Moneyfest** · *Agentic Dollars on Bitcoin* hackathon · BLOX Turin, 17–18 October 2026

**Built with:** RGB on Bitcoin (approval token + stablecoin deposit) · QVAC local AI (landlord form + reading the tenant's documents on-device) · Tether WDK (tenant's self-custodial wallet) · zero-knowledge proofs (circom + Groth16) · digitally signed PDFs.

> **The AI helps, the math decides.** Every ✓ a landlord sees is proven from data a trusted issuer signed. The landlord never sees a document, a name or an amount.

---

## Contents

1. [The problem](#1-the-problem)
2. [What KeyProof does](#2-what-keyproof-does)
3. [How it works, step by step](#3-how-it-works-step-by-step)
4. [Technologies and how we use them](#4-technologies-and-how-we-use-them) – RGB · QVAC · Tether WDK · ZK proof · signatures
5. [Hackathon requirements and judging points](#5-hackathon-requirements-and-judging-points)
6. [Security: what can and can't be faked](#6-security-what-can-and-cant-be-faked)
7. [We tested real documents](#7-we-tested-real-documents)
8. [Proof it works: transactions and tests](#8-proof-it-works-transactions-and-tests)
9. [Try it yourself](#9-try-it-yourself) – quick demo · full setup (AI, real RGB, WDK) · phones · verify a proof
10. [Demo files](#10-demo-files)
11. [What's real today, what's next](#11-whats-real-today-whats-next)
12. [Repository map](#12-repository-map)
13. [Open-source projects we build on](#13-open-source-projects-we-build-on)
14. [Security note](#security-note) · [Team](#team)

---

## 1. The problem

To rent a room, tenants send strangers their **ID card, payslips, bank statements and contracts**, usually by email or WhatsApp. The landlord only needs a few yes/no answers: *adult? earns enough? student or employed until the lease ends? guarantor?*

- **Tenants overshare:** exact salary, balance, spending history, address and ID number end up in strangers' inboxes forever.
- **Landlords still can't trust it:** a PDF can be edited in 30 seconds. We checked 6 real documents from 5 institutions; **none** was digitally signed (see [section 7](#7-we-tested-real-documents)).

## 2. What KeyProof does

| Who | Does | Sees |
|---|---|---|
| **Landlord** | Writes what they need in plain words; the local AI fills the form; adds the flat; publishes a code, link and QR | Only ✓/✗ per requirement, plus the deposit |
| **Tenant** | Opens the link (laptop or phone), drops signed PDFs; the local AI reads them **on their device**; creates a zero-knowledge proof; sends it as an RGB token; pays the deposit | Everything about their own documents, nothing leaves the device |
| **Issuer** (bank, comune, university, employer) | Signs documents and a small data card inside them | – |
| **Anyone** (notary, bank, jury) | Drops the downloaded proof file into the standalone verifier | ✓ Valid / ✗ NOT valid and what was proven |

**Requirements a landlord can set:** adult (18+) · sex (for rooms in a shared flat only) · monthly income ≥ X · student and/or employed until the lease ends · savings ≥ X · guarantor's income ≥ X. Documents with money must be less than 90 days old, and all documents must belong to the same person.

## 3. How it works, step by step

```
 Issuer (bank, comune, university)   signs the PDF + a data card inside it (EdDSA-Poseidon, ZK-friendly)
        │
 Landlord's laptop                   1. writes requirements → QVAC local AI fills the form → landlord checks → publish
        │                               (code + link + QR for the listing)
        ▼
 Tenant's laptop / phone             2. drops PDFs → signature check (not changed, trusted issuer, valid, right issuer)
                                     3. QVAC reads each document ON THE DEVICE: sorts it, reads values, private advice
                                     4. browser builds a zero-knowledge proof: "every rule is met, using data
                                        signed by these issuers" – no name, no amounts, no documents
                                     5. proof attached to an RGB approval token → sent on Bitcoin to the landlord
        │
 Landlord's laptop                   6. RGB wallet receives + validates the token
                                     7. browser verifies the proof against ITS OWN rules and ITS OWN trust list
                                     8. ✓ / ✗ per requirement → assistant asks for the deposit
        │
 Tenant                              9. confirms → deposit in a stablecoin on RGB (tenant wallet on Tether WDK)
 Both                               10. completion screen, printable receipt, downloadable proof anyone can re-check
```

### Who decides what

| Part | Job | Decides? |
|---|---|---|
| Issuer's digital signature | The data is real and unchanged | ✓ |
| Trust list | Which issuers count, and for which facts | ✓ |
| Zero-knowledge proof | The data meets the landlord's rules, without revealing it | ✓ |
| RGB on Bitcoin | Who owns the approval, timestamp, carries the deposit | ✓ |
| Local AI (QVAC) | Fills the landlord's form; reads, sorts and explains the tenant's documents | **Never** |
| People | The landlord publishes the rules; the tenant confirms sending and paying | ✓ |

## 4. Technologies and how we use them

### RGB on Bitcoin (required)
- **Approval token:** an RGB **UDA** (unique digital asset) issued by the tenant's wallet; its media is the ZK proof, so the RGB contract commits to the proof's hash. Sent **on-chain** to the landlord.
- **Why RGB:** the approval has one owner, can't be duplicated or quietly sent to many landlords, has a Bitcoin timestamp, and is validated client-side by the receiver. Nothing private is published on the chain.
- **Deposit:** an RGB **NIA** stablecoin (`TUSDT`, our test token) from tenant to landlord after approval, the "agentic dollars" part: the landlord's assistant requests it, the tenant confirms.
- **Future idea, prototyped on-chain:** issuers send signed data cards straight into the tenant's RGB wallet, so no PDF is needed. Removed from the app to keep the demo focused; design note in [keyproof/docs/FUTURE_issuer_credentials.md](keyproof/docs/FUTURE_issuer_credentials.md).
- **Stack:** `rgb-lib` 0.3.0b7 (Python), **Mutinynet** (Bitcoin signet, ~30 s blocks), KaleidoSwap's Mutinynet indexer `esplora.signet.kaleidoswap.com` and RGB proxy `proxy.kaleidoswap.com`. No Docker.

### QVAC local AI (required)
Runs **Qwen3.5 4B** (Q4_K_M) locally through `@qvac/cli` (OpenAI-compatible API on `127.0.0.1:11436`), offline. Qwen3 1.7B is the backup and keyword rules are the last fallback, so the demo never breaks.
- **Landlord:** turns "adult female student, earns 1,500" (English, Italian, Turkish) into the requirement form. Benchmark (`keyproof/tools/bench_ai.py`): **4B 10/10 correct, ~3.3 s**; 1.7B 8/10, ~1.2 s.
- **Tenant, where local matters most:** reads each uploaded PDF **on the tenant's device** (`keyproof/keyproof/pdftext.py` + `ai.read_document`): document type, issuer, name, amount, dates, sex, reference. It routes the document and gives private advice ("€1,650 meets €1,500 ✓", "issued 6 days ago ✓", "name differs from your ID", "not related to this request"). Tested on 6 sample documents and **real** Agenzia delle Entrate, UniCredit, Politecnico and e-Devlet PDFs: all read correctly in ~4–7.5 s each.
- **Why it must be local:** it reads the most private data in the whole flow. A cloud AI means uploading ID and bank statements.
- **What it never does:** decide. Its output is advice only; approval comes from signatures and the ZK proof.

### Tether WDK
- The tenant gets a **self-custodial wallet built on WDK's RGB module** [`@utexo/wdk-wallet-rgb`](https://www.npmjs.com/package/@utexo/wdk-wallet-rgb) 2.0.3 (a community module listed in the WDK docs). Keys stay on the device (`keyproof/data/wdk/`, never committed).
- `keyproof/wdk/server.mjs` is a small local service (127.0.0.1:8011) that the app calls. The tenant screens show the wallet's address, live balance from the Bitcoin test network, and a QR to fund it.
- `keyproof/scripts/wdk_check.command` installs WDK and checks it on our network: it connected on **signet** with our KaleidoSwap indexer.
- **Next step:** move the RGB deposit itself into the WDK wallet. WDK supports standard signet, while our rgb-lib wallets use Mutinynet as a *custom* signet, so the two must be aligned first.

### Zero-knowledge proof
- **Circuit** `keyproof/circuits/keyproof.circom` (~45,500 constraints, circom 2.2.2). For each ticked requirement it verifies the issuer's **EdDSA-Poseidon** signature on the data card, the document type, that all documents belong to the same person, and the rule itself: age, **sex** (from the signed identity card / codice fiscale), income, student or employed until the lease ends, savings, guarantor, and freshness of money documents.
- **Groth16** with snarkjs: the proof is made **in the tenant's browser** (~10 s, 0.7 KB) and checked **in the landlord's browser** (milliseconds).
- **27 public values:** the landlord's own rules, the request number and the issuer keys used. The landlord rejects proofs made with easier rules, another request, or an untrusted issuer.
- **Unlinkable:** the output tag is the same for the same tenant on the same request, and different across landlords.
- **Verifiable by anyone:** the completion screen offers **Download proof** (proof, public values, rules, verification key, Bitcoin transaction links). The **standalone verifier** (`/verify.html`, or `keyproof/docs/keyproof-verifier.html` opened anywhere) checks it against KeyProof's **built-in** official key and trust list, so a file can't vouch for itself. One edited number in the file → "NOT valid".
- Trusted setup: powers of tau 2^16 plus a circuit-specific phase, run by our team (`keyproof/tools/setup_zk.cjs`). Production needs a multi-party ceremony.

### Digitally signed PDFs
- CMS signatures (`adbe.pkcs7.detached`) over every byte, readable by any PDF tool: poppler's `pdfsig` and Adobe Acrobat report "Signature is Valid".
- `keyproof/keyproof/pdfsig.py` runs **4 checks**: **not changed** · **trusted issuer** (certificate from the trusted root) · **still valid** (dates, not revoked) · **right issuer** (a university can't vouch for income). It handles ECDSA and **RSA** (SHA-256/384/512), the signature types real issuers use.
- **Three levels shown to the tenant:**
  - green: a trusted issuer, used for the proof;
  - amber: a valid signature from a key that is **not** on the trust list ("a key that *calls itself* X"); never used for the proof;
  - grey: unsigned; the AI reads it, but it never counts.

## 5. Hackathon requirements and judging points

| Point | Where in KeyProof |
|---|---|
| **RGB (required)** | Approval token (UDA carrying the ZK proof) and stablecoin deposit (NIA), both **settled on Bitcoin Mutinynet**; wallet page with balances and transactions ([section 8](#8-proof-it-works-transactions-and-tests)) |
| **QVAC (required)** | Local Qwen3.5 4B on both sides: the landlord form from free text (EN/IT/TR), and reading the tenant's private documents **on the device**; benchmarked; with fallbacks |
| **Tether WDK (bonus)** | The tenant's self-custodial wallet built on `@utexo/wdk-wallet-rgb`, live on the test network inside the app |
| **Agentic dollars** | The landlord's assistant requests the deposit after a valid proof; the tenant confirms; a stablecoin moves on RGB. No human handles documents, the AI never decides money or approval |
| **Privacy** | Documents never leave the tenant's device; the landlord learns only ✓/✗; the ZK proof hides all values; nothing private on-chain; the proof tag is unlinkable across landlords |
| **Security** | Issuer signatures + trust list + "right issuer" + ZK checked on the landlord's own machine; edited, self-signed and forged-name documents all fail ([section 6](#6-security-what-can-and-cant-be-faked)) |
| **Real-world fit** | Real Italian and Turkish documents tested; listing, QR for Idealista, receipts, EN/IT/TR, phones on the same Wi-Fi |
| **Completeness** | Full flow works end to end, real transactions, downloadable proof, standalone verifier, admin page, restart script |
| **Honesty** | A clear "real today / next" list ([section 11](#11-whats-real-today-whats-next)); demo issuers labelled "(test)" |

## 6. Security: what can and can't be faked

| Attempt | Result |
|---|---|
| Edit a number in a signed PDF | ❌ signature breaks ("modified after it was signed"); the proof can't be built from it |
| Sign a document yourself, even with true data | ❌ your key isn't on the landlord's trust list |
| Sign with a key named "Moneyfest Bank (test)" | ❌ shown as "a key that *calls itself*…"; not trusted |
| A university signing an income statement | ❌ "right issuer" check |
| Use someone else's documents | ❌ all documents must be the same person; the proof is tied to one request |
| Prove against easier rules (e.g. €100 instead of €1,500) | ❌ the landlord verifies with their own rules; the standalone verifier says NOT valid |
| Skip the identity card to dodge a sex requirement | ❌ the circuit forces the signed identity card on when sex is required |
| Hack the local AI or the tenant's app | ❌ only fools their own screen; the landlord verifies independently |
| A dishonest or hacked **trusted issuer** | ⚠️ the math faithfully proves what the issuer signed; the fix is revoking that issuer on the trust list |

## 7. We tested real documents

Not one of these real documents carried a digital signature inside the PDF. Each uses a different method instead:

| Document | Issuer | Signed? | How it's verified instead | Local AI read it |
|---|---|---|---|---|
| Bank account statement | UniCredit | No | – | ✓ savings, €482 |
| Lease-registration receipt (RLI12) | Agenzia delle Entrate | No | protocol number | ✓ rental, €13,200/yr |
| Enrolment certificate | Politecnico di Torino | No ("firma omessa", D.Lgs. 39/1993) | verify link on polito.it | ✓ |
| Self-declaration | Politecnico di Torino | No | – | ✓ |
| Address document | Turkish e-Devlet (NVİ) | No | barcode on turkiye.gov.tr | ✓ |
| Gas bill | utility (Doxee platform) | No | – (the signed version is the XML e-invoice) | ✓ |

The real documents stay on our machine; they are **not** in this repo.

**Conclusion:** today a landlord can't check any of these at scale. KeyProof only approves what's mathematically provable. Next: **zkTLS** to prove facts straight from issuer websites (home banking, e-Devlet, university portals), still privately.

## 8. Proof it works: transactions and tests

### Real Bitcoin transactions (Mutinynet test network)

| Step | Transaction |
|---|---|
| Test bitcoin from the faucet to our issuer wallet | [3243ddff…](https://mutinynet.com/tx/3243ddffd988652ca382ccd073bc33349468d0b382926b305f962b56825c7cf0) |
| Bitcoin shared with the landlord wallet | [87f3ce7a…](https://mutinynet.com/tx/87f3ce7af2fc8dde3d9b446ec3f8811f7f3de9d6e98c1d72a0bf42dd4fedb6ff) |
| 2,000 TUSDT (RGB stablecoin) to the tenant | [a255bf90…](https://mutinynet.com/tx/a255bf90c14c688ae80d1fa37e9e6bdd35109d49a3a3188629036778a22514a5) |
| 3 credentials as RGB tokens, issuers → tenant, one transaction (prototype of the future idea, see `keyproof/docs/FUTURE_issuer_credentials.md`) | [fa94519c…](https://mutinynet.com/tx/fa94519c3b22f806f26c751851ccf4eb1b093a5817d26ba79bfb50f29e1616a5) |
| **Approval token (RGB UDA with the ZK proof), tenant → landlord** | [01bc272e…](https://mutinynet.com/tx/01bc272eb2a29629ac95907cca4377dcdf17f83af8d793ecd02324b69daa6655) |
| **Deposit 1,100 TUSDT, tenant → landlord** | [899d3dc8…](https://mutinynet.com/tx/899d3dc81d352a13112b651381921eeb1b1f4fb7f9d3210bcf1811b8b66e83ba) |

Stablecoin asset: `rgb:j7daBWV1-qd2YN6B-QD_84b5-4qqRuGj-lUCwT8y-ictiTwY` (TUSDT). Later runs during the demo add more approval and deposit transactions; each one is linked from the app's receipt.

### Tests we ran

| Test | Result |
|---|---|
| 6 signed documents (identity + codice fiscale, income, enrolment, employment, balance, guarantor) | ✅ all 4 checks pass; `pdfsig`: "Signature is Valid" |
| The 6 `_EDITED` copies (one value changed each) | ❌ rejected |
| Documents signed by a stranger's key / a fake "bank" key | ⚠️ valid signature, not trusted, never used for the proof |
| Circuit: income below the minimum, enrolment ends before the lease, wrong status, wrong sex | ❌ no proof possible |
| "Women only" with Elena (F) / "Men only" | ✅ proof / ❌ no proof |
| Downloaded proof in the standalone verifier / same file with the minimum edited | ✅ valid / ❌ NOT valid |
| Local AI (QVAC, Qwen3.5 4B) on 6 sample + 4 real documents | ✅ all classified correctly, ~4–7.5 s each |
| Full browser flow: landlord → tenant → proof → RGB → deposit → receipt (desktop + phone width) | ✅ (`keyproof/tools/e2e_real.cjs`) |
| Full flow on Bitcoin Mutinynet with real RGB | ✅ approval token and deposit settled |

## 9. Try it yourself

Requirements: a **Mac with Apple Silicon** and Python 3.10+. Everything installs **into the project folder**: no admin rights, no Docker. On a Mac, run the `.command` files by double-clicking them in Finder (first time: right-click → Open if macOS asks).

### A. Quick demo (5 minutes, no Bitcoin, no AI download)
1. `git clone https://github.com/kuzeykacar/Moneyfest.git`, or **Code → Download ZIP**.
2. Double-click `keyproof/scripts/setup_mac.command` (once: creates `.venv` with `cryptography` + `rgb-lib`).
3. Double-click `keyproof/scripts/run_demo.command` and keep the window open.
4. Open **http://127.0.0.1:8010** → **Create a tenant check** → publish → open the tenant link → drag PDFs from `keyproof/demo_docs/`.

Without the AI running, documents are read with simple rules instead, and the screen says so. RGB is simulated.

### B. Full setup, as we run it (local AI + real RGB + WDK)
1. **Local AI (QVAC):**
   - Double-click `scripts/setup_ai.command` once. It installs Node.js and QVAC into `.node/` and `.qvac/`.
   - Then double-click `keyproof/scripts/start_ai_4b.command` and keep it open. The first run downloads Qwen3.5 4B (~2.7 GB, checked by SHA-256).
   - Optional: `keyproof/scripts/test_ai_docs.command` makes the AI read every sample document and writes `keyproof/data/ai-docs.txt`.
2. **Tether WDK:** double-click `keyproof/scripts/wdk_check.command` once. It installs WDK and creates the tenant's WDK wallet (seed in `keyproof/data/wdk/`, never committed).
3. **Real RGB wallets on Mutinynet:**
   - Run `keyproof/scripts/run_real.command` once. It creates the issuer, tenant and landlord wallets in `keyproof/data/wallets/` (never committed).
   - Open **http://127.0.0.1:8010/wallets.html**, copy the **issuer** address, and get test coins at https://faucet.mutinynet.com.
   - On the wallet page (every spend shows its cost and needs **Confirm**), or with `keyproof/scripts/rgb_setup.command`:
     1. share sats with the tenant and landlord;
     2. create RGB slots;
     3. issue the TUSDT stablecoin;
     4. send TUSDT to the tenant.
4. **Run:** `keyproof/scripts/run_real.command` starts KeyProof with real RGB, the local AI (if running) and the WDK wallet service. If anything ever hangs, `keyproof/scripts/restart_app.command` stops and restarts it.

### C. Phones
- The QR and link use the Mac's **Wi-Fi** address. Phones on the same Wi-Fi open the **tenant** side; landlord, wallets and admin only work on the Mac.
- Guest Wi-Fi networks often block devices from reaching each other. In that case, turn on a phone's **Personal Hotspot**, connect the Mac to it, and run `restart_app.command`.

### D. Verify a proof anywhere
1. On the completion screen, click **Download proof**.
2. Open **`/verify.html`** (or the single file `keyproof/docs/keyproof-verifier.html` on any computer) and drop the JSON.
3. Developers can also check it with the open-source CLI: `snarkjs groth16 verify verification_key.json public.json proof.json`.

### Useful pages
| Page | What |
|---|---|
| `/` | Home: landlords create a tenant check, tenants enter a code |
| `/landlord.html` | Landlord: requirements (with the local AI), the flat, publish, share, result, deposit |
| `/a/CODE` | Tenant link for an application |
| `/receipt.html` | Printable receipt |
| `/verify.html` | Standalone proof verifier |
| `/admin.html` (host only) | Wallets, developer view, start over, presenter mode |
| `/wallets.html` (host only) | RGB wallets: balances, assets, transactions, actions with confirmation |
| `/dev.html` (host only) | Developer view: both sides on one page |

### Developers
```
python3 keyproof/keyproof/make_demo.py            # trust root, issuers, signed demo PDFs (+ _EDITED copies)
python3 keyproof/keyproof/make_team_doc.py        # Team Moneyfest signed certificate (RSA, self-issued)
python3 keyproof/keyproof/make_untrusted_docs.py  # same income statement signed by untrusted keys
keyproof/tools/circom-linux keyproof/circuits/keyproof.circom --r1cs --wasm -o keyproof/build
node keyproof/tools/setup_zk.cjs                  # Groth16 setup -> web/zk/keyproof_final.zkey + verification_key.json
python3 keyproof/tools/build_verifier.py          # standalone verifier page
node keyproof/tools/e2e_real.cjs <screenshot-dir> # browser end-to-end test (app on :8010)
```
More technical detail: [keyproof/README.md](keyproof/README.md). The 3-minute pitch and jury Q&A: [keyproof/docs/PITCH.md](keyproof/docs/PITCH.md).

## 10. Demo files

All demo people are fictional (Elena Rossi, Marco Rossi); all demo issuers are ours and labelled "(test)".

| File (in `keyproof/`) | Signed by | KeyProof shows |
|---|---|---|
| `demo_docs/1_Identity_codice_fiscale_Elena_Rossi.pdf` | Moneyfest Anagrafe (test) | ✓ trusted, identity (age, sex F) |
| `demo_docs/2_Income_statement_Elena_Rossi.pdf` | Moneyfest Bank (test) | ✓ trusted, income €1,650 with 6 salary credits |
| `demo_docs/3_Enrolment_certificate_Elena_Rossi.pdf` | Moneyfest University (test) | ✓ trusted, student until 30/09/2027 |
| `demo_docs/3b_Employment_certificate_Elena_Rossi.pdf` | Moneyfest Employer (test) | ✓ trusted, employed until 30/06/2028 |
| `demo_docs/4_Balance_certificate_Elena_Rossi.pdf` | Moneyfest Bank (test) | ✓ trusted, savings €4,800 |
| `demo_docs/5_Guarantor_income_Marco_Rossi.pdf` | Moneyfest Bank (test) | ✓ trusted, guarantor €3,900 |
| `demo_docs/*_EDITED.pdf` (6 files) | changed after signing | ✗ rejected |
| `real_docs/Team_Moneyfest_membership.pdf` | Team Moneyfest (RSA, self-issued) | ⚠️ valid signature, not trusted |
| `real_docs/Team_Moneyfest_membership_EDITED.pdf` | changed after signing | ✗ rejected |
| `real_docs/2_Income_statement_SIGNED_BY_STRANGER.pdf` | a private person's key | ⚠️ valid signature, not trusted |
| `real_docs/2_Income_statement_FAKE_BANK_KEY.pdf` | a key that *calls itself* Moneyfest Bank | ⚠️ valid signature, not trusted |

## 11. What's real today, what's next

| Real today | Next |
|---|---|
| Signature checks (ECDSA + RSA); edited files rejected | Real issuers signing data cards (banks, comuni, universities) |
| ZK circuit: age, sex, income, occupation, savings, guarantor, freshness, same person | zkPDF / **zkTLS**: prove from existing signatures or issuer websites |
| Proof made and verified in the browser; downloadable; standalone verifier | EU Trusted Lists (eIDAS) via the EU DSS validator as the trust list |
| RGB approval token + stablecoin deposit on Bitcoin (Mutinynet) | Mainnet + a real RGB stablecoin (e.g. USDT on RGB) |
| QVAC local AI on both sides | Deposit fully through the WDK wallet |
| Tether WDK self-custodial tenant wallet | Multi-party trusted setup, revocation (OCSP/CRL), hosted HTTPS |
| Phone QR, receipts, EN/IT/TR, admin page | Accounts, multiple listings and applicants, persistence |
| | Issuers send credentials straight to the tenant's wallet as RGB tokens (prototyped, see `keyproof/docs/FUTURE_issuer_credentials.md`) |

## 12. Repository map

| Path | What |
|---|---|
| `keyproof/keyproof/app.py` | Server: landlord, tenant, issuer, wallets, proof bundle, phone access rules |
| `keyproof/keyproof/pdfsig.py` | Sign and verify PDFs (CMS, ECDSA/RSA), the 4 checks, data cards |
| `keyproof/keyproof/zkcrypto.py` | Poseidon, Baby Jubjub, EdDSA (matches circomlib) |
| `keyproof/keyproof/ai.py`, `pdftext.py` | QVAC calls: landlord rules, reading documents, assistant texts; PDF text extraction |
| `keyproof/keyproof/rgb.py`, `rgb_setup.py` | RGB wallets with rgb-lib (real) and a simulated version |
| `keyproof/keyproof/make_*.py` | Demo issuers and signed documents |
| `keyproof/circuits/keyproof.circom` | The ZK circuit |
| `keyproof/web/` | Pages (`index`, `landlord`, `tenant`, `receipt`, `verify`, `admin`, `wallets`, `dev`), design (`simple.css`/`simple.js`), `zk/` (snarkjs, circuit wasm, proving key, verification key, trusted issuers) |
| `keyproof/wdk/` | Tether WDK tenant wallet: check script and local service |
| `keyproof/demo_docs/`, `keyproof/real_docs/` | Signed demo documents, edited copies, untrusted-signer copies |
| `keyproof/trust/` | Trust root and issuer certificates (public) |
| `keyproof/tools/` | ZK setup, verifier builder, AI benchmark and document test, browser end-to-end tests |
| `keyproof/scripts/` | Double-click scripts: setup, run (demo/real), restart, AI, WDK, wallets |
| `keyproof/docs/` | Pitch and jury Q&A, standalone verifier, future-idea notes |
| `scripts/` | QVAC install (`setup_ai.command`), shared by both projects |
| `backend/`, `web/` | *Moneyfest Aid*, an earlier prototype from the same hackathon |

## 13. Open-source projects we build on

| Project | Used for |
|---|---|
| [RGB / rgb-lib](https://github.com/RGB-Tools/rgb-lib) (Python bindings 0.3.0b7) | RGB wallets: issuing, sending, receiving UDA and NIA assets |
| [KaleidoSwap](https://kaleidoswap.com) Mutinynet indexer + RGB proxy | Bitcoin indexer and RGB consignment transport |
| [Mutinynet](https://mutinynet.com) + faucet | Bitcoin signet test network (~30 s blocks) |
| [QVAC](https://www.npmjs.com/package/@qvac/cli) (`@qvac/cli`, `@qvac/sdk`) | Local AI server |
| [Qwen3.5 4B GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF), Qwen3 1.7B | Local language models |
| [Tether WDK](https://docs.wallet.tether.io) RGB module [`@utexo/wdk-wallet-rgb`](https://www.npmjs.com/package/@utexo/wdk-wallet-rgb) | Tenant's self-custodial wallet |
| [circom](https://github.com/iden3/circom) 2.2.2 + [circomlib](https://github.com/iden3/circomlib) | ZK circuit, Poseidon, EdDSA, comparators |
| [snarkjs](https://github.com/iden3/snarkjs) | Groth16 setup, proving and verifying |
| [pyca/cryptography](https://github.com/pyca/cryptography), [asn1crypto](https://github.com/wbond/asn1crypto) (vendored) | PDF signatures, certificates |
| [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) (vendored) | QR codes |
| [Playwright](https://playwright.dev) | Browser end-to-end tests |

## Security note

Only Mutinynet, a Bitcoin test network, with test coins that have no value. Wallet keys, recovery words, the WDK seed, the demo issuers' private keys and the AI models stay on our machine and are excluded by `.gitignore` (every `data/` folder is ignored). Real personal documents we tested are not in this repo. In the design, documents never leave the tenant's device; the landlord receives only the proof.

## Third-party code

See [keyproof/THIRD_PARTY_NOTICES.md](keyproof/THIRD_PARTY_NOTICES.md) for every open-source project, file and license we use.

## Team

| Name | GitHub |
| ---- | ------ |
| Kuzey Can Kacar | [@kuzeykacar](https://github.com/kuzeykacar) |
| Irem Sengor | [@iurisiur](https://github.com/iurisiur) |
| Ege Arca Akcay | [@arcakcy](https://github.com/arcakcy) |
| Kerem Alp Yildiz | [@keremalpyildiz](https://github.com/keremalpyildiz) |
