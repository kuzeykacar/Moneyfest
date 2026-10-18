"""Compare the local models on landlord sentences: speed and correctness.
Run on the Mac: .venv/bin/python tools/bench_ai.py   (needs the QVAC servers running)"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "keyproof"))
os.environ["KEYPROOF_AI"] = "qvac"
import ai

CASES = [  # sentence, expected (subset of fields that must match)
    ("Adult student in Turin, earns at least 1500 a month, studying until at least 2027-07-31",
     {"identity": True, "income": True, "minIncome": 1500, "occupation": True, "allowStudent": True, "leaseEnd": "2027-07-31"}),
    ("Working professional, salary 2000+, savings of 5000",
     {"income": True, "minIncome": 2000, "occupation": True, "allowEmployed": True, "savings": True, "minSavings": 5000}),
    ("Students welcome, parents as guarantor with 3000 income",
     {"occupation": True, "allowStudent": True, "guarantor": True, "minGuarantor": 3000, "income": False}),
    ("Rent is 600, tenant must earn 3 times the rent", {"income": True, "minIncome": 1800}),
    ("Anyone over 18 with a job contract until 2027-06-30",
     {"identity": True, "occupation": True, "allowEmployed": True, "leaseEnd": "2027-06-30"}),
    ("Cerco uno studente maggiorenne con un reddito di almeno 1200 euro al mese",
     {"identity": True, "income": True, "minIncome": 1200, "occupation": True, "allowStudent": True}),
    ("Kiracı 18 yaşından büyük olmalı ve en az 2500 euro birikimi olmalı",
     {"identity": True, "savings": True, "minSavings": 2500}),
    ("I need someone with a steady job, 1800 net per month, and a guarantor earning 2500",
     {"income": True, "minIncome": 1800, "occupation": True, "allowEmployed": True, "guarantor": True, "minGuarantor": 2500}),
    ("Just make sure they are an adult", {"identity": True, "income": False, "savings": False}),
    ("Student or worker is fine, needs 4000 in savings and must stay until 2028-01-31",
     {"occupation": True, "allowStudent": True, "allowEmployed": True, "savings": True, "minSavings": 4000, "leaseEnd": "2028-01-31"}),
]

def flat(r):
    d = dict(r["checks"]); d.update({k: v for k, v in r.items() if k != "checks"}); return d

all_eps = list(ai.ENDPOINTS)
for ep in all_eps:
    ai.ENDPOINTS[:] = [ep]
    ok = 0; times = []
    print(f"\n=== {ep[2]} ({ep[0]})")
    for text, exp in CASES:
        t = time.time()
        try:
            r = flat(ai._clean(ai._ask_model(text)))
        except Exception as e:
            print("  ERROR", e); break
        dt = time.time() - t; times.append(dt)
        bad = {k: (v, r.get(k)) for k, v in exp.items() if r.get(k) != v}
        ok += not bad
        print(f"  {'OK ' if not bad else 'BAD'} {dt:4.1f}s  {text[:60]}" + (f"   wrong: {bad}" if bad else ""))
    if times:
        print(f"  -> {ok}/{len(CASES)} correct, average {sum(times)/len(times):.1f}s")
