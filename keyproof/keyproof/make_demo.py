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


def _e(t):
    return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def layout(issuer, office, title, ref, rows, note, signer, when, accent=(0.11, 0.27, 0.55)):
    """Official-looking one-page certificate: letterhead, title, reference, field table, signature panel."""
    r, g, b = accent
    o = []
    txt = lambda f, sz, x, y, t, c=(0.1, 0.12, 0.16): o.append(
        f"BT {c[0]} {c[1]} {c[2]} rg /{f} {sz} Tf 1 0 0 1 {x} {y} Tm ({_e(t)}) Tj ET")
    # letterhead band
    o.append(f"{r} {g} {b} rg 0 772 595 70 re f")
    txt("F2", 17, 48, 808, issuer, (1, 1, 1))
    txt("F1", 10, 48, 790, office, (0.85, 0.9, 1))
    # title + reference
    txt("F2", 15, 48, 735, title)
    txt("F1", 9.5, 48, 717, ref, (0.35, 0.38, 0.45))
    o.append("0.8 0.82 0.86 RG 0.8 w 48 704 m 547 704 l S")
    y = 678
    for label, value in rows:
        txt("F1", 9, 48, y, label.upper(), (0.4, 0.43, 0.5))
        txt("F2", 11.5, 232, y, value)
        o.append(f"0.9 0.91 0.93 RG 0.5 w 48 {y - 9} m 547 {y - 9} l S")
        y -= 30
    y -= 6
    for line in note:
        txt("F1", 9.5, 48, y, line, (0.3, 0.33, 0.4))
        y -= 14
    # signature panel
    o.append(f"0.96 0.97 0.99 rg {r} {g} {b} RG 1 w 300 120 247 92 re B")
    txt("F2", 10, 314, 192, "Digitally signed PDF (CMS signature)", (r, g, b))
    txt("F1", 9, 314, 176, "Signer: " + signer)
    txt("F1", 9, 314, 162, "Date: " + when)
    txt("F1", 9, 314, 148, "Algorithm: ECDSA P-256, SHA-256")
    txt("F1", 8, 314, 132, "Any change to this file breaks the signature.", (0.4, 0.43, 0.5))
    txt("F1", 8, 48, 132, "Signed electronically. Valid without a handwritten signature.", (0.4, 0.43, 0.5))
    # footer
    o.append("0.8 0.82 0.86 RG 0.5 w 48 70 m 547 70 l S")
    txt("F1", 7.5, 48, 56, "TEST ISSUER - fictional person and organisation, created for the KeyProof prototype. Not a real public document.",
        (0.55, 0.3, 0.3))
    txt("F1", 7.5, 48, 44, "Verify: open in any PDF reader > Signature panel, or upload to KeyProof.", (0.45, 0.48, 0.55))
    return "\n".join(o)


def load_existing():
    """Reuse the existing trust root and issuer keys (so certificates and wallets stay valid)."""
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    root_cert = x509.load_pem_x509_certificate(open(os.path.join(ROOT, "trust", "root.pem"), "rb").read())
    issuers = {}
    for k in ("comune", "bank", "poli", "employer"):
        kd = os.path.join(ROOT, "data", "issuer_keys")
        cert = x509.load_pem_x509_certificate(open(os.path.join(ROOT, "trust", "issuers", k + ".pem"), "rb").read())
        issuers[k] = {"org": cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value,
                      "key": load_pem_private_key(open(os.path.join(kd, k + ".pem"), "rb").read(), None),
                      "cert": cert, "zk_key": int(open(os.path.join(kd, k + ".zk")).read())}
    return root_cert, issuers


def main():
    today = dt.date(2026, 10, 18)
    if "--render" in sys.argv:
        root_cert, issuers = load_existing()
        return write_docs(today, root_cert, issuers)
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
    write_docs(today, root_cert, issuers)


DOC_FILES = {1: "Certificato_anagrafico_Elena_Rossi.pdf", 2: "Income_statement_Elena_Rossi.pdf",
             3: "Certificato_iscrizione_Elena_Rossi.pdf", 4: "Balance_certificate_Elena_Rossi.pdf",
             5: "Guarantor_income_Marco_Rossi.pdf"}
FAKE_FILE = "Income_statement_Elena_Rossi_EDITED.pdf"


