# Moneyfest @ Agentic Dollars on Bitcoin

Team **Moneyfest**, *Agentic Dollars on Bitcoin* hackathon (BLOX Turin, 17–18 October 2026).

## Our project: 🔑 KeyProof → [`keyproof/`](keyproof/)

**Prove you qualify for a flat without showing your documents.**

Tenants send landlords full bank statements, IDs and contracts, but landlords only need a few yes/no answers.
With KeyProof the tenant proves those answers from documents the bank, the city office or the university already
**digitally signed**, using a **zero-knowledge proof**. The approval travels to the landlord as an **RGB token on
Bitcoin**, and the deposit is paid in an RGB stablecoin. A **local AI (QVAC)** turns the landlord's sentence into
checkboxes, but never decides anything.

Everything (code, circuit, demo documents, how to run it, what is real) is in **[keyproof/README.md](keyproof/README.md)**.
Pitch script and jury Q&A: [keyproof/docs/PITCH.md](keyproof/docs/PITCH.md).

| Mandatory / bonus tech | How KeyProof uses it |
|---|---|
| **RGB** (required) | approval token (UDA) carrying the proof hash, sent on-chain to the landlord; deposit in an RGB stablecoin (NIA), on Bitcoin Mutinynet via rgb-lib |
| **QVAC** (required) | Qwen3 1.7B running locally: landlord text → rules, offline |
| ZK | circom circuit + Groth16 (snarkjs), proof made in the tenant's browser, checked in the landlord's browser |

## History of this repository

We changed direction twice during the hackathon, and all of it is here in dated commits:

1. A budgeting idea (Saturday morning, no code).
2. **Moneyfest Aid**: private aid vouchers on RGB with an offline assistant (Saturday afternoon).
   Its code is still in [`backend/`](backend/), [`web/`](web/) and [`scripts/`](scripts/); it runs with fake wallets.
3. **KeyProof** (Saturday evening → Sunday), after feedback from a jury member: our final project.

**Work done before the hackathon:** no code, prototypes or designs. Everything was written during the event.

## Security

Only Mutinynet, a Bitcoin test network, with test coins that have no value. Wallet keys, recovery words and the
demo issuers' private keys stay on our machine and are excluded by `.gitignore` (every `data/` folder).

## Team

| Name | GitHub |
| ---- | ------ |
| Kuzey Can Kacar | [@kuzeykacar](https://github.com/kuzeykacar) |
| Irem Sengor | [@iurisiur](https://github.com/iurisiur) |
| Ege Arca Akcay | [@arcakcy](https://github.com/arcakcy) |
| Kerem Alp Yildiz | [@keremalpyildiz](https://github.com/keremalpyildiz) |
