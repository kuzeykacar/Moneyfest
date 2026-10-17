"""Create the demo trust authority, demo issuers, and the tenant's signed demo documents.

    python3 keyproof/make_demo.py

Writes:
  trust/root.pem              the trusted authority's certificate (public, the landlord trusts this)
  trust/issuers/*.pem         issuer certificates (public; each holds the issuer's ZK card key)
  demo_docs/*.pdf             signed documents for the demo tenant, plus one edited (fake) copy
  web/zk/dummy_card.json      a filler card for checks the landlord did not tick
  data/issuer_keys/           demo private keys (git-ignored, never committed)

ALL OF THIS IS DEMO DATA: fictional people, fictional issuers, test keys.
"""

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from cryptography import x509  # noqa: E402
from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.x509.oid import NameOID  # noqa: E402

import zkcrypto as zk  # noqa: E402
from pdfsig import KEYPROOF_OID, make_signed_pdf, read_card, verify_pdf  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EPOCH = dt.date(1970, 1, 1)


def days(d):
    return (d - EPOCH).days


def name(org, cn):
    return x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
                      x509.NameAttribute(NameOID.COMMON_NAME, cn)])


def save_key(key, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                  serialization.NoEncryption()))
    os.chmod(path, 0o600)


def save_cert(cert, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def make_root():
    key = ec.generate_private_key(ec.SECP256R1())
    subject = name("KeyProof Demo Trust Authority", "KeyProof Demo Root CA")
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(days=1)).not_valid_after(now + dt.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .sign(key, hashes.SHA256()))
    return key, cert


def make_issuer(root_key, root_cert, org, role, doc_types):
    key = ec.generate_private_key(ec.SECP256R1())
    zk_key = zk.new_private_key()
    Ax, Ay = zk.public_key(zk_key)
    meta = {"role": role, "docTypes": doc_types, "zk": [str(Ax), str(Ay)]}
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name(org, org + " document signing"))
            .issuer_name(root_cert.subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(days=1)).not_valid_after(now + dt.timedelta(days=730))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.UnrecognizedExtension(KEYPROOF_OID, json.dumps(meta).encode()), critical=False)
            .sign(root_key, hashes.SHA256()))
    return {"org": org, "key": key, "cert": cert, "zk_key": zk_key, "meta": meta}


def make_card(issuer, doc_type, holder, v1, v2, issued_at):
    fields = [doc_type, holder, v1, v2, issued_at]
    R8x, R8y, S = zk.sign(issuer["zk_key"], zk.poseidon(fields))
    return {"type": doc_type, "holder": str(holder), "v1": v1, "v2": v2, "issuedAt": issued_at,
            "sig": [str(R8x), str(R8y), str(S)]}


