"""Copies of a demo document that are validly signed - but NOT by a trusted issuer.

    python3 keyproof/make_untrusted_docs.py

real_docs/2_Income_statement_SIGNED_BY_STRANGER.pdf  signed by a private person's own key ("Luca Ferri")
real_docs/2_Income_statement_FAKE_BANK_KEY.pdf       signed by a key that *calls itself* "Moneyfest Bank (test)"
Both signatures are mathematically valid ("not changed"), but neither key is on the trust list,
so KeyProof shows them in amber and never uses them for the proof.
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cryptography import x509  # noqa: E402
from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.x509.oid import NameOID  # noqa: E402

import zkcrypto as zk  # noqa: E402
from make_demo import days, layout  # noqa: E402
from pdfsig import make_signed_pdf  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
today = dt.date(2026, 10, 18)
d_iss = today - dt.timedelta(days=6)


def self_signed(org, cn):
    key = ec.generate_private_key(ec.SECP256R1())
    n = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"), x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
                   x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(n).issuer_name(n).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - dt.timedelta(days=1))
            .not_valid_after(now + dt.timedelta(days=365)).sign(key, hashes.SHA256()))
    return key, cert


def income_doc(issuer_name, signer):
    rows = [("Account holder", "Elena Rossi"), ("Codice fiscale", "RSSLNE04C52L219K"), ("IBAN", "IT60 X054 2811 1010 0000 0123 456"),
            ("Period", "May 2026 - Oct 2026 (6 months)"), ("Average monthly net income", "EUR 1,650")]
    return layout(issuer_name, "Filiale di Torino Centro - Via Garibaldi 2, 10122 Torino", "Certificazione dei redditi accreditati",
                  f"Ref. INC-2026-77341   -   Issued {d_iss.strftime('%d/%m/%Y')}", rows,
                  ["Salary credits received on the account in the period."], signer, d_iss.strftime("%d/%m/%Y 10:42 CET"),
                  accent=(0.05, 0.27, 0.38),
                  footer="TEST - this copy is signed by a key that is NOT on the KeyProof trust list (demonstration of an untrusted signer).")


def card_with_own_key():
    k = zk.new_private_key()
    holder = zk.to_field("RSSLNE04C52L219K")
    f = [2, holder, 1650, 0, days(d_iss)]
    R8x, R8y, S = zk.sign(k, zk.poseidon(f))
    return {"type": 2, "holder": str(holder), "v1": 1650, "v2": 0, "issuedAt": days(d_iss), "sig": [str(R8x), str(R8y), str(S)]}


out = os.path.join(ROOT, "real_docs")
os.makedirs(out, exist_ok=True)
for fname, org, cn, shown in [
        ("2_Income_statement_SIGNED_BY_STRANGER.pdf", "Luca Ferri", "Luca Ferri (private person)", "Moneyfest Bank (test)"),
        ("2_Income_statement_FAKE_BANK_KEY.pdf", "Moneyfest Bank (test)", "Moneyfest Bank (test) document signing", "Moneyfest Bank (test)")]:
    key, cert = self_signed(org, cn)
    pdf = make_signed_pdf([], card_with_own_key(), org, key, cert, raw=income_doc(shown, org))
    open(os.path.join(out, fname), "wb").write(pdf)
    print("written", fname)
