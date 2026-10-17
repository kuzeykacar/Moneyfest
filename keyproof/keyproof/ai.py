"""Local AI (QVAC): turns the landlord's sentence into checkbox rules.

QVAC serves a local model with an OpenAI-compatible API (see scripts/setup_ai.command):
    npx qvac serve --openai --port 11434 --host 127.0.0.1

The AI only fills the form. The landlord sees the ticked boxes and can change them before
publishing, and all checking is done by code and the ZK circuit, never by the model.
With KEYPROOF_AI=fake (default) keyword rules stand in for the model.
"""

import json
import os
import re
import urllib.request

QVAC_URL = os.environ.get("QVAC_URL", "http://127.0.0.1:11434/v1/chat/completions")
QVAC_MODEL = os.environ.get("QVAC_MODEL", "moneyfest")
USE_FAKE = os.environ.get("KEYPROOF_AI", "fake") == "fake"

CHECKS = ["identity", "income", "occupation", "savings", "guarantor"]

PROMPT = """You turn a landlord's requirements for a tenant into JSON. Reply with JSON only, no other text.
Format:
{"identity": true/false, "income": true/false, "min_income": number, "occupation": true/false,
 "allow_student": true/false, "allow_employed": true/false, "lease_end": "YYYY-MM-DD" or "",
 "savings": true/false, "min_savings": number, "guarantor": true/false, "min_guarantor": number}
Rules:
- identity: true if they want an adult, ID, or age 18+.
- income: true if they mention salary, income, earning, or rent multiple. min_income = the monthly amount in EUR.
  If they say "3 times the rent" and give the rent, min_income = 3 * rent.
- occupation: true if they mention student, working, employed, job, contract. allow_student / allow_employed
  say which are accepted (both true if either is fine).
- lease_end: the date the lease ends, if given.
- savings: true if they mention savings, deposit money, balance. min_savings in EUR.
- guarantor: true if they mention guarantor, parents, garante, co-signer. min_guarantor = guarantor's monthly income in EUR.
- Use false and 0 for anything not mentioned. Never invent numbers."""


def _ask_model(text):
    body = {"model": QVAC_MODEL, "temperature": 0,
            "messages": [{"role": "system", "content": PROMPT},
                         {"role": "user", "content": text + " /no_think"}]}
    req = urllib.request.Request(QVAC_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        out = json.load(resp)["choices"][0]["message"]["content"]
    out = re.sub(r"<think>.*?</think>", "", out, flags=re.DOTALL)
    m = re.search(r"\{.*\}", out, re.DOTALL)
    if not m:
        raise ValueError(f"model did not return JSON: {out!r}")
    return json.loads(m.group(0))


def _num(v):
    try:
        return max(0, int(float(str(v).replace(",", "").replace("€", "").strip() or 0)))
    except ValueError:
        return 0


def _clean(raw):
    """Code decides what a valid rule is: booleans, whole euros, real dates."""
    rules = {"checks": {c: bool(raw.get(c)) for c in CHECKS},
             "minIncome": _num(raw.get("min_income")),
             "allowStudent": bool(raw.get("allow_student")),
             "allowEmployed": bool(raw.get("allow_employed")),
             "leaseEnd": raw.get("lease_end") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(raw.get("lease_end", ""))) else "",
             "minSavings": _num(raw.get("min_savings")),
             "minGuarantor": _num(raw.get("min_guarantor"))}
    ch = rules["checks"]
    if ch["occupation"] and not (rules["allowStudent"] or rules["allowEmployed"]):
        rules["allowStudent"] = rules["allowEmployed"] = True
    for check, key in (("income", "minIncome"), ("savings", "minSavings"), ("guarantor", "minGuarantor")):
        if rules[key] and not ch[check]:
            ch[check] = True
    return rules


def landlord_rules(text):
    """Landlord's sentence -> {"rules": ..., "source": "qvac" | "keywords"}."""
    if not USE_FAKE:
        try:
            return {"rules": _clean(_ask_model(text)), "source": "qvac"}
        except Exception as e:  # model down or bad JSON: keyword rules keep the demo going
            print(f"QVAC failed, using keyword rules: {e}", flush=True)
    return {"rules": _clean(_keywords(text)), "source": "keywords"}


def _amount_near(t, words):
    for w in words:
        m = re.search(w + r"[^0-9]{0,40}?(\d[\d.,]*)\s*(k\b)?", t) or re.search(r"(\d[\d.,]*)\s*(k\b)?[^0-9]{0,25}?" + w, t)
        if m:
            n = float(m.group(1).replace(",", "").rstrip("."))
            return int(n * 1000 if m.group(2) else n)
    return 0


def _keywords(text):
    t = text.lower()
    raw = {}
    raw["identity"] = bool(re.search(r"\b(adult|18|id\b|identity|age)", t))
    raw["guarantor"] = bool(re.search(r"guarant|garante|parent|co-?sign", t))
    if raw["guarantor"]:
        raw["min_guarantor"] = _amount_near(t, ["guarant\\w*", "garante", "parents?"])
    raw["savings"] = bool(re.search(r"saving|balance|in the bank", t))
    if raw["savings"]:
        raw["min_savings"] = _amount_near(t, ["savings?", "balance"])
    raw["income"] = bool(re.search(r"income|earn|salary|stipend|per month|/month|a month", t))
    if raw["income"]:
        raw["min_income"] = _amount_near(t, ["income", "earns?", "earning", "salary"])
        rent = _amount_near(t, ["rent"])
        mult = re.search(r"(\d)\s*(x|times)\s*(the\s*)?rent", t)
        if mult and rent:
            raw["min_income"] = int(mult.group(1)) * rent
    student = bool(re.search(r"student|universit|studying|enrol", t))
    employed = bool(re.search(r"employ|working|\bjob\b|contract|worker", t))
    raw["occupation"] = student or employed
    raw["allow_student"], raw["allow_employed"] = student, employed
    d = re.search(r"(20\d\d-\d\d-\d\d)", t)
    raw["lease_end"] = d.group(1) if d else ""
    return raw


if __name__ == "__main__":
    for s in ["Student in Turin, earns at least 1500 a month, must be an adult",
              "Working professional, salary 2000+, savings of 5000",
              "Students welcome, parents as guarantor with 3000 income",
              "Rent is 600, tenant must earn 3 times the rent",
              "Anyone over 18 with a job contract until 2027-06-30"]:
        print(s, "->", landlord_rules(s))
