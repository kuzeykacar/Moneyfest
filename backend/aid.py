"""Aid program logic: plain code that decides what happens to the vouchers.

Flow: NGO issues FOOD vouchers -> sends them to a family -> the family pays an
approved shop -> the shop redeems the vouchers back to the NGO.

Privacy by design: each role keeps its own log. The NGO only learns how many
vouchers it sent and how many each shop redeemed. It never sees what a family
bought or where. That mirrors RGB: only the sender and receiver see a transfer.
"""

import itertools
import time

import ai

TICKER = "FOOD"
FAMILY = "Yılmaz family"
SHOP = "Bakkal Ahmet"                 # approved grocery, the real shop wallet
UNAPPROVED = ["Elektronik Dünyası"]   # known shops that may NOT take food vouchers


class AidProgram:
    def __init__(self, wallets):
        self.wallets = wallets
        self.asset_id = None
        self.issued = 0
        self.sent_to_families = 0
        self.redeemed = {}                  # shop name -> vouchers redeemed (all the NGO sees)
        self.logs = {"ngo": [], "family": [], "shop": []}
        self.chat = []                      # the family's conversation, stays on their device
        self.pending = {}                   # payments waiting for the family's yes
        self._ids = itertools.count(1)

    # ------------------------------------------------------------------ NGO
    def issue(self, amount):
        amount = _positive_int(amount)
        self.asset_id = self.wallets.issue("ngo", TICKER, amount)
        self.issued += amount
        self._log("ngo", f"Issued {amount} {TICKER} vouchers on RGB.")
        return {"asset_id": self.asset_id, "issued": amount}

    def send_to_family(self, amount):
        amount = _positive_int(amount)
        transfer = self.wallets.send("ngo", "family", amount)
        self.sent_to_families += amount
        self._log("ngo", f"Sent {amount} {TICKER} to {FAMILY}.", transfer)
        self._log("family", f"Received {amount} {TICKER} from the aid program.", transfer)
        return {"transfer": transfer}

    # --------------------------------------------------------------- family
    def ask(self, text):
        """The family writes in their language; the assistant answers in the same language."""
        self.chat.append({"from": "family", "text": text})
        intent = ai.understand(text, [SHOP] + UNAPPROVED)
        lang = intent.get("language", "en")
        kind = intent.get("intent")

        if kind == "balance":
            reply = ai.answer("balance", lang, {"balance": self.wallets.balance("family")})
        elif kind == "shops":
            reply = ai.answer("shops", lang, {"shops": SHOP})
        elif kind == "pay":
            reply, _ = self._prepare_payment(intent.get("shop", ""), intent.get("amount", 0), lang)
        else:
            reply = ai.answer("help", lang, {})
        self.chat.append({"from": "assistant", "text": reply})
        return {"reply": reply, "pending": list(self.pending.values())}

    def _prepare_payment(self, shop, amount, lang):
        """Rules come from code, not from the model."""
        shop = _match_shop(shop)
        reason = None
        if not shop:
            reason = ai.reason("unknown_shop", lang)
        elif shop != SHOP:
            reason = ai.reason("not_approved", lang, shop=shop)
        elif not isinstance(amount, (int, float)) or amount <= 0:
            reason = ai.reason("no_amount", lang)
        elif amount > self.wallets.balance("family"):
            reason = ai.reason("too_much", lang, left=self.wallets.balance("family"))
        if reason:
            return ai.answer("error", lang, {"reason": reason}), None
        pid = str(next(self._ids))
        self.pending[pid] = {"id": pid, "shop": shop, "amount": int(amount), "language": lang}
        return ai.answer("pay", lang, {"shop": shop, "amount": int(amount)}), pid

    def confirm(self, pid, yes):
        p = self.pending.pop(str(pid))
        if not yes:
            self.chat.append({"from": "assistant", "text": "—"})
            return {"status": "cancelled"}
        transfer = self.wallets.send("family", "shop", p["amount"])
        self._log("family", f"Paid {p['amount']} {TICKER} to {p['shop']}.", transfer)
        self._log("shop", f"Received {p['amount']} {TICKER} voucher payment.", transfer)  # no family name
        self.chat.append({"from": "assistant", "text": ai.answer("paid", p["language"], {})})
        return {"status": "paid", "transfer": transfer}

    # ----------------------------------------------------------------- shop
    def redeem(self, amount):
        amount = _positive_int(amount)
        transfer = self.wallets.send("shop", "ngo", amount)
        self.redeemed[SHOP] = self.redeemed.get(SHOP, 0) + amount
        self._log("shop", f"Redeemed {amount} {TICKER} with the aid program.", transfer)
        self._log("ngo", f"{SHOP} redeemed {amount} {TICKER}.", transfer)
        return {"transfer": transfer}

    # ---------------------------------------------------------------- views
    def state(self):
        w = self.wallets
        return {
            "ticker": TICKER, "asset_id": self.asset_id, "family": FAMILY, "shop": SHOP,
            "ngo": {"balance": w.balance("ngo"), "issued": self.issued,
                    "sent_to_families": self.sent_to_families, "redeemed": self.redeemed,
                    "log": self.logs["ngo"][:20]},
            "family": {"balance": w.balance("family"), "chat": self.chat[-20:],
                       "pending": list(self.pending.values()), "log": self.logs["family"][:20]},
            "shop": {"balance": w.balance("shop"), "log": self.logs["shop"][:20]},
        }

    def _log(self, role, text, transfer=None):
        self.logs[role].insert(0, {"time": time.strftime("%H:%M:%S"), "text": text, "transfer": transfer})


# Words a family might use for each known shop, in Turkish, English and Arabic.
_SHOP_WORDS = {
    SHOP: ["bakkal", "grocery", "market", "food shop", "ahmet", "بقال", "بقالة", "سوق"],
    UNAPPROVED[0]: ["elektronik", "electronic", "electronics", "إلكترونيات"],
}


def _match_shop(name):
    """Map whatever the family or the model said to a known shop name, or ''."""
    n = (name or "").lower()
    if not n:
        return ""
    for shop, words in _SHOP_WORDS.items():
        if n == shop.lower() or any(w in n for w in words):
            return shop
    return name   # unknown shop: the rules will refuse it


def _positive_int(value):
    n = int(float(str(value).replace(",", ".")))
    if n <= 0:
        raise ValueError("Amount must be more than zero.")
    return n
