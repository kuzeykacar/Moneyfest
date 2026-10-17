# KeyProof: pitch and jury Q&A

## 3-minute demo script
1. **Problem (20 s).** "To rent a room in Turin you send a stranger your bank statements, ID and contract.
   The landlord needs 3 answers. We send 3 answers, and a proof."
2. **Landlord (30 s).** Types "adult student, earns at least 1500 a month, studying until July 2027".
   The local AI (QVAC, on this laptop, offline) ticks the boxes. The landlord checks them and publishes.
3. **Fake (20 s).** Tenant uploads the edited PDF (one number changed). Rejected: "modified after it was signed".
4. **Real (40 s).** Tenant uploads the real signed documents: 4 checks green each.
   Creates the zero-knowledge proof on the laptop (a few seconds). Sends it as an RGB token on Bitcoin.
5. **Landlord sees (30 s).** Token arrives, wallet validates it, proof checked against the landlord's own rules:
   ✓ Identity 18+, ✓ Income ≥ €1,500, ✓ Student until 2027. "I never saw a name or a number."
6. **Deposit (20 s).** The landlord's agent asks for the deposit; the tenant's agent prepares it; tenant confirms;
   tUSDT moves on RGB. Show the transaction on the Mutinynet explorer.
7. **Close (20 s).** "Bank signature: the data is real. ZK proof: it passes your rules, privately.
   RGB on Bitcoin: the approval and the deposit can't be copied or reused."

## Jury questions

**You said last time verification wasn't trustworthy. What changed?**
We removed our own verifier (A2) completely. We don't judge if a document looks real. Only the issuer's
digital signature counts, and the math checks it. An edited PDF fails, whatever tool made the edit.

**Can the tenant fake the result on their own laptop?**
No. The landlord checks the proof on the landlord's side, against the landlord's own published rules and the
landlord's own list of trusted issuers. A proof made with easier rules, another request number, or a key that
isn't a trusted bank is rejected. Without real signed data that passes, the math can't produce a proof.

**What does the landlord actually learn?**
One ✓ per ticked check. Plus a tag that is the same for the same tenant on the same request, and different
across landlords, so landlords can't link a tenant between them.

**Do real banks sign documents like this?**
Real banks and public offices already sign PDFs (in the EU with eIDAS qualified signatures). Our demo issuers
also sign a small "data card" with a ZK-friendly signature, to fit 24 hours. The next step is proving facts
about the existing PDF signatures directly, as PSE's zkPDF does.

**Why Bitcoin and RGB? Why not just send the proof by email?**
The approval is an RGB token owned by one wallet: it can't be duplicated or quietly sent to many landlords,
it has a Bitcoin timestamp, the tenant can see and cancel it, and nothing private goes on chain (only a hash
commitment). The same rails carry the deposit, so approval and payment live in one place.

**Why on-chain and not Lightning?**
Every step is final in a Bitcoin block: permanent timestamp and simple validation. Speed isn't needed here.

**Where is the AI? Is it just a form?**
The AI turns free text into rules, on the landlord's laptop, offline (QVAC). It never decides: the landlord
confirms the boxes, the circuit decides. Same for the deposit: agents prepare, humans confirm.

**What if the bank doesn't sign?**
Then KeyProof doesn't accept the document. That's the rule. For banks that only show data on their website,
zkTLS (proving data from a bank web session) is the next step.

**Isn't checking someone's age, income, etc. still sensitive?**
Yes, which is why the landlord only gets ✓. We left criminal record out: in the EU that data is specially
protected (GDPR Art. 10) and landlords generally can't ask for it.

**How big and fast is the proof?**
About 45,000 constraints, Groth16. Proving takes seconds in the browser; the proof is under 1 KB;
checking takes milliseconds.