def main():
    today = dt.date(2026, 10, 18)
    root_key, root_cert = make_root()
    save_cert(root_cert, os.path.join(ROOT, "trust", "root.pem"))
    with open(os.path.join(ROOT, "trust", "revoked.json"), "w") as f:
        json.dump([], f)

    issuers = {
        "comune": make_issuer(root_key, root_cert, "Demo Comune di Torino", "identity office", [1]),
        "bank": make_issuer(root_key, root_cert, "Banca Demo", "bank", [2, 4, 5]),
        "poli": make_issuer(root_key, root_cert, "Demo Politecnico di Torino", "university", [3]),
        "employer": make_issuer(root_key, root_cert, "Demo Employer SpA", "employer", [3]),
    }
    for k, iss in issuers.items():
        save_key(iss["key"], os.path.join(ROOT, "data", "issuer_keys", k + ".pem"))
        with open(os.path.join(ROOT, "data", "issuer_keys", k + ".zk"), "w") as f:
            f.write(str(iss["zk_key"]))
        os.chmod(os.path.join(ROOT, "data", "issuer_keys", k + ".zk"), 0o600)
        save_cert(iss["cert"], os.path.join(ROOT, "trust", "issuers", k + ".pem"))

    # Fictional tenant and guarantor.
    tenant_name, tenant_cf = "Elena Rossi", "RSSLNE04C52L219K"
    guarantor_name = "Marco Rossi"
    holder = zk.to_field(tenant_cf)
    birth = dt.date(2004, 3, 12)
    issued = days(today - dt.timedelta(days=6))

    docs = {
        "1_identity.pdf": ("comune", make_card(issuers["comune"], 1, holder, days(birth), 0, issued), [
            ("F2", 18, "Demo Comune di Torino - Certificato anagrafico"),
            ("F1", 11, "DEMO DOCUMENT - fictional person, test signature"),
            ("F1", 12, f"Name: {tenant_name}"),
            ("F1", 12, f"Codice fiscale: {tenant_cf}"),
            ("F1", 12, f"Date of birth: {birth.strftime('%d/%m/%Y')}"),
            ("F1", 12, "Residence: Via Roma 10, Torino"),
            ("F1", 12, f"Issued: {(today - dt.timedelta(days=6)).strftime('%d/%m/%Y')}"),
        ]),
        "2_income.pdf": ("bank", make_card(issuers["bank"], 2, holder, 1650, 0, issued), [
            ("F2", 18, "Banca Demo - Income statement"),
            ("F1", 11, "DEMO DOCUMENT - fictional person, test signature"),
            ("F1", 12, f"Account holder: {tenant_name} ({tenant_cf})"),
            ("F1", 12, "Average monthly net income (last 6 months): EUR 1,650"),
            ("F1", 12, "Sources: part-time salary, scholarship"),
            ("F1", 12, f"Issued: {(today - dt.timedelta(days=6)).strftime('%d/%m/%Y')}"),
        ]),
        "3_enrolment.pdf": ("poli", make_card(issuers["poli"], 3, holder, 1, days(dt.date(2027, 9, 30)), issued), [
            ("F2", 18, "Demo Politecnico di Torino - Certificate of enrolment"),
            ("F1", 11, "DEMO DOCUMENT - fictional person, test signature"),
            ("F1", 12, f"Student: {tenant_name} ({tenant_cf})"),
            ("F1", 12, "Programme: BSc Computer Engineering, year 2"),
            ("F1", 12, "Enrolled for academic year 2026/2027, valid until 30/09/2027"),
            ("F1", 12, f"Issued: {(today - dt.timedelta(days=6)).strftime('%d/%m/%Y')}"),
        ]),
        "4_savings.pdf": ("bank", make_card(issuers["bank"], 4, holder, 4800, 0, issued), [
            ("F2", 18, "Banca Demo - Balance certificate"),
            ("F1", 11, "DEMO DOCUMENT - fictional person, test signature"),
            ("F1", 12, f"Account holder: {tenant_name} ({tenant_cf})"),
            ("F1", 12, "Available balance: EUR 4,800"),
            ("F1", 12, f"Issued: {(today - dt.timedelta(days=6)).strftime('%d/%m/%Y')}"),
        ]),
        "5_guarantor.pdf": ("bank", make_card(issuers["bank"], 5, holder, 3900, 0, issued), [
            ("F2", 18, "Banca Demo - Guarantor income statement"),
            ("F1", 11, "DEMO DOCUMENT - fictional people, test signature"),
            ("F1", 12, f"Guarantor: {guarantor_name}"),
            ("F1", 12, f"Guarantees the rent of: {tenant_name} ({tenant_cf})"),
            ("F1", 12, "Guarantor's average monthly net income: EUR 3,900"),
            ("F1", 12, f"Issued: {(today - dt.timedelta(days=6)).strftime('%d/%m/%Y')}"),
        ]),
    }
    out_dir = os.path.join(ROOT, "demo_docs")
    os.makedirs(out_dir, exist_ok=True)
    for fname, (iss_key, card, lines) in docs.items():
        iss = issuers[iss_key]
        pdf = make_signed_pdf(lines, card, iss["org"], iss["key"], iss["cert"])
        with open(os.path.join(out_dir, fname), "wb") as f:
            f.write(pdf)

    # The fake: same income statement with one number edited (1,650 -> 2,650).
    with open(os.path.join(out_dir, "2_income.pdf"), "rb") as f:
        real = f.read()
    fake = real.replace(b"EUR 1,650", b"EUR 2,650")
    assert fake != real and len(fake) == len(real)
    with open(os.path.join(out_dir, "FAKE_income_edited.pdf"), "wb") as f:
        f.write(fake)

    # Filler for checks the landlord did not tick: a card signed by a throwaway key.
    filler_key = zk.new_private_key()
    fx, fy = zk.public_key(filler_key)
    filler = {"fields": [0, 0, 0, 0, 0], "issuerKey": [str(fx), str(fy)],
              "sig": [str(v) for v in zk.sign(filler_key, zk.poseidon([0, 0, 0, 0, 0]))]}
    with open(os.path.join(ROOT, "web", "zk", "dummy_card.json"), "w") as f:
        json.dump(filler, f)

    # Self-check.
    for fname in list(docs) + ["FAKE_income_edited.pdf"]:
        with open(os.path.join(out_dir, fname), "rb") as f:
            r = verify_pdf(f.read(), root_cert)
        print(f"{fname:26} {'OK  ' if r['ok'] else 'FAIL'} " +
              "; ".join(f"{c['check']}: {c['detail']}" for c in r["checks"]))
    print("demo issuers and documents written")


if __name__ == "__main__":
    main()
