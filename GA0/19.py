import re, shutil, zipfile
from pathlib import Path

HERE = Path(__file__).parent
ZIP = max(HERE.glob("*.zip"), key=lambda p: p.stat().st_mtime)   # newest zip
OUT = HERE / "q19"
print("using", ZIP.name)

shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir()
zipfile.ZipFile(ZIP).extractall(OUT)

for p in OUT.rglob("*"):
    if p.is_file():
        b = p.read_bytes()
        p.write_bytes(re.sub(rb"(?i)iitm", b"IIT Madras", b))

print([str(p.relative_to(OUT)) for p in OUT.rglob("*")][:10])