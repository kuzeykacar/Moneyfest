# 🔑 KeyProof

**Prove you qualify for a flat without showing your documents.**

Team **Moneyfest** · *Agentic Dollars on Bitcoin* hackathon · BLOX Turin, 17–18 October 2026
Built with **RGB** (required), **QVAC** (required), zero-knowledge proofs (circom + Groth16).

> ✅ **Tested end to end on Bitcoin (Mutinynet) on Sunday 18 Oct at 00:46–00:49:** a real RGB approval token
> and a real RGB stablecoin deposit, both settled on-chain. Links in [Proof it works](#proof-it-works).

---

## The problem

To rent a room, a tenant sends a stranger their **full bank statements, ID card, payslips and contracts**,
often by email or WhatsApp. The landlord only needs a few answers: *Is this person an adult? Do they earn
enough? Are they a student or employed? Is there a guarantor?*

Everything else in those documents (exact salary, account balance, spending history, address, ID number) is
exposed for nothing, and the files stay in someone's inbox forever. Meanwhile, edited PDFs are easy to make,
so landlords can't fully trust what they receive either.

**Both sides lose:** tenants give away too much, landlords still can't be sure.

## The solution

KeyProof lets the tenant **prove the answers** instead of sending the documents:

1. **The issuer signs.** The bank, the city office (comune) or the university issues a **digitally signed PDF**.
   Inside it is a small **data card** (e.g. `income = 1650`), also signed by the issuer.
2. **The landlord asks.** They type what they need ("adult student, earns at least €1,500 a month"). A **local AI
   (QVAC)** turns the sentence into checkboxes. The landlord checks them and publishes the request.
3. **The tenant proves.** On the tenant's own laptop, KeyProof checks every PDF signature, then creates a
   **zero-knowledge proof**: *"documents signed by trusted issuers say this person passes every ticked check."*
   The proof contains **no name, no amounts, no documents**.
4. **RGB carries the approval.** The proof is attached to a unique **RGB token on Bitcoin** and sent on-chain to
   the landlord's wallet. Only a hash of the proof is committed on-chain; nothing private goes on the blockchain.
5. **The landlord verifies.** The landlord's wallet validates the RGB token; the landlord's page checks the proof
   against **its own rules** and **its own list of trusted issuers**. Result: ✓ / ✗ per check, nothing more.
6. **Agentic dollars.** After a valid approval, the landlord's agent requests the deposit; the tenant's agent
   prepares it; the tenant presses **Confirm**; the deposit moves as an **RGB stablecoin** on Bitcoin.

### Who decides what

| Part | Job | Decides? |
|---|---|---|
| Issuer's digital signature | the data is real and unchanged | yes |
| Zero-knowledge proof | the data passes the landlord's rules, without revealing it | yes |
| RGB token on Bitcoin | who owns the approval; single use; timestamp; carries the deposit | yes |
| Local AI (QVAC, Qwen3.5 4B) | understands the landlord's text, fills the form | **never** |
| Humans | landlord publishes the rules; tenant confirms sending and paying | yes |

Rule we kept from the start: **the AI understands, code and math decide, humans confirm.**

## The 5 checks a landlord can tick

| Check | Signed source (real world) | What the landlord learns |
|---|---|---|
| **Identity, 18+** | ID office / municipality | adult ✓; all documents belong to the same person |
| **Monthly income ≥ X** | bank statement / payslip | income ≥ X ✓ (never the amount) |
| **Occupation** | university or employer | student / employed ✓, lasting until the lease ends |
| **Savings ≥ X** | bank balance certificate | savings ≥ X ✓ |
| **Guarantor's income ≥ X** | guarantor's bank | guarantor ✓ |

**Only digitally signed documents are accepted.** No valid signature, no approval. We don't guess whether a PDF
"looks real" (no Photoshop/metadata checks). We left criminal records out on purpose: in the EU that data is
specially protected (GDPR Art. 10) and landlords generally may not ask for it.

## How each technology is used

### RGB (required)
- **Approval token:** an RGB **UDA** (unique digital asset) issued by the tenant's wallet. Its media file is the
  proof, so the RGB contract commits to the proof's hash. Sent **on-chain** (not Lightning) to the landlord.
- **Why RGB:** the approval is *owned* by one wallet, can't be duplicated or quietly sent to many landlords, has a
  Bitcoin timestamp, and is validated client-side by the receiver. Nothing private is published.
- **Deposit:** an RGB **NIA** stablecoin (`TUSDT`, our test token) moved tenant → landlord after approval.
- **Stack:** `rgb-lib` 0.3.0b7 Python bindings, Bitcoin **Mutinynet** (signet, ~30 s blocks), KaleidoSwap's
  Mutinynet indexer (`esplora.signet.kaleidoswap.com`) and RGB proxy (`proxy.kaleidoswap.com`). No Docker.

### QVAC (required)
- **Qwen3.5 4B (Q4_K_M)** served locally by `@qvac/cli` (OpenAI-compatible API on `127.0.0.1:11436`), offline;
  Qwen3 1.7B as a backup. Thinking mode off (`reasoning_budget: 0`) so it answers directly.
- Turns the landlord's free text (English, Italian, Turkish) into the 5 checkboxes and numbers.
- Benchmark on 10 landlord sentences (`keyproof/tools/bench_ai.py`): **Qwen3.5 4B 10/10 correct, ~3.3 s**;
  Qwen3 1.7B 8/10, ~1.2 s.
- Code validates the output (booleans, whole euros, real dates) and the landlord confirms the boxes.
  If QVAC is off, keyword rules take over so the demo never breaks.

### Zero-knowledge proof
- **Circuit** (`keyproof/circuits/keyproof.circom`, ~45,000 constraints): for each ticked check it verifies the
  issuer's **EdDSA-Poseidon** signature on the data card, that the document is the right kind, that all documents
  belong to the same person, and the rule itself (age, income, status and end date, savings, guarantor, and that
  money documents are less than 90 days old).
- **Groth16** with snarkjs: the proof is made **in the tenant's browser** (~8 s, 0.7 KB) and checked **in the
  landlord's browser** (milliseconds).
- **Public inputs** are the landlord's own rules, request number and the issuer keys used; the landlord rejects
  any proof made with easier rules, another request, or an issuer it doesn't trust.
- **Output:** a tag that is the same for the same tenant on the same request, and different across landlords,
  so landlords can't link a tenant between them.

### Digital signatures on the PDFs
- Each demo PDF carries a CMS signature (`adbe.pkcs7.detached`, ECDSA P-256) covering every byte. Any PDF tool can
  check it: poppler's `pdfsig` reports **"Signature is Valid"** on our documents.
- KeyProof's 4 checks: **not changed**, **trusted issuer** (certificate issued by the trusted root), **still valid**
  (dates, not revoked), **right issuer** (a university can't vouch for income).
- Each issuer certificate also carries the issuer's ZK key, so the landlord only needs to trust one root.

## Proof it works

### Real Bitcoin transactions (Mutinynet test network)

| Step | Transaction |
|---|---|
| Test bitcoin from the faucet to our issuer wallet (100,000 sats) | [3243ddff…](https://mutinynet.com/tx/3243ddffd988652ca382ccd073bc33349468d0b382926b305f962b56825c7cf0) |
| Bitcoin shared with the landlord wallet | [87f3ce7a…](https://mutinynet.com/tx/87f3ce7af2fc8dde3d9b446ec3f8811f7f3de9d6e98c1d72a0bf42dd4fedb6ff) |
| 2,000 TUSDT (RGB stablecoin) to the tenant | [a255bf90…](https://mutinynet.com/tx/a255bf90c14c688ae80d1fa37e9e6bdd35109d49a3a3188629036778a22514a5) |
| **3 credentials (identity, income, enrolment) as RGB tokens, issuers → tenant, one transaction** | [fa94519c…](https://mutinynet.com/tx/fa94519c3b22f806f26c751851ccf4eb1b093a5817d26ba79bfb50f29e1616a5) |
| **Approval token (RGB UDA with the ZK proof) tenant → landlord** | [01bc272e…](https://mutinynet.com/tx/01bc272eb2a29629ac95907cca4377dcdf17f83af8d793ecd02324b69daa6655) |
| **Deposit, 1,100 TUSDT, tenant → landlord** | [899d3dc8…](https://mutinynet.com/tx/899d3dc81d352a13112b651381921eeb1b1f4fb7f9d3210bcf1811b8b66e83ba) |

RGB assets: approval token `rgb:3X~uMZFM-gJZqkCl-asrjSVA-NKuExMW-6hPwmzp-IxFez9Q`,
stablecoin `rgb:j7daBWV1-qd2YN6B-QD_84b5-4qqRuGj-lUCwT8y-ictiTwY` (TUSDT).
After the test: tenant 900 TUSDT, landlord 1,100 TUSDT. Total network fees so far: about 3,000 test sats.

### Tests we ran

| Test | Result |
|---|---|
| Edited PDF (one number changed, €1,650 → €2,650) | ❌ rejected: "modified after it was signed" |
| PDF from a "bank" certified by an untrusted authority | ❌ rejected: not a trusted issuer |
| University trying to sign an income statement | ❌ rejected: wrong issuer for this document |
| Content appended after signing | ❌ rejected |
| Real signed documents | ✅ all 4 checks pass |
| Circuit: income below the minimum / enrolment ending before the lease / wrong status | ❌ no proof possible |
| Circuit: card value edited after the issuer signed it | ❌ no proof possible |
| Landlord changes the minimum to an easier number in a valid proof | ❌ verification fails |
| Full flow in the browser, simulated RGB | ✅ |
| **Full flow on Bitcoin Mutinynet with real RGB** | ✅ approval token and deposit settled |

## Status

| Part | Status |
|---|---|
| Signed demo documents (5 + 1 fake) | ✅ |
| Signature checks | ✅ |
| ZK circuit, trusted setup, browser proving and verifying | ✅ |
| Local AI (QVAC, Qwen3.5 4B) filling the landlord form | ✅ 10/10 on our benchmark (keyword backup) |
| Simple screens for tenant and landlord (one step at a time, big buttons, plain words, EN/IT/TR) | ✅ |
| **Credentials as RGB tokens** ("future" mode): issuers send signed data cards straight to the tenant's RGB wallet in one transaction; the tenant checks them (issuer seal, trusted issuer, valid, right issuer) and uses them instead of PDFs | ✅ (`/issuer.html`) |
| Local AI assistant texts: explains requests, rejections, results and the deposit in the user's language | ✅ |
| Wallet page: balances, assets, transactions, every spend needs Confirm | ✅ |
| Completion screen with receipt; **downloadable ZK proof** (proof + public values + verification key + tx links) that any third party can verify with `snarkjs groth16 verify`, plus a re-check button | ✅ |
| Landlord ↔ tenant connection: application code + link + QR to share (e.g. on Idealista), private landlord dashboard link; the proof is bound to that request | ✅ |
| Real RGB approval token + deposit on Mutinynet | ✅ |
| Product screens: landing page, landlord adds the flat (address, type, move-in, rent, deposit), tenant sees a listing card first | ✅ |
| Tenant drags all signed PDFs into one box; they are checked and sorted automatically (by the issuer-signed type in the data card) | ✅ |
| Official-style signed PDFs (letterhead, protocol number, visible signature panel, still marked TEST ISSUER) | ✅ |
| Phones on the same Wi-Fi open the tenant link / QR; landlord, wallets and admin stay on the host computer (`/admin.html`) | ✅ |
| Printable receipt (`/receipt.html`): flat, requirements met, deposit, Bitcoin tx links, approval token, proof fingerprint | ✅ |
| **Local AI on the tenant side (QVAC):** reads each uploaded PDF on the tenant's own device – what it is, issuer, name, amount, dates – and gives a private pre-check with advice (amount vs the landlord's minimum, age, document age, name matches the ID, enrolment lasts until the lease ends, AI label vs issuer-signed label). Advice only: the landlord relies on the signatures and the ZK proof. Test: `keyproof/scripts/test_ai_docs.command` | ✅ |
| **Real official PDFs:** signature check now handles real issuers' RSA / SHA-2 signatures. Real documents from issuers not on the trust list (or unsigned, like Agenzia delle Entrate Entratel receipts) are accepted as "real documents": integrity shown, read by the local AI on the device, never used for the proof. Tested on a real Agenzia delle Entrate lease-registration receipt and a real UniCredit account statement (both read correctly in ~7.5 s). None of 5 real documents from 4 institutions (UniCredit, Agenzia delle Entrate, Politecnico di Torino, Turkish e-Devlet) carried a PDF signature. | ✅ |
| **A real signed document with a real origin:** `keyproof/real_docs/Team_Moneyfest_membership.pdf`, written and signed (RSA 2048) by Team Moneyfest itself; Acrobat / poppler report "Signature is Valid"; the `_EDITED` copy (one name changed) is rejected | ✅ |
| Pitch script and jury Q&A | ✅ [keyproof/docs/PITCH.md](keyproof/docs/PITCH.md) |

## What is real and what is demo

**Real:** the PDF signatures and their checks; the EdDSA-Poseidon signatures on the data cards; the circom circuit
and Groth16 proofs; the RGB token and stablecoin transfers on Bitcoin Mutinynet; the local AI.

**Demo:**
- The issuers (Banca Demo, Demo Comune di Torino, Demo Politecnico di Torino, Demo Employer SpA) and the trust root
  are ours. The people (Elena Rossi, Marco Rossi) are fictional.
- `TUSDT` is our own test stablecoin on Mutinynet (no value).
- The ZK trusted setup was a single-team ceremony (fine for a demo, not for production).
- In the demo one server plays both laptops, but the landlord side only uses what arrives in its own RGB wallet.

**Next steps:**
- Prove facts directly from the signatures real issuers already put on PDFs (as PSE's **zkPDF** does), so issuers
  don't need to add our data card.
- zkTLS for banks that only show data on their website.
- Use a real RGB stablecoin (e.g. USDT on RGB) for the deposit; Lightning for instant deposits.
- Revocation: the tenant cancels an approval by spending its token.

## Run it

**Teammates, quickest way (about 5 min, no Bitcoin, no AI needed):**
1. `git clone https://github.com/kuzeykacar/Moneyfest.git` (or *Code → Download ZIP* on GitHub)
2. In Finder, double-click `keyproof/scripts/setup_mac.command` (once), then `keyproof/scripts/run_demo.command`
3. Open http://127.0.0.1:8010 – drag the PDFs from `keyproof/demo_docs/` and `keyproof/real_docs/` onto the tenant screen.
Without the local AI running, documents are read with simple rules instead (the screen says so).

Requirements: a Mac (Apple Silicon), Python 3.10+. Everything installs into the project folder, no admin rights,
no Docker.

```
keyproof/scripts/setup_mac.command    # once: .venv with cryptography + rgb-lib
scripts/setup_ai.command              # once: Node + QVAC + Qwen3 model, then keeps the local AI running
keyproof/scripts/run_demo.command     # app with simulated RGB (no bitcoin needed)
keyproof/scripts/run_real.command     # app with real RGB on Mutinynet (wallets must be funded)
```

Open **http://127.0.0.1:8010** (EN/IT/TR). Landlords "Create a tenant check"; tenants enter the code or open the link.
Phones on the same Wi-Fi open tenant links at the address shown in the QR. `/admin.html` (host only): wallets,
issuer, developer view, start over, presenter mode.
On a Mac, double-click the `.command` files in Finder.

**Demo flow (3 minutes):** landlord describes the tenant, the local AI fills the form → adds the flat → **Publish** →
shares link / code / QR → tenant opens it (laptop or phone), sees the flat → drags the signed PDFs from
`keyproof/demo_docs/` (the `_EDITED` one is rejected) → **Create my private proof** → **Send** (RGB approval token,
~1–2 min for a block) → landlord sees ✓✓✓ → tenant **pays the deposit** (RGB stablecoin) → both see the completion
screen, the printable receipt and the downloadable ZK proof.

**Real RGB setup:** fund the issuer wallet from https://faucet.mutinynet.com, then use the wallet page (each spend
shows its cost first) or `keyproof/scripts/rgb_setup.command` to share sats, create RGB slots, and issue the
stablecoin. Details and developer commands: [keyproof/README.md](keyproof/README.md).

## Repository map

| Path | What |
|---|---|
| `keyproof/keyproof/` | Python: `pdfsig.py` (sign/verify PDFs), `zkcrypto.py` (Poseidon, Baby Jubjub, EdDSA), `ai.py` (QVAC), `rgb.py` + `rgb_setup.py` (rgb-lib wallets), `app.py` (server), `make_demo.py` (demo issuers + documents) |
| `keyproof/circuits/` | `keyproof.circom`: the circuit |
| `keyproof/web/` | `index.html` (landing), `landlord.html`, `tenant.html`, `receipt.html`, `admin.html`, `issuer.html`, `wallets.html`, `dev.html`, `simple.css`/`simple.js` (design + texts), `zk/` (snarkjs, circuit wasm, proving key, verification key) |
| `keyproof/demo_docs/` | signed demo PDFs + the edited fake |
| `keyproof/trust/` | demo root and issuer certificates (public) |
| `keyproof/tools/` | ZK setup and tests (witness, proof, browser end-to-end) |
| `keyproof/docs/PITCH.md` | 3-minute demo script and jury Q&A |
| `backend/`, `web/`, `scripts/` | **Moneyfest Aid**, our earlier idea (see below); `scripts/setup_ai.command` installs QVAC for both |

## How we got here (all during the hackathon)

1. **Saturday morning:** a budgeting idea (no code).
2. **Saturday afternoon:** *Moneyfest Aid*, private aid vouchers on RGB with an offline multilingual assistant
   (code in `backend/` and `web/`).
3. **Saturday evening → Sunday:** *KeyProof*. A jury member liked the document-verification idea but said our first
   design (a separate "verifier agent" checking metadata) wasn't trustworthy enough. We removed our own verifier
   completely: trust now comes only from the issuers' signatures and the math.

**Work done before the hackathon:** none. No code, prototypes or designs existed before kickoff.

## Security

Only Mutinynet, a Bitcoin test network, with test coins that have no value. Wallet keys, recovery words and the
demo issuers' private keys stay on our machine and are excluded by `.gitignore` (every `data/` folder is ignored).
Documents never leave the tenant's device in the design; the landlord receives only the proof.

## Team Moneyfest

| Name | GitHub |
| ---- | ------ |
| Kuzey Can Kacar | [@kuzeykacar](https://github.com/kuzeykacar) |
| Irem Sengor | [@iurisiur](https://github.com/iurisiur) |
| Ege Arca Akcay | [@arcakcy](https://github.com/arcakcy) |
| Kerem Alp Yildiz | [@keremalpyildiz](https://github.com/keremalpyildiz) |
