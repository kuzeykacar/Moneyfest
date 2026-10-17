# Moneyfest Aid build plan

Shared plan for the team. Update it when a decision changes.

## Run it

```
python3 backend/app.py
```

Open http://127.0.0.1:8000. Python 3.10+ only, nothing to install.
Leave it running: it restarts by itself when a `.py` file changes (this resets the fake wallets), and page changes show up on refresh. `MONEYFEST_RELOAD=0` turns the auto-restart off.
By default it uses **fake wallets** and **fake AI**, so everyone can work before RGB and QVAC are ready.

| Setting | Values | Default |
| ------- | ------ | ------- |
| `MONEYFEST_WALLETS` | `fake`, `rgb` | `fake` |
| `MONEYFEST_AI` | `fake`, `qvac` | `fake` |
| `QVAC_URL` | local model address | `http://127.0.0.1:11434/v1/chat/completions` |

Example with the real local model: `MONEYFEST_AI=qvac python3 backend/app.py`

## Files and owners

| File | What it does | Owner |
| ---- | ------------ | ----- |
| `backend/wallets.py` | The only place vouchers move. `FakeWallets` now; `RgbWallets` to write against the RGB Lightning Node API | RGB |
| `backend/ai.py` | The family's assistant: understand the question, phrase the answer in their language | AI |
| `backend/aid.py` | Plain code that decides: issue, send, approved shops, confirm payments, redeem, who sees what | Backend |
| `backend/app.py` | Small web server connecting everything | Backend |
| `web/index.html` | Three panels: NGO, family phone (chat), shop | UI |

## Wallets and flow

Wallets: `ngo`, `family`, `shop` (one RGB node each). Token: `FOOD` (NIA), issued by the NGO.

1. NGO issues FOOD → NGO wallet.
2. NGO → family (real transfer).
3. Family asks the assistant → payment proposal → family confirms → family → shop (real transfer).
4. Shop → NGO to redeem (real transfer). The NGO records totals per shop only.

Each role keeps its own log: the NGO never sees family purchases; the shop never sees the family's name.

## API

`GET /api/state` · `POST /api/ngo/issue {amount}` · `/api/ngo/send {amount}` · `/api/family/ask {text}` · `/api/family/confirm {id, yes}` · `/api/shop/redeem {amount}`

## Demo flow (3 minutes)

1. NGO issues 500 FOOD and sends 100 to the Yılmaz family.
2. Family asks "Ne kadar kredim kaldı?" → "100 FOOD krediniz kaldı."
3. "Elektronik Dünyası'na 30 öde" → refused: not an approved food shop.
4. "Bakkal'a 12 öde" → confirm → real transfer to the shop.
5. Shop redeems 12 → NGO sees "Bakkal Ahmet redeemed 12", no family data.

## Rules for the repo

- Never commit seeds, mnemonics, keys, `.env` or wallet data (`data/` is git-ignored).
- No force push, no rebase of pushed commits.
- Nothing pushed after Sunday 13:00 counts.
