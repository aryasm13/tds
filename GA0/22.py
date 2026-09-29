import csv, io, zipfile
from pathlib import Path

HERE = Path(__file__).parent
ZIP = max(HERE.glob("*.zip"), key=lambda p: p.stat().st_mtime)
print("using", ZIP.name)

TARGET = {"˜", "“", "‘"}
SPEC = {"data1.csv": ("cp1252", ","), "data2.csv": ("utf-8", ","), "data3.txt": ("utf-16", "\t")}

total = 0.0
with zipfile.ZipFile(ZIP) as z:
    for name in z.namelist():
        base = name.split("/")[-1]
        if base not in SPEC:
            continue
        enc, sep = SPEC[base]
        text = z.read(name).decode(enc)
        rows = list(csv.reader(io.StringIO(text), delimiter=sep))
        sub = sum(float(r[1]) for r in rows[1:] if len(r) >= 2 and r[0].strip() in TARGET)
        print(base, enc, "->", sub)
        total += sub

print("TOTAL:", total)