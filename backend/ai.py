"""Local AI layer (QVAC).

QVAC can serve a local model behind an OpenAI-compatible HTTP API:

    npx qvac serve --openai --port 11434 --host 127.0.0.1

This file sends prompts to that local server and asks for JSON back. Nothing
leaves the laptop. If MONEYFEST_AI=fake, simple keyword rules stand in for the
model, so the rest of the team can work before QVAC is running.

The model only proposes. rules.py checks every answer before anything happens.
"""

import json
import os
import re
import urllib.request

QVAC_URL = os.environ.get("QVAC_URL", "http://127.0.0.1:11434/v1/chat/completions")
QVAC_MODEL = os.environ.get("QVAC_MODEL", "moneyfest")
USE_FAKE = os.environ.get("MONEYFEST_AI", "fake") == "fake"

CATEGORIES = ["food", "fun", "transport", "other"]


def _ask_model(system_prompt, user_text):
    """Send one prompt to the local QVAC server and return the parsed JSON."""
    body = {
        "model": QVAC_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }
    req = urllib.request.Request(
        QVAC_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = json.load(resp)["choices"][0]["message"]["content"]
    # Small models sometimes add text or "thinking" around the JSON: keep the JSON part.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"model did not return JSON: {text!r}")
    return json.loads(match.group(0))


# ---------------------------------------------------------------------------
# 1. Rules: "food 60 a week" -> {"budgets": {"food": 6000}, ...}

RULES_PROMPT = """You turn a person's budget rules into JSON. Reply with JSON only.
Format:
{"budgets": {"food": cents, "fun": cents, "transport": cents, "other": cents},
 "subscriptions_monthly": cents,
 "pause_unused_days": number,
 "sweep_leftovers_to_savings": true or false}
Budgets are per week. Amounts are in cents (60 = 6000). Leave out anything the person did not say."""


def parse_rules(text):
    if USE_FAKE:
        return _fake_parse_rules(text)
    return _ask_model(RULES_PROMPT, text)


def _fake_parse_rules(text):
    t = text.lower()
    result = {"budgets": {}}
    for cat in CATEGORIES:
        m = re.search(cat + r"\D{0,10}(\d+(?:[.,]\d+)?)", t)
        if m:
            result["budgets"][cat] = _to_cents(m.group(1))
    m = re.search(r"subscriptions?\D{0,10}(\d+(?:[.,]\d+)?)", t)
    if m:
        result["subscriptions_monthly"] = _to_cents(m.group(1))
    m = re.search(r"(\d+)\s*days", t)
    if m:
        result["pause_unused_days"] = int(m.group(1))
    if "saving" in t:
        result["sweep_leftovers_to_savings"] = True
    return result


# ---------------------------------------------------------------------------
# 1b. Commands: "pay netflix 10 euros" -> {"action": "pay", "to": "Netflix", "amount": 10}

COMMAND_PROMPT = """You turn one money instruction into JSON. Reply with JSON only.
Format: {"action": "pay" | "income" | "sweep" | "unknown", "to": "who gets paid", "amount": number}
- "pay": the person wants to pay a shop, a service, a subscription or a friend.
- "income": the person received money.
- "sweep": the person wants to move leftovers to savings.
- "unknown": anything else, or if the amount is missing.
Amounts are plain numbers in dollars or euros as written (10 euros = 10). Leave out fields you do not know."""


def parse_command(text):
    if USE_FAKE:
        return _fake_parse_command(text)
    return _ask_model(COMMAND_PROMPT, text)


def _fake_parse_command(text):
    t = text.lower().strip()
    amount = re.search(r"(\d+(?:[.,]\d+)?)", t)
    amount = float(amount.group(1).replace(",", ".")) if amount else None
    if any(w in t for w in ("sweep", "savings", "save leftovers")):
        return {"action": "sweep"}
    if any(w in t for w in ("received", "got paid", "income", "salary")):
        return {"action": "income", "amount": amount} if amount else {"action": "unknown"}
    m = re.search(r"(?:pay|send|give)\s+(?:to\s+)?([a-z][\w' ]*?)\s+\d", t)
    if m and amount:
        return {"action": "pay", "to": m.group(1).strip().title(), "amount": amount}
    return {"action": "unknown"}


# ---------------------------------------------------------------------------
# 2. Payments: "Esselunga" -> {"category": "food", "reason": "..."}

CLASSIFY_PROMPT = """You sort one payment into a budget category. Reply with JSON only.
Categories: food, fun, transport, other.
Format: {"category": "...", "reason": "one short sentence"}"""

_FAKE_SHOPS = {
    "food": ["esselunga", "carrefour", "coop", "conad", "lidl", "bakery", "pizza", "market"],
    "fun": ["bar", "cinema", "pub", "concert", "steam", "club", "spotify"],
    "transport": ["gtt", "bus", "metro", "train", "trenitalia", "uber", "taxi", "bike"],
}


def classify_payment(merchant, amount):
    if USE_FAKE:
        name = merchant.lower()
        for cat, words in _FAKE_SHOPS.items():
            if any(w in name for w in words):
                return {"category": cat, "reason": f"{merchant} looks like {cat}."}
        return {"category": "other", "reason": f"Not sure what {merchant} is."}
    return _ask_model(CLASSIFY_PROMPT, f"Merchant: {merchant}. Amount: {amount / 100:.2f} USDT.")


# ---------------------------------------------------------------------------
# 3. Explanations: turn a decision made by code into one friendly sentence.

EXPLAIN_PROMPT = """You explain a budgeting decision to the user in one short, friendly sentence.
Reply with JSON only: {"message": "..."}"""


def explain(decision):
    if USE_FAKE:
        return decision.get("summary", "Done.")
    return _ask_model(EXPLAIN_PROMPT, json.dumps(decision))["message"]


def _to_cents(number_text):
    return round(float(number_text.replace(",", ".")) * 100)
