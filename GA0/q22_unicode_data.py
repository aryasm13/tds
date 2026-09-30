"""Q22 Different encodings: sum the values for your symbols across the 3 differently-encoded files in q-unicode-data.zip.

Run: uv run q22_unicode_data.py path/to/q-unicode-data.zip   (edit SYMBOLS below first)
"""
import csv, io, sys, zipfile

# ---- EDIT to match YOUR question (the symbols differ per student) ----
SYMBOLS = set()  # the symbols your question lists, e.g. {"€", "™"}
FILES = {        # file name -> (encoding, delimiter), as described in the question
    "data1.csv": ("cp1252", ","),
    "data2.csv": ("utf-8", ","),
    "data3.txt": ("utf-16", "\t"),
}
# ----------------------------------------------------------------------

if len(sys.argv) < 2 or not SYMBOLS:
    sys.exit(__doc__)
ZIP = sys.argv[1]
print("using", ZIP)

total = 0.0
with zipfile.ZipFile(ZIP) as z:
    for name in z.namelist():
        base = name.split("/")[-1]
        if base not in FILES:
            continue
        enc, sep = FILES[base]
        text = z.read(name).decode(enc)
        rows = list(csv.reader(io.StringIO(text), delimiter=sep))
        sub = sum(float(r[1]) for r in rows[1:] if len(r) >= 2 and r[0].strip() in SYMBOLS)
        print(base, enc, "->", sub)
        total += sub

print("TOTAL:", total)