def write_docs(today, root_cert, issuers):
    # Fictional tenant and guarantor.
    tenant_name, tenant_cf = "Elena Rossi", "RSSLNE04C52L219K"
    guarantor_name = "Marco Rossi"
    holder = zk.to_field(tenant_cf)
    birth = dt.date(2004, 3, 12)
    issued = days(today - dt.timedelta(days=6))

    d6 = (today - dt.timedelta(days=6)).strftime("%d/%m/%Y")
    signed = (today - dt.timedelta(days=6)).strftime("%d/%m/%Y 10:42 CET")
    note_priv = ["This certificate is issued at the request of the holder for private use (rental application)."]
    docs = {
        DOC_FILES[1]: ("comune", make_card(issuers["comune"], 1, holder, days(birth), 0, issued), layout(
            issuers["comune"]["org"], "Servizi Demografici - Ufficio Anagrafe", "Certificato anagrafico di nascita e residenza",
            f"Prot. n. 2026/ANA/0148213   -   Issued {d6}",
            [("Cognome e nome", tenant_name), ("Codice fiscale", tenant_cf),
             ("Data di nascita", birth.strftime("%d/%m/%Y")), ("Luogo di nascita", "Torino (TO)"),
             ("Residenza", "Via Roma 10, 10121 Torino (TO)"), ("Cittadinanza", "Italiana")],
            ["Si rilascia in carta libera per gli usi consentiti dalla legge."] , "Ufficiale d'Anagrafe", signed)),
        DOC_FILES[2]: ("bank", make_card(issuers["bank"], 2, holder, 1650, 0, issued), layout(
            issuers["bank"]["org"], "Filiale di Torino Centro - ABI 99999", "Income statement",
            f"Ref. INC-2026-77341   -   Issued {d6}",
            [("Account holder", tenant_name), ("Codice fiscale", tenant_cf), ("IBAN", "IT60 X999 9901 0000 0000 0123 456"),
             ("Period", "Apr 2026 - Sep 2026 (6 months)"),
             ("Average monthly net income", "EUR 1,650"), ("Sources", "Part-time salary, scholarship")],
            note_priv, issuers["bank"]["org"] + " - Ufficio Certificazioni", signed)),
        DOC_FILES[3]: ("poli", make_card(issuers["poli"], 3, holder, 1, days(dt.date(2027, 9, 30)), issued), layout(
            issuers["poli"]["org"], "Area Gestione Didattica - Segreteria Studenti", "Certificate of enrolment",
            f"Prot. n. 52190/2026   -   Issued {d6}",
            [("Student", tenant_name), ("Codice fiscale", tenant_cf), ("Student ID", "s314159"),
             ("Programme", "BSc Computer Engineering"), ("Year", "2nd year, full time"),
             ("Academic year", "2026/2027, valid until 30/09/2027")],
            note_priv, "Segreteria Studenti", signed, accent=(0.05, 0.33, 0.45))),
        DOC_FILES[4]: ("bank", make_card(issuers["bank"], 4, holder, 4800, 0, issued), layout(
            issuers["bank"]["org"], "Filiale di Torino Centro - ABI 99999", "Balance certificate",
            f"Ref. BAL-2026-55102   -   Issued {d6}",
            [("Account holder", tenant_name), ("Codice fiscale", tenant_cf), ("IBAN", "IT60 X999 9901 0000 0000 0123 456"),
             ("Balance date", d6), ("Available balance", "EUR 4,800")],
            note_priv, issuers["bank"]["org"] + " - Ufficio Certificazioni", signed)),
        DOC_FILES[5]: ("bank", make_card(issuers["bank"], 5, holder, 3900, 0, issued), layout(
            issuers["bank"]["org"], "Filiale di Torino Centro - ABI 99999", "Guarantor income statement",
            f"Ref. GUA-2026-10877   -   Issued {d6}",
            [("Guarantor", guarantor_name), ("Guarantees the rent of", f"{tenant_name} ({tenant_cf})"),
             ("Period", "Apr 2026 - Sep 2026 (6 months)"), ("Average monthly net income", "EUR 3,900")],
            note_priv, issuers["bank"]["org"] + " - Ufficio Certificazioni", signed)),
    }
    out_dir = os.path.join(ROOT, "demo_docs")
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".pdf"):
            os.remove(os.path.join(out_dir, f))
    for fname, (iss_key, card, raw) in docs.items():
        iss = issuers[iss_key]
        pdf = make_signed_pdf([], card, iss["org"], iss["key"], iss["cert"], raw=raw)
        with open(os.path.join(out_dir, fname), "wb") as f:
            f.write(pdf)

    # The fake: same income statement with one number edited (1,650 -> 2,650).
    with open(os.path.join(out_dir, DOC_FILES[2]), "rb") as f:
        real = f.read()
    fake = real.replace(b"EUR 1,650", b"EUR 2,650")
    assert fake != real and len(fake) == len(real)
    with open(os.path.join(out_dir, FAKE_FILE), "wb") as f:
        f.write(fake)

    # Filler for checks the landlord did not tick: a card signed by a throwaway key.
    filler_key = zk.new_private_key()
    fx, fy = zk.public_key(filler_key)
    filler = {"fields": [0, 0, 0, 0, 0], "issuerKey": [str(fx), str(fy)],
              "sig": [str(v) for v in zk.sign(filler_key, zk.poseidon([0, 0, 0, 0, 0]))]}
    with open(os.path.join(ROOT, "web", "zk", "dummy_card.json"), "w") as f:
        json.dump(filler, f)

    # Self-check.
    for fname in list(docs) + [FAKE_FILE]:
        with open(os.path.join(out_dir, fname), "rb") as f:
            r = verify_pdf(f.read(), root_cert)
        print(f"{fname:26} {'OK  ' if r['ok'] else 'FAIL'} " +
              "; ".join(f"{c['check']}: {c['detail']}" for c in r["checks"]))
    print("demo issuers and documents written")


if __name__ == "__main__":
    main()
