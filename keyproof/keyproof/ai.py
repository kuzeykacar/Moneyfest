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

# Qwen3.5 4B Multimodal (scripts/start_ai_4b.command) first, the older Qwen3 1.7B as backup.
ENDPOINTS = [(os.environ.get("QVAC_URL", "http://127.0.0.1:11436/v1/chat/completions"),
              os.environ.get("QVAC_MODEL", "keyproof"), "Qwen3.5 4B"),
             ("http://127.0.0.1:11434/v1/chat/completions", "moneyfest", "Qwen3 1.7B")]
LAST_MODEL = {"name": None}
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


def chat(system, user, max_tokens=400):
    """Ask the local model; tries the 4B model first, then the 1.7B one."""
    last = None
    for url, model, name in ENDPOINTS:
        body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
                "reasoning_budget": 0,          # answer directly, no long "thinking" first (Qwen3.5)
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user + " /no_think"}]}
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                out = json.load(resp)["choices"][0]["message"].get("content") or ""
            if not out.strip():
                raise ValueError("empty answer")
            LAST_MODEL["name"] = name
            return re.sub(r"<think>.*?</think>", "", out, flags=re.DOTALL).strip()
        except Exception as e:
            last = e
    raise ConnectionError(f"no local model answered: {last}")


def _ask_model(text):
    out = chat(PROMPT, text)
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
            return {"rules": _clean(_ask_model(text)), "source": "qvac", "model": LAST_MODEL["name"]}
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


# ---------------------------------------------------------------------------
# Helper texts: the AI explains, in the user's language. It never decides anything:
# every fact comes from code (the request, the signature checks, the proof result).

LANGS = {"en": "English", "it": "Italian", "tr": "Turkish"}

EXPLAIN_PROMPT = """You are a kind helper inside KeyProof, an app for renting a flat.
Write for an older person who is not technical: short sentences, everyday words, no jargon
(never say: hash, ZK, zero-knowledge, RGB, token, blockchain, cryptography, certificate).
Use ONLY the facts given. Never invent numbers, names, documents or results.
Write in {lang}. Reply with plain text only, at most {n} sentences."""

TASKS = {
    "request": ("The landlord's requirements are in 'facts'. Explain to the tenant what the landlord asks for, "
                "and for each item which official document they need and where they usually get it "
                "(bank, municipality/comune, university, employer). Mention that the documents stay on their "
                "computer and the landlord only sees yes or no.", 5),
    "rejected": ("A document was refused. 'facts' says which document and why. Explain kindly what this means "
                 "and what the person can do next (for example ask the issuer for a new signed copy).", 3),
    "accepted": ("A document was checked and accepted. 'facts' says which one and who issued it. "
                 "Confirm it in one or two friendly sentences.", 2),
    "summary": ("Write a short summary for the landlord. 'facts' lists which checks passed. "
                "Say clearly that they did not see the tenant's documents, salary or personal details, "
                "and what the next step is (the deposit).", 3),
    "deposit": ("Write the deposit request message the landlord's assistant sends to the tenant. "
                "'facts' has the amount. Polite, two sentences.", 2),
}

FALLBACK = {
    "request": {"en": "The landlord asks for: {items}. You will need official signed documents from your bank, your "
                      "municipality and your university or employer. They stay on your computer: the landlord only "
                      "sees yes or no.",
                "it": "Il proprietario chiede: {items}. Ti servono documenti ufficiali firmati dalla banca, dal comune "
                      "e dall'università o dal datore di lavoro. Restano sul tuo computer: il proprietario vede solo sì o no.",
                "tr": "Ev sahibi şunları istiyor: {items}. Bankanızdan, belediyeden ve üniversiteniz ya da "
                      "işvereninizden imzalı resmi belgelere ihtiyacınız var. Belgeler bilgisayarınızda kalır: "
                      "ev sahibi yalnızca evet ya da hayır görür."},
    "rejected": {"en": "This document could not be accepted: {why}. Please ask the issuer for a new signed copy.",
                 "it": "Questo documento non può essere accettato: {why}. Chiedi all'ente una nuova copia firmata.",
                 "tr": "Bu belge kabul edilemedi: {why}. Lütfen kurumdan yeni imzalı bir kopya isteyin."},
    "accepted": {"en": "Your {doc} from {issuer} is original and was accepted.",
                 "it": "Il tuo documento ({doc}) di {issuer} è originale ed è stato accettato.",
                 "tr": "{issuer} tarafından verilen belgeniz ({doc}) orijinal ve kabul edildi."},
    "summary": {"en": "The tenant meets all your requirements: {items}. You did not see any document or personal "
                      "detail. Next step: the deposit.",
                "it": "L'inquilino soddisfa tutti i requisiti: {items}. Non hai visto documenti né dati personali. "
                      "Prossimo passo: il deposito.",
                "tr": "Kiracı tüm şartlarınızı karşılıyor: {items}. Hiçbir belge ya da kişisel bilgi görmediniz. "
                      "Sonraki adım: depozito."},
    "deposit": {"en": "Good news: you are approved. Please pay the deposit of {amount} to confirm the flat.",
                "it": "Buone notizie: sei stato approvato. Paga il deposito di {amount} per confermare l'appartamento.",
                "tr": "Müjde: onaylandınız. Daireyi onaylamak için {amount} depozitoyu ödeyin."},
}


def explain(kind, lang, facts):
    """Plain-language helper text. Falls back to fixed sentences if the model is off."""
    lang = lang if lang in LANGS else "en"
    task, n = TASKS[kind]
    if not USE_FAKE:
        try:
            out = chat(EXPLAIN_PROMPT.format(lang=LANGS[lang], n=n),
                       task + "\nfacts: " + json.dumps(facts, ensure_ascii=False), max_tokens=260)
            out = re.sub(r"\s+", " ", out).strip().strip('"')
            if out:
                return {"text": out, "source": "qvac", "model": LAST_MODEL["name"]}
        except Exception as e:
            print(f"QVAC explain failed: {e}", flush=True)
    vals = {"items": ", ".join(facts.get("items", [])), "why": facts.get("why", ""),
            "doc": facts.get("doc", ""), "issuer": facts.get("issuer", ""), "amount": facts.get("amount", "")}
    return {"text": FALLBACK[kind][lang].format(**vals), "source": "fixed"}
