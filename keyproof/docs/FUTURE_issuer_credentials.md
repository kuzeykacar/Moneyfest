# Future idea: issuers send credentials straight to the tenant's wallet (no PDF)

**Status:** prototyped and tested on Bitcoin Mutinynet during the hackathon, then removed from the app to keep
the demo focused on signed PDFs. Kept here as a design note.

## The idea
Instead of downloading a signed PDF, the tenant receives the **signed data card itself** from the bank, comune or
university, as an **RGB token** in their own wallet:

1. The issuer creates a small RGB asset (UDA, ticker `KPCRED`) whose attached media is
   `{"kind": "KeyProof credential", "label": "...", "card": {type, holder, v1, v2, issuedAt, sig}, "issuer_cert": PEM}`.
2. It sends it on-chain to the tenant's RGB wallet (several credentials can go in one Bitcoin transaction).
3. The tenant's app checks each credential exactly like a PDF: the RGB contract commits to the media hash
   (not changed), the issuer certificate chains to the trusted root (trusted issuer), dates and revocation
   (still valid), and the issuer may vouch for that type (right issuer).
4. Valid credentials fill the document slots and feed the same zero-knowledge proof. No PDF, no upload, no AI parsing needed.

## What we proved on-chain
3 credentials (identity, income, enrolment) sent issuers → tenant in **one transaction**:
[fa94519c…](https://mutinynet.com/tx/fa94519c3b22f806f26c751851ccf4eb1b093a5817d26ba79bfb50f29e1616a5).

## Why it's attractive
- Issuers sign once, tenants own their credentials and reuse them for any landlord.
- Revocation could be modelled by the issuer spending or re-issuing state.
- Works with self-custodial wallets (e.g. the tenant's Tether WDK wallet).

## Why it's not in the demo
It needs issuers to run RGB wallets, which is further from today's world than signed PDFs. The PDF path shows the
same cryptography with documents people already have.

## Where the code was
Git history before the commit "Remove issuer-to-wallet credentials from the app": `Demo.issuer_send`,
`Demo.wallet_credentials`, `RealRgb.send_credentials` / `tenant_credentials`, `pdfsig.verify_credential`,
`web/issuer.html`, and the tenant's "In your wallet" card.
