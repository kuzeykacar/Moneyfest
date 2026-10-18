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
    subject = name("Moneyfest Trust Authority (test)", "Moneyfest Root CA (test)")
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


def layout(issuer, office, title, ref, rows, note, signer, when, accent=(0.11, 0.27, 0.55), footer=None, algo="ECDSA P-256, SHA-256", table=None):
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
    if table:
        head, body = table
        y -= 6
        o.append(f"{r} {g} {b} rg 48 {y - 5} 499 18 re f")
        xs = [56, 140, 470]
        for x, h in zip(xs, head):
            txt("F2", 9, x, y, h, (1, 1, 1))
        y -= 20
        for i, rowv in enumerate(body):
            if i % 2:
                o.append(f"0.96 0.97 0.98 rg 48 {y - 5} 499 16 re f")
            for x, v in zip(xs, rowv):
                txt("F1", 9, x, y, v)
            y -= 16
    # signature panel
    o.append(f"0.96 0.97 0.99 rg {r} {g} {b} RG 1 w 300 120 247 92 re B")
    txt("F2", 10, 314, 192, "Digitally signed PDF (CMS signature)", (r, g, b))
    txt("F1", 9, 314, 176, "Signer: " + signer)
    txt("F1", 9, 314, 162, "Date: " + when)
    txt("F1", 9, 314, 148, "Algorithm: " + algo)
    txt("F1", 8, 314, 132, "Any change to this file breaks the signature.", (0.4, 0.43, 0.5))
    txt("F1", 8, 48, 132, "Signed electronically. Valid without a handwritten signature.", (0.4, 0.43, 0.5))
    # footer
    o.append("0.8 0.82 0.86 RG 0.5 w 48 70 m 547 70 l S")
    txt("F1", 7.5, 48, 56, footer or "TEST ISSUER - fictional person and organisation, created for the KeyProof prototype. Not a real public document.",
        (0.55, 0.3, 0.3) if not footer else (0.35, 0.38, 0.45))
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
    save_key(root_key, os.path.join(ROOT, "data", "issuer_keys", "root.pem"))
    with open(os.path.join(ROOT, "trust", "revoked.json"), "w") as f:
        json.dump([], f)

    issuers = {
        "comune": make_issuer(root_key, root_cert, "Moneyfest Anagrafe (test)", "identity office", [1]),
        "bank": make_issuer(root_key, root_cert, "Moneyfest Bank (test)", "bank", [2, 4, 5]),
        "poli": make_issuer(root_key, root_cert, "Moneyfest University (test)", "university", [3]),
        "employer": make_issuer(root_key, root_cert, "Moneyfest Employer (test)", "employer", [3]),
    }
    for k, iss in issuers.items():
        save_key(iss["key"], os.path.join(ROOT, "data", "issuer_keys", k + ".pem"))
        with open(os.path.join(ROOT, "data", "issuer_keys", k + ".zk"), "w") as f:
            f.write(str(iss["zk_key"]))
        os.chmod(os.path.join(ROOT, "data", "issuer_keys", k + ".zk"), 0o600)
        save_cert(iss["cert"], os.path.join(ROOT, "trust", "issuers", k + ".pem"))
    write_docs(today, root_cert, issuers)


DOC_FILES = {1: "1_Identity_codice_fiscale_Elena_Rossi.pdf", 2: "2_Income_statement_Elena_Rossi.pdf",
             3: "3_Enrolment_certificate_Elena_Rossi.pdf", 4: "4_Balance_certificate_Elena_Rossi.pdf",
             5: "5_Guarantor_income_Marco_Rossi.pdf", 6: "3b_Employment_certificate_Elena_Rossi.pdf"}
FAKE_FILE = "2_Income_statement_Elena_Rossi_EDITED.pdf"


