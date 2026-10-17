"""Local AI layer (QVAC): the family's assistant.

It runs on the family's own device, offline, and speaks their language.
QVAC serves a local model behind an OpenAI-compatible HTTP API, for example:

    npx qvac serve --openai --port 11434 --host 127.0.0.1

With MONEYFEST_AI=fake (the default), simple keyword rules stand in for the
model, so the app works before QVAC is running.

Safety rule: the model only understands the question and phrases the answer.
Balances, shop lists and payments come from code (aid.py), never from the model.
"""

import json
import os
import re
import urllib.request

QVAC_URL = os.environ.get("QVAC_URL", "http://127.0.0.1:11434/v1/chat/completions")
QVAC_MODEL = os.environ.get("QVAC_MODEL", "moneyfest")
USE_FAKE = os.environ.get("MONEYFEST_AI", "fake") == "fake"


def _ask_model(system_prompt, user_text):
    """Send one prompt to the local QVAC server and return its text answer."""
    body = {"model": QVAC_MODEL, "temperature": 0,
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_text + " /no_think"}]}
    req = urllib.request.Request(QVAC_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = json.load(resp)["choices"][0]["message"]["content"]
    # Qwen models may "think out loud" inside <think> tags: keep only the final answer.
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _json_from(text):
    """Small models sometimes add words or 'thinking' around the JSON: keep the JSON part."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"model did not return JSON: {text!r}")
    return json.loads(match.group(0))


# ---------------------------------------------------------------------------
# 1. Understand: "Ne kadar kredim kaldı?" -> {"intent": "balance", "language": "tr"}

UNDERSTAND_PROMPT = """You help a family that receives food aid vouchers. Read their message and reply with JSON only.
Format: {"intent": "balance" | "shops" | "pay" | "help", "shop": "shop name or empty", "amount": number or 0, "language": "tr" | "ar" | "en"}
- "balance": they ask how much credit is left.
- "shops": they ask where they can use the vouchers.
- "pay": they want to pay a shop. Fill "shop" and "amount".
- "help": anything else.
"language" is the language the message is written in."""


def detect_language(text):
    """Decided by code, not the model: small models mislabel languages."""
    t = text.lower()
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"
    if re.search(r"[çğıöşü]|\b(ne|kadar|kredi|dükkan|dukkan|öde|ode|nerede|hangi|merhaba|bakkal)", t):
        return "tr"
    return "en"


def understand(text, shop_names):
    if USE_FAKE:
        result = _fake_understand(text, shop_names)
    else:
        hint = (f"\nKnown shops: {', '.join(shop_names)}. If the message names one of them or a shop like it, "
                "put that exact known name in \"shop\".")
        result = _json_from(_ask_model(UNDERSTAND_PROMPT + hint, text))
    result["language"] = detect_language(text)
    return result


def _fake_understand(text, shop_names):
    t = text.lower()
    lang = "ar" if re.search(r"[؀-ۿ]", text) else (
        "tr" if re.search(r"[çğıöşü]|kredi|kaldı|dükkan|öde|nerede", t) else "en")
    amount = re.search(r"(\d+)", t)
    amount = int(amount.group(1)) if amount else 0
    shop = next((s for s in shop_names if s.lower().split()[0] in t), "")
    if amount and (shop or any(w in t for w in ("öde", "pay", "ادفع"))):
        return {"intent": "pay", "shop": shop, "amount": amount, "language": lang}
    if any(w in t for w in ("dükkan", "nerede", "where", "shop", "store", "متجر", "أين")):
        return {"intent": "shops", "shop": "", "amount": 0, "language": lang}
    if any(w in t for w in ("kaldı", "ne kadar", "bakiye", "left", "balance", "how much", "كم", "رصيد")):
        return {"intent": "balance", "shop": "", "amount": 0, "language": lang}
    return {"intent": "help", "shop": "", "amount": 0, "language": lang}


# ---------------------------------------------------------------------------
# 2. Answer: facts from code -> one friendly sentence in the family's language

ANSWER_PROMPT = """You are a kind assistant for a family receiving food aid. Write a short, simple answer
(1 to 2 sentences) in the language given by "language" (tr = Turkish, ar = Arabic, en = English).
Use ONLY the facts given. Never invent numbers or shops. Reply with plain text only."""

_FAKE_ANSWERS = {
    "balance": {"tr": "{balance} FOOD krediniz kaldı.",
                "en": "You have {balance} FOOD credit left.",
                "ar": "لديك {balance} من رصيد الطعام."},
    "shops": {"tr": "Kuponlarınızı şu dükkanlarda kullanabilirsiniz: {shops}.",
              "en": "You can use your vouchers at: {shops}.",
              "ar": "يمكنك استخدام القسائم في: {shops}."},
    "pay": {"tr": "{shop} için {amount} FOOD ödemesi hazır. Onaylıyor musunuz?",
            "en": "A payment of {amount} FOOD to {shop} is ready. Do you confirm?",
            "ar": "دفعة {amount} طعام إلى {shop} جاهزة. هل تؤكد؟"},
    "paid": {"tr": "Ödeme gönderildi.", "en": "Payment sent.", "ar": "تم إرسال الدفعة."},
    "error": {"tr": "Bu ödeme yapılamadı: {reason}", "en": "This payment can't be made: {reason}",
              "ar": "لا يمكن إجراء هذه الدفعة: {reason}"},
    "help": {"tr": "Bakiyenizi, dükkanları sorabilir veya ödeme yapabilirsiniz. Örnek: \"Bakkal'a 12 öde\".",
             "en": "You can ask for your balance, the shops, or make a payment. Example: \"Pay 12 to Bakkal\".",
             "ar": "يمكنك السؤال عن رصيدك أو المتاجر أو الدفع."},
}


_REASONS = {
    "unknown_shop": {"tr": "dükkan bulunamadı", "en": "shop not recognised", "ar": "المتجر غير معروف"},
    "not_approved": {"tr": "{shop} onaylı bir gıda dükkanı değil", "en": "{shop} is not an approved food shop",
                     "ar": "{shop} ليس متجر طعام معتمد"},
    "no_amount": {"tr": "tutar eksik", "en": "amount missing", "ar": "المبلغ مفقود"},
    "too_much": {"tr": "sadece {left} FOOD kaldı", "en": "only {left} FOOD left", "ar": "تبقى {left} فقط"},
}


def reason(code, language, **facts):
    """Why a payment was refused, in the family's language. Decided by code, not the model."""
    lang = language if language in ("tr", "en", "ar") else "en"
    return _REASONS[code][lang].format(**facts)


# Replies about money are fixed, checked sentences: the model must never say a payment
# happened before the family confirmed it, or change a number or unit.
_FIXED_KINDS = {"balance", "pay", "paid", "error"}


def answer(kind, language, facts):
    if USE_FAKE or kind in _FIXED_KINDS:
        lang = language if language in ("tr", "en", "ar") else "en"
        return _FAKE_ANSWERS[kind][lang].format(**facts)
    return _ask_model(ANSWER_PROMPT, json.dumps({"kind": kind, "language": language, "facts": facts},
                                               ensure_ascii=False)).strip()
