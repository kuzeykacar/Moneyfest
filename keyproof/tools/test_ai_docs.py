"""Run the local AI document reader on every PDF in demo_docs (and any extra PDFs given). Writes data/ai-docs.txt via the .command."""
import glob, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "keyproof"))
os.environ.setdefault("KEYPROOF_AI", "qvac")
import ai, pdftext  # noqa: E402
ai.USE_FAKE = False
files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "demo_docs", "*.pdf"))) + sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "data", "real_docs", "*.pdf"))) + sys.argv[1:]
for f in files:
    t0 = time.time()
    text = pdftext.extract_text(open(f, "rb").read())
    r = ai.read_document(text)
    print(f"{os.path.basename(f)[:40]:40} {time.time()-t0:5.1f}s {r}", flush=True)
