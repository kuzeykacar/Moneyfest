# Moneyfest build plan

Shared plan for the team. Update it when a decision changes.

## Run it

```
python3 backend/app.py
```

Open http://127.0.0.1:8000. Python 3.10+ only, nothing to install.
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
| `backend/wallets.py` | The only place money moves. `FakeWallets` now; `RgbWallets` to write with rgb-lib-python | RGB |
| `backend/ai.py` | Prompts to the local QVAC model: parse rules, sort payments, explain decisions | AI |
| `backend/rules.py` | Plain code that decides: budgets, warnings, subscription check, savings sweep | Backend |
| `backend/app.py` | Small web server connecting everything | Backend |
| `web/index.html` | The page: wallets, envelopes, decisions, activity | UI |
| `backend/sample_data/usage.json` | Sample data: days since each subscription was used | Backend |

Work in your own files to avoid merge conflicts. Pull before you push.

## Data shapes (agreed)

**Money is always integer cents**: 1250 means 12.50 USDT. Never floats.

**Wallets** (`wallets.py`), names: `spending`, `subscriptions`, `savings`, `shop`
- `balance(wallet) -> int` settled cents
- `send(from_wallet, to_wallet, amount) -> transfer_id`
- `status(transfer_id) -> "settling" | "settled" | "failed"`
- `refresh()`

**AI** (`ai.py`) returns JSON; `rules.py` validates everything:
- `parse_rules(text)` → `{"budgets": {"food": 6000, ...}, "subscriptions_monthly": 4000, "pause_unused_days": 30, "sweep_leftovers_to_savings": true}`
- `classify_payment(merchant, amount)` → `{"category": "food|fun|transport|other", "reason": "..."}`
- `explain(decision)` → one friendly sentence

**API** (`app.py`): `GET /api/state`; `POST /api/rules {text}`, `/api/income {amount}`, `/api/pay {merchant, amount}`, `/api/subscription {name, amount}`, `/api/sweep`, `/api/decide {id, approve}`.

## Wallet design

- Income arrives in **spending** (in the demo: funded from the KaleidoSwap faucet).
- The monthly subscriptions budget moves **spending → subscriptions**.
- Payments go **spending → shop**; subscriptions go **subscriptions → shop**.
- The weekly sweep moves leftovers **spending → savings**.
- Food, fun, transport and other are **budgets tracked in code** inside the spending wallet, not separate wallets. This keeps the number of RGB wallets at 4.

RGB transfers are not instant: wait for a block (~30 s on Mutinynet) and refresh both wallets. A wallet cannot spend money that is still settling.

## Milestones

| When | Done means |
| ---- | ---------- |
| Sat 13:00 | One real RGB transfer settled · QVAC returns correct JSON for a rule · UI shows fake data |
| Sat 18:00 | `RgbWallets` and `MONEYFEST_AI=qvac` both work in the app |
| Sat night | Full demo flow once, end to end, with real RGB and QVAC |
| Sun 10:00 | Polish, error handling, rehearse the 3-minute demo |
| Sun 12:30 | README: how to install and run, what was built, what is mocked, RGB and QVAC features used. Final push before 13:00 |

## Demo flow (3 minutes)

1. Type rules in plain language → the AI turns them into envelopes.
2. Income arrives → the subscriptions budget moves to its own wallet (real RGB transfer).
3. Pay Esselunga → sorted into food. Pay a cinema over the fun budget → the app asks first.
4. Gym is due but unused for 34 days → paused, "Keep or cancel?"
5. End the week → leftovers move to savings (real RGB transfer).

## Rules for the repo

- Never commit seeds, mnemonics, keys, `.env` or wallet data (`data/` is git-ignored).
- No force push, no rebase of pushed commits.
- Nothing pushed after Sunday 13:00 counts.
