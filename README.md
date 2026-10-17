# Moneyfest Aid

**Private aid vouchers on Bitcoin, with an offline assistant in the family's own language.**

Built for the *Agentic Dollars on Bitcoin* hackathon (BLOX Turin, 17–18 October 2026).
Tracks: **Self-custodial digital dollar apps** and **Private financial intelligence**.

> We started the weekend on a budgeting idea and changed direction on Saturday afternoon. Everything in this repository was written during the hackathon.

## The problem

After disasters such as the 2023 earthquake in Turkey, aid organisations increasingly give families digital vouchers or cash instead of food boxes. Today's blockchain aid pilots run on **public** blockchains, where every payment to a victim or refugee stays visible forever: who received aid, how much, and where they spent it. That exposes vulnerable people. Families also often have unreliable internet and do not speak English.

## The idea

- **The NGO issues its own voucher token on RGB** (for example `FOOD`) and sends it to each family's self-custodial wallet.
- **The family spends vouchers at approved shops.** Payments are private: only the family and the shop see them.
- **The shop redeems vouchers with the NGO.** The NGO sees **totals per shop**, never what a family bought.
- **A local AI assistant (QVAC) on the family's device** answers in their language, offline: "How much credit do I have left?", "Which shops accept it?", "Pay 12 to the grocery". It only understands and explains; balances, approved shops and payments are decided by code, and every payment needs the family's confirmation.

## Why RGB and why local AI

- **RGB:** the NGO issues a real asset on Bitcoin; transfers are private between sender and receiver (client-side validation), so aid recipients are not exposed on a public ledger; each receiver holds the proof of what they received.
- **QVAC:** an assistant that works without internet, in the family's own language, and keeps their questions and spending on their device.

## Stack, and what is installed and working

- **RGB Protocol on Bitcoin** on **Mutinynet**: three wallets (NGO, family, shop), one RGB Lightning Node each, run with `kaleido-cli`; the NGO issues a NIA asset. On-chain RGB transfers.
- **QVAC** (`@qvac/sdk`): a small local Qwen model behind a local OpenAI-compatible server.
- **Languages:** Python backend (standard library only) and a plain HTML/JS page.

The app runs end to end today with **fake wallets and a keyword stand-in for the AI** (see "What is real and what is simulated"). Connecting the real RGB nodes and QVAC is the next step.

## Work done before the hackathon (declared)

**No code, prototypes, designs or app existed before the hackathon.** Before kickoff (Saturday 17 October 2026, 09:30 CEST) we only chose the idea, wrote this README and planned the architecture. All product code will be written during the hackathon, in dated commits.

## Hackathon goals

A starting point; we may add, change or drop items. The final README marks each one as working, partial or not done.

1. **Issue vouchers:** the NGO wallet issues a `FOOD` token on RGB (Mutinynet).
2. **Distribute:** real RGB transfer NGO → family.
3. **Spend:** real RGB transfer family → approved shop, after the family confirms; unapproved shops are refused by code.
4. **Redeem:** real RGB transfer shop → NGO; the NGO dashboard shows totals per shop only.
5. **Local assistant:** QVAC answers balance, shop and payment questions in Turkish, Arabic and English, offline.
6. **Clear UI:** NGO, family and shop panels an outsider can follow.

## What is real and what is simulated

To be completed at submission. Today: wallets are in-memory fakes and the assistant is keyword rules (`MONEYFEST_WALLETS=fake`, `MONEYFEST_AI=fake`). Goal: real RGB transfers on Mutinynet and real QVAC answers. There is one demo family and one approved shop.

## Security

Moneyfest Aid only touches Mutinynet, a Bitcoin test network, with test tokens that have no value. Wallet seeds and keys stay on our machines and are excluded from the repository by `.gitignore`.

## Team

**Team name:** Moneyfest

| Name | GitHub |
| ---- | ------ |
| Kuzey Can Kacar | [@kuzeykacar](https://github.com/kuzeykacar) |
| Irem Sengor | [@iurisiur](https://github.com/iurisiur) |
| Ege Arca Akcay | [@arcakcy](https://github.com/arcakcy) |
| Kerem Alp Yildiz | [@keremalpyildiz](https://github.com/keremalpyildiz) |
