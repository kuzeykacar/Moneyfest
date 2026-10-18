# KeyProof – 3-minute pitch + live demo

**One line:** Prove you qualify for a flat without handing over your documents.
**Stack:** issuer signatures + zero-knowledge proof (privacy) · RGB on Bitcoin (approval + deposit) · QVAC local AI (reads documents on your device) · Tether WDK (tenant wallet).
**Rule we never break:** *the AI helps, the math decides.*

---

## 0:00 – The problem (20 s)
> "To rent a room in Turin you send a stranger your ID, payslips and bank statements – by email, to people you've never met.
> Landlords only need a few yes/no answers: is she an adult, does she earn enough, is she a student until the lease ends.
> And they still can't tell if the PDF was edited – it takes 30 seconds."

## 0:20 – Landlord (30 s) — screen: Landlord
1. "Giulia writes what she wants in her own words: *adult female student, earns at least 1,500*."
2. Click **Fill in the form for me** → "the local AI – QVAC, running on this laptop – fills the requirements. She checks them; the AI never decides."
3. Show the flat details → **Publish** → "she gets a code, a link and a QR for her Idealista listing."

## 0:50 – Tenant (60 s) — screen: Tenant (phone QR or laptop)
1. Open the link / scan the QR → "Elena sees the flat and exactly what's asked: adult, a woman, income, student."
2. Drag **2_Income_statement_Elena_Rossi_EDITED.pdf** → rejected: *modified after it was signed*.
   > "Someone changed 1,650 to 2,650. The issuer's digital signature breaks – instantly."
3. Drag all the real ones (`demo_docs/`) → green ticks + blue boxes.
   > "Now the local AI reads her ID and bank documents **on her own laptop** – sorts them, checks them against the rules, and gives private advice. That's why it must be local: it reads the most private data in the whole flow. Nothing is uploaded."
4. Optional (10 s): drag a **real** unsigned bank statement → "read by the AI, but *can't prove it's genuine* – so it never counts."
5. **Create my private proof** (~10 s) → **Send**.
   > "Her laptop builds a zero-knowledge proof: *every rule is met, using data signed by trusted issuers.* No name, no amount, no birth date leaves her computer."

## 1:50 – Bitcoin (30 s)
> "The proof travels inside an **RGB token on Bitcoin** to Giulia's wallet – timestamped, owned, can't be swapped later."
- Landlord screen: ✓ adult · ✓ woman · ✓ income · ✓ student — "verified on **her** computer, against **her** rules and **her** list of trusted issuers. She never saw a document."
- Tenant pays the deposit → "a stablecoin on RGB, from Elena's self-custodial wallet built on **Tether WDK**."
- Completion screen → **Download proof** / **Check again**: "anyone – a notary, a bank – can re-verify this with open-source tools."

## 2:20 – Why it's real (25 s)
> "We tested six real documents from five institutions in two countries – UniCredit, Agenzia delle Entrate, Politecnico, Turkish e-Devlet, a utility.
> **None was digitally signed.** They all *look* official, and all can be edited. That's the gap.
> KeyProof only says ✓ when it's mathematically proven: today for signed documents, next with zkTLS for anything verifiable online – home banking, e-Devlet barcodes, university portals."

## 2:45 – Close (15 s)
> "Tenants keep their privacy, landlords get proof instead of paperwork, and the money moves on Bitcoin.
> **The AI helps, the math decides.** KeyProof."

---

## Slide: what's real today / what's next

| Real today | Next |
|---|---|
| Digital-signature checks (ECDSA + RSA, edited files rejected) | Real issuers (banks, comuni, universities) signing data cards |
| ZK circuit (Groth16, ~45k constraints): age, sex, income, occupation, savings, guarantor, freshness, same person | zkPDF / zkTLS: prove from existing signatures or issuer websites |
| Proof made and verified in the browser; downloadable, verifiable by anyone | EU Trusted Lists (eIDAS) via EU DSS as the trust list |
| RGB approval token + stablecoin deposit on Bitcoin (Mutinynet test network) | Mainnet + a real RGB stablecoin (e.g. USDT on RGB) |
| QVAC local AI on both sides (Qwen3.5 4B, ~4 s per document) | Deposit fully through the WDK wallet |
| Tether WDK self-custodial tenant wallet | Multi-party trusted setup, revocation, hosted HTTPS |
| Phone QR, receipts, EN / IT / TR | Accounts, multiple listings and applicants |

**Demo data is clearly marked:** issuers are "Moneyfest … (test)", the person (Elena Rossi) is fictional, the network is a test network.

---

## Jury Q&A (short answers)

- **Can't the tenant just edit the PDF?** Edited files break the issuer's signature (shown live). And the proof uses only issuer-signed values, never the visible text.
- **What if I sign a fake document myself – even with true data?** Your key isn't on the landlord's trust list → refused. The landlord trusts the bank, not the tenant.
- **What if someone hacks the local AI?** It only changes their own screen. The proof is built from signed data, and the landlord verifies on their own computer.
- **Why local AI and not ChatGPT?** It reads your ID and bank statements. A cloud AI means uploading them. QVAC keeps them on your device.
- **Why Bitcoin / RGB?** The approval is a bearer token with an on-chain timestamp and single owner; the deposit is a stablecoin on the same rails; RGB keeps the details off the public chain.
- **Why zero-knowledge, not just signatures?** A signature alone means showing the document. ZK proves "income ≥ 1,500" without revealing 1,650.
- **What does the landlord learn?** Only ✓/✗ per requirement, and that the documents came from trusted issuers.
- **Are real documents signed today?** Mostly not – we tested six; none were. Signed contracts, invoices and PA acts exist under eIDAS; KeyProof gives issuers a reason to sign tenant documents too.
- **The sex requirement – is that legal?** Only for rooms in a shared flat or the landlord's own home; the app says so. Otherwise it may be discrimination.
- **Who did the ZK setup?** Our team (a demo ceremony). Production needs a multi-party ceremony.

## Before you start (checklist)
- [ ] `restart_app.command` running (KeyProof + WDK service), local AI window (`start_ai_4b`) running.
- [ ] Mac on the **same Wi-Fi as the phone** (or the phone's hotspot) → reload the landlord page so the QR shows the right address.
- [ ] Admin page → **Start over**, so you begin from a clean request.
- [ ] Finder open at `keyproof/demo_docs/` for dragging.
- [ ] Tenant wallet has enough TUSDT for the deposit (Wallets page).