def write_docs(today, root_cert, issuers):
    # Fictional tenant (a woman, so the codice fiscale day of birth is +40) and her guarantor.
    tenant_name, tenant_cf = "Elena Rossi", "RSSLNE04C52L219K"
    guarantor_name, guarantor_cf = "Marco Rossi", "RSSMRC70A01L219X"
    holder = zk.to_field(tenant_cf)
    birth = dt.date(2004, 3, 12)
    d_iss = today - dt.timedelta(days=6)
    issued = days(d_iss)
    d6 = d_iss.strftime("%d/%m/%Y")
    signed = d_iss.strftime("%d/%m/%Y 10:42 CET")
    foot = ("TEST ISSUER - issued and digitally signed by Moneyfest for the KeyProof prototype; the person is fictional. "
            "Not a real public or bank document.")
    iban = "IT60 X054 2811 1010 0000 0123 456"
    mf = lambda k: issuers[k]["org"]
    accent = {"comune": (0.13, 0.23, 0.45), "bank": (0.05, 0.27, 0.38), "poli": (0.20, 0.17, 0.42), "employer": (0.16, 0.30, 0.22)}

    def doc(key, title, office, ref, rows, note, table=None):
        return layout(mf(key), office, title, ref, rows, note, mf(key) + " - firma digitale", signed,
                      accent=accent[key], footer=foot, table=table)

    salary = [("02/05/2026", "Accredito stipendio - Moneyfest Employer", "1.640,00"),
              ("02/06/2026", "Accredito stipendio - Moneyfest Employer", "1.655,00"),
              ("02/07/2026", "Accredito stipendio - Moneyfest Employer", "1.650,00"),
              ("03/08/2026", "Accredito stipendio - Moneyfest Employer", "1.650,00"),
              ("02/09/2026", "Accredito stipendio - Moneyfest Employer", "1.648,00"),
              ("02/10/2026", "Accredito stipendio - Moneyfest Employer", "1.657,00")]
    docs = {
        DOC_FILES[1]: ("comune", make_card(issuers["comune"], 1, holder, days(birth), 2, issued), doc(
            "comune", "Certificato anagrafico e codice fiscale", "Servizi Demografici - Ufficio Anagrafe, Torino",
            f"Prot. n. 2026/ANA/0148213   -   Rilasciato il {d6}",
            [("Cognome e nome", tenant_name), ("Codice fiscale", tenant_cf), ("Sesso", "F"),
             ("Data di nascita", birth.strftime("%d/%m/%Y")), ("Luogo di nascita", "Torino (TO)"),
             ("Residenza", "Via Roma 10, 10121 Torino (TO)"), ("Cittadinanza", "Italiana")],
            ["Il codice fiscale e il sesso risultano dall'Anagrafe. Certificato rilasciato per uso privato."])),
        DOC_FILES[2]: ("bank", make_card(issuers["bank"], 2, holder, 1650, 0, issued), doc(
            "bank", "Certificazione dei redditi accreditati", "Filiale di Torino Centro - Via Garibaldi 2, 10122 Torino",
            f"Ref. INC-2026-77341   -   Issued {d6}",
            [("Account holder", tenant_name), ("Codice fiscale", tenant_cf), ("IBAN", iban),
             ("Period", "May 2026 - Oct 2026 (6 months)"), ("Average monthly net income", "EUR 1,650")],
            ["Salary credits received on the account in the period:"],
            table=(("Date", "Description", "EUR"), salary))),
        DOC_FILES[3]: ("poli", make_card(issuers["poli"], 3, holder, 1, days(dt.date(2027, 9, 30)), issued), doc(
            "poli", "Certificato di iscrizione / Certificate of enrolment", "Segreteria Studenti - Corso Duca degli Abruzzi 24, Torino",
            f"Prot. n. 52190/2026   -   Issued {d6}",
            [("Student", tenant_name), ("Codice fiscale", tenant_cf), ("Student ID", "s314159"),
             ("Programme", "BSc Computer Engineering (L-8)"), ("Year", "2nd year, full time"),
             ("Academic year", "2026/2027, valid until 30/09/2027")],
            ["The student is regularly enrolled for the academic year shown above."])),
        DOC_FILES[6]: ("employer", make_card(issuers["employer"], 3, holder, 2, days(dt.date(2028, 6, 30)), issued), doc(
            "employer", "Attestazione di servizio / Employment certificate", "Ufficio Risorse Umane - Via Nizza 150, Torino",
            f"Ref. HR-2026-0412   -   Issued {d6}",
            [("Employee", tenant_name), ("Codice fiscale", tenant_cf), ("Role", "Junior software developer (part time)"),
             ("Contract", "Fixed term, from 01/03/2026"), ("Contract end", "30/06/2028"), ("Gross monthly salary", "EUR 2,050")],
            ["We certify that the person above is employed by us under the contract described."])),
        DOC_FILES[4]: ("bank", make_card(issuers["bank"], 4, holder, 4800, 0, issued), doc(
            "bank", "Attestazione di saldo / Balance certificate", "Filiale di Torino Centro - Via Garibaldi 2, 10122 Torino",
            f"Ref. BAL-2026-55102   -   Issued {d6}",
            [("Account holder", tenant_name), ("Codice fiscale", tenant_cf), ("IBAN", iban),
             ("Balance date", d6), ("Available balance", "EUR 4,800"), ("Average balance 2026", "EUR 4,215")],
            ["Balance certified at the request of the account holder (rental application)."])),
        DOC_FILES[5]: ("bank", make_card(issuers["bank"], 5, holder, 3900, 0, issued), doc(
            "bank", "Dichiarazione del garante / Guarantor income statement", "Filiale di Torino Centro - Via Garibaldi 2, 10122 Torino",
            f"Ref. GUA-2026-10877   -   Issued {d6}",
            [("Guarantor", guarantor_name), ("Guarantor codice fiscale", guarantor_cf),
             ("Guarantees the rent of", f"{tenant_name} ({tenant_cf})"),
             ("Period", "May 2026 - Oct 2026 (6 months)"), ("Average monthly net income", "EUR 3,900")],
            ["The guarantor's salary credits were verified on the account held at this bank."])),
    }
    out_dir = os.path.join(ROOT, "demo_docs")
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".pdf"):
            os.remove(os.path.join(out_dir, f))
    pdfs = {}
    for fname, (iss_key, card, raw) in docs.items():
        iss = issuers[iss_key]
        pdfs[fname] = make_signed_pdf([], card, iss["org"], iss["key"], iss["cert"], raw=raw)
        with open(os.path.join(out_dir, fname), "wb") as f:
            f.write(pdfs[fname])

    # Edited copies: one visible detail changed after signing (same length), so the signature breaks.
    edits = {1: [(b"(F)", b"(M)")], 2: [(b"EUR 1,650", b"EUR 2,650")], 3: [(b"until 30/09/2027", b"until 30/09/2029")],
             6: [(b"30/06/2028", b"30/06/2030")], 4: [(b"EUR 4,800", b"EUR 9,800")], 5: [(b"EUR 3,900", b"EUR 8,900")]}
    fakes = []
    for k, pairs in edits.items():
        data = pdfs[DOC_FILES[k]]
        fake = data
        for a, b in pairs:
            fake = fake.replace(a, b, 1)
        assert fake != data and len(fake) == len(data), DOC_FILES[k]
        name = DOC_FILES[k].replace(".pdf", "_EDITED.pdf")
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(fake)
        fakes.append(name)

    # Filler for checks the landlord did not tick: a card signed by a throwaway key.
    filler_key = zk.new_private_key()
    fx, fy = zk.public_key(filler_key)
    filler = {"fields": [0, 0, 0, 0, 0], "issuerKey": [str(fx), str(fy)],
              "sig": [str(v) for v in zk.sign(filler_key, zk.poseidon([0, 0, 0, 0, 0]))]}
    with open(os.path.join(ROOT, "web", "zk", "dummy_card.json"), "w") as f:
        json.dump(filler, f)

    for fname in list(docs) + fakes:
        with open(os.path.join(out_dir, fname), "rb") as f:
            r = verify_pdf(f.read(), root_cert)
        print(f"{fname:52} {'OK  ' if r['ok'] else 'FAIL'} " + "; ".join(f"{c['check']}: {c['detail']}" for c in r["checks"]))
    print("demo issuers and documents written")

if __name__ == "__main__":
    main()
