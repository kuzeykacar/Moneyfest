# Moneyfest

**Manifest your money, privately.**

Private, self-custodial budgeting for digital dollars. A local AI sorts your spending into envelopes and pauses the subscriptions you don't use. Your spending data never leaves your device.

Built for the *Agentic Dollars on Bitcoin* hackathon (BLOX Turin, 17–18 October 2026).
Track: **Private financial intelligence** (on-device budgeting).

## The problem

Budgeting apps work, but they ask for your bank login and send every purchase you make to their servers. Your spending history is a detailed map of your life: where you shop, what you buy, which subscriptions you forget about. Students and young workers run out of money before the end of the month, and they pay for subscriptions they no longer use.

## The idea

You write your money rules once, in plain language:

- "Every week: food 60, fun 30, transport 20."
- "Subscriptions: 40 a month. If I haven't used one in 30 days, pause it and ask me."
- "On Sunday, move whatever is left to savings."

Then a **local AI agent** (QVAC, running on your device) does the rest:

1. **Income arrives** and is split into envelopes automatically. Each envelope is a separate self-custodial wallet holding digital dollars on Bitcoin (RGB).
2. **Every payment is sorted** into the right envelope. When an envelope runs low, you get a warning before you overspend.
3. **Subscriptions are checked before they are paid.** If you haven't used a service, the agent pauses the payment and asks: keep or cancel?
4. **Leftovers go to savings** at the end of the week.

**The AI proposes, code decides, you approve.** The model sorts payments and explains its reasoning in plain words, but fixed rules in code set the limits, and no money moves outside them.

## Why local AI

- **Private by default:** your spending history and your rules stay on your device. No bank login, no cloud.
- **Works offline,** with no per-call cost, so the agent can check every single payment.
- **Self-custody:** you hold your own dollars. The app never holds funds.

## Stack (planned, final versions listed at submission)

- **RGB Protocol on Bitcoin:** a test USDT asset on **Mutinynet**. Envelopes are separate RGB wallets; budget moves and subscription payments are real RGB transfers.
- **QVAC** (`@qvac/sdk`): a small local Qwen model for sorting payments, reading plain-language rules into structured JSON, and explaining decisions.
- **Tether WDK** with `@utexo/wdk-wallet-rgb`: self-custodial envelope wallets (aiming for the WDK bonus).
- Python backend for the rules engine and wallet logic; web UI.

## Work done before the hackathon (declared)

**No product code exists in this repository before kickoff** (Saturday 17 October 2026, 09:30 CEST). All product code will be written during the hackathon, in dated commits.

Before kickoff we only:

- chose the idea and planned the architecture;
- set up our laptops (Node, Python, QVAC, model downloads) and requested test bitcoin from the Mutinynet faucet.

## Hackathon goals (17–18 October)

What we plan to build during the event. These are goals, not finished features; the final README will mark each one as working, partial or not done.

1. **Envelope wallets:** separate self-custodial RGB wallets for each envelope (food, fun, transport, subscriptions, savings), holding test USDT on Mutinynet.
2. **Plain-language rules:** the local QVAC model turns rules such as "food 60 a week" into structured JSON; code validates and stores them.
3. **Income split:** incoming money is divided into envelopes automatically, with real RGB transfers.
4. **Payment sorting:** each payment is assigned to an envelope by the local model, with a warning when an envelope runs low.
5. **Subscription check:** before a subscription is paid, the agent checks usage and pays, pauses, or asks the user. Code enforces the decision; the model explains it.
6. **Savings sweep:** leftover money moves to the savings envelope at the end of the week.
7. **Simple web UI:** envelopes, balances, warnings, and approve/decline buttons, usable by someone who did not build it.
8. **WDK (bonus):** envelope wallets built with Tether WDK and `@utexo/wdk-wallet-rgb`.

## How to run

To be completed during the hackathon, before the Sunday 13:00 deadline.

## What is real and what is simulated

To be completed at submission. Planned: all money movements are real RGB transfers on Mutinynet (test funds only). Subscription **usage data** in the demo comes from a sample file, because no real service shares usage data with a hackathon prototype.

## Security

Test networks and test funds only. Never commit `.env` files, seed phrases, mnemonics or private keys; wallets and keys live in a git-ignored data folder.

## Team

**Team name:** Moneyfest

| Name | GitHub |
| ---- | ------ |
| Kuzey Can Kacar | [@kuzeykacar](https://github.com/kuzeykacar) |
| Irem Sengor | TBD |
| Ege Arca Akcay | TBD |
| Kerem Alp Yildiz | TBD |
