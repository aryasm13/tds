import re, shutil, zipfile
from pathlib import Path

HERE = Path(__file__).parent
ZIP = next(HERE.glob("*.zip"))
EXTRACT = HERE / "extracted"
FLAT = HERE / "flat"

for d in (EXTRACT, FLAT):
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()

with zipfile.ZipFile(ZIP) as z:
    z.extractall(EXTRACT)

# move every file (at any depth) into one flat folder
n = 0
for p in EXTRACT.rglob("*"):
    if p.is_file():
        target = FLAT / p.name
        if target.exists():
            print("COLLISION:", p.name)
        shutil.move(str(p), str(target))
        n += 1
print("moved", n, "files")

# rename: each digit becomes the next one, 9 -> 0
bump = lambda m: str((int(m.group()) + 1) % 10)
for p in sorted(FLAT.iterdir()):
    new = re.sub(r"\d", bump, p.name)
    if new != p.name:
        p.rename(FLAT / new)
print("renamed. sample:", sorted(x.name for x in FLAT.iterdir())[:5])