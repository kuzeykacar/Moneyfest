"""Rules engine: plain code that decides what happens to the money.

The AI proposes (a category, a parsed rule). This file checks the proposal
against the user's rules and decides. Only this file calls wallets.send().

Amounts are integers in cents.
"""

import itertools
import json
import os
import time

from ai import CATEGORIES

SAMPLE_USAGE = os.path.join(os.path.dirname(__file__), "sample_data", "usage.json")

DEFAULT_RULES = {
    "budgets": {"food": 6000, "fun": 3000, "transport": 2000, "other": 1000},
    "subscriptions_monthly": 4000,
    "pause_unused_days": 30,
    "sweep_leftovers_to_savings": True,
}


class Moneyfest:
    def __init__(self, wallets, ai):
        self.wallets = wallets
        self.ai = ai
        self.rules = json.loads(json.dumps(DEFAULT_RULES))
        self.spent = {cat: 0 for cat in CATEGORIES}   # this week, in cents
        self.pending = {}                              # decisions waiting for the user
        self.activity = []                             # newest first
        self._ids = itertools.count(1)
        # Sample data: days since last use -> timestamp of last use.
        with open(SAMPLE_USAGE) as f:
            days_ago = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
        self.usage = {name: time.time() - d * 86400 for name, d in days_ago.items()}

    # ----------------------------------------------------------------- rules
    def set_rules(self, text):
        proposal = self.ai.parse_rules(text)
        clean = validate_rules(proposal)
        for key, value in clean.items():
            if key == "budgets":
                self.rules["budgets"].update(value)
            else:
                self.rules[key] = value
        self._log("rules", f"Rules updated from: “{text}”", {"parsed": clean})
        return clean

    # --------------------------------------------------------------- command
    def command(self, text):
        """One sentence from the prompt box -> a real action.

        The AI only reads the sentence. This code checks the answer, then the
        same rules as the buttons decide: budgets, subscription checks, approvals.
        """
        proposal = self.ai.parse_command(text)
        action = proposal.get("action")
        amount = proposal.get("amount")
        amount = round(float(amount) * 100) if isinstance(amount, (int, float)) and amount > 0 else None
        to = str(proposal.get("to") or "").strip()[:60]

        if action == "pay" and to and amount:
            self._log("command", f"You said: “{text}”", {"parsed": proposal})
            known = {name.lower(): name for name in self.usage}
            if to.lower() in known:  # a subscription we track -> pay from the subscriptions wallet
                return self.subscription_due(known[to.lower()], amount)
            return self.pay(to, amount)
        if action == "income" and amount:
            self._log("command", f"You said: “{text}”", {"parsed": proposal})
            return self.receive_income(amount)
        if action == "sweep":
            self._log("command", f"You said: “{text}”", {"parsed": proposal})
            return self.sweep()
        raise ValueError("I didn't understand that. Try: “pay Netflix 10” or “pay Esselunga 12.40”.")

    # ---------------------------------------------------------------- income
    def receive_income(self, amount):
        """Income lands in the spending wallet; the subscriptions budget moves to its own wallet."""
        subs = min(self.rules["subscriptions_monthly"], amount)
        transfer = None
        if subs > 0:
            transfer = self.wallets.send("spending", "subscriptions", subs)
        self._log("income", f"Income of {fmt(amount)}: {fmt(subs)} set aside for subscriptions.",
                  {"transfer": transfer})
        return {"subscriptions": subs, "transfer": transfer}

    # -------------------------------------------------------------- payments
    def pay(self, merchant, amount, approved=False):
        proposal = self.ai.classify_payment(merchant, amount)
        category = proposal.get("category")
        if category not in CATEGORIES:
            category = "other"
        limit = self.rules["budgets"].get(category, 0)
        left = limit - self.spent[category]

        if amount > left and not approved:
            return self._ask_user("payment", {
                "merchant": merchant, "amount": amount, "category": category,
                "summary": f"{merchant} ({fmt(amount)}) would go over your {category} budget: "
                           f"only {fmt(max(left, 0))} left this week.",
            })

        transfer = self.wallets.send("spending", "shop", amount)
        self.spent[category] += amount
        self._log("payment", f"Paid {fmt(amount)} to {merchant} from {category}. "
                             f"{fmt(limit - self.spent[category])} left this week.",
                  {"category": category, "ai_reason": proposal.get("reason"), "transfer": transfer})
        warning = None
        if limit and limit - self.spent[category] < limit * 0.2:
            warning = f"Your {category} envelope is almost empty."
        return {"status": "paid", "category": category, "transfer": transfer, "warning": warning}

    # --------------------------------------------------------- subscriptions
    def subscription_due(self, name, amount):
        """A subscription wants to be paid. Pay it, or pause it if unused."""
        last_used = self.usage.get(name)
        days_unused = None if last_used is None else int((time.time() - last_used) / 86400)
        limit_days = self.rules["pause_unused_days"]

        if days_unused is not None and days_unused >= limit_days:
            return self._ask_user("subscription", {
                "name": name, "amount": amount, "days_unused": days_unused,
                "summary": f"Paused {name}: you haven't used it in {days_unused} days. Keep or cancel?",
            })
        transfer = self.wallets.send("subscriptions", "shop", amount)
        self._log("subscription", f"Paid {name} ({fmt(amount)}).", {"transfer": transfer})
        return {"status": "paid", "transfer": transfer}

    # ----------------------------------------------------------------- sweep
    def sweep(self):
        """End of week: move what was not spent into savings, then start a new week."""
        if not self.rules["sweep_leftovers_to_savings"]:
            return {"status": "off"}
        leftover = sum(max(self.rules["budgets"][c] - self.spent[c], 0) for c in CATEGORIES)
        leftover = min(leftover, self.wallets.balance("spending"))
        transfer = self.wallets.send("spending", "savings", leftover) if leftover > 0 else None
        self.spent = {cat: 0 for cat in CATEGORIES}
        self._log("sweep", f"Week closed: {fmt(leftover)} moved to savings.", {"transfer": transfer})
        return {"moved": leftover, "transfer": transfer}

    # ------------------------------------------------------------- decisions
    def decide(self, decision_id, approve):
        d = self.pending.pop(decision_id)
        if d["kind"] == "payment":
            if approve:
                return self.pay(d["merchant"], d["amount"], approved=True)
            self._log("declined", f"Skipped {d['merchant']} ({fmt(d['amount'])}).", {})
            return {"status": "declined"}
        if d["kind"] == "subscription":
            if approve:  # keep: pay it anyway
                transfer = self.wallets.send("subscriptions", "shop", d["amount"])
                self.usage[d["name"]] = time.time()
                self._log("subscription", f"Kept {d['name']} and paid {fmt(d['amount'])}.",
                          {"transfer": transfer})
                return {"status": "paid", "transfer": transfer}
            self._log("cancelled", f"Cancelled {d['name']}: saved {fmt(d['amount'])} a month.", {})
            return {"status": "cancelled"}
        raise ValueError("unknown decision")

    # ----------------------------------------------------------------- state
    def state(self):
        return {
            "wallets": {name: self.wallets.balance(name) for name in ("spending", "subscriptions", "savings")},
            "envelopes": {c: {"limit": self.rules["budgets"].get(c, 0), "spent": self.spent[c]}
                          for c in CATEGORIES},
            "rules": self.rules,
            "pending": list(self.pending.values()),
            "activity": self.activity[:30],
        }

    # --------------------------------------------------------------- helpers
    def _ask_user(self, kind, info):
        decision_id = str(next(self._ids))
        info.update({"id": decision_id, "kind": kind})
        info["message"] = self.ai.explain(info)
        self.pending[decision_id] = info
        self._log("waiting", info["message"], {})
        return {"status": "needs_approval", "decision": info}

    def _log(self, kind, text, extra):
        self.activity.insert(0, {"time": time.strftime("%H:%M:%S"), "kind": kind, "text": text, **extra})


def validate_rules(proposal):
    """Keep only well-formed, sensible values from the model's answer."""
    clean = {}
    budgets = proposal.get("budgets") or {}
    good = {c: int(v) for c, v in budgets.items()
            if c in CATEGORIES and isinstance(v, (int, float)) and 0 <= v <= 1_000_000}
    if good:
        clean["budgets"] = good
    v = proposal.get("subscriptions_monthly")
    if isinstance(v, (int, float)) and 0 <= v <= 1_000_000:
        clean["subscriptions_monthly"] = int(v)
    v = proposal.get("pause_unused_days")
    if isinstance(v, (int, float)) and 1 <= v <= 365:
        clean["pause_unused_days"] = int(v)
    v = proposal.get("sweep_leftovers_to_savings")
    if isinstance(v, bool):
        clean["sweep_leftovers_to_savings"] = v
    return clean


def fmt(cents):
    return f"{cents / 100:.2f} USDT"
