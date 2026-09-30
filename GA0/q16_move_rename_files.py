"""Q16 Move and rename files: flatten q-move-rename-files.zip into one folder, then shift each digit in names (1->2, 9->0).

Run: uv run q16_move_rename_files.py path/to/q-move-rename-files.zip   (then run the sha256sum command it prints)
"""
import re, shutil, sys, zipfile
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
ZIP = Path(sys.argv[1])
EXTRACT = ZIP.with_name(ZIP.stem + "_extracted")   # work folders next to the zip
FLAT = ZIP.with_name(ZIP.stem + "_flat")

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
print(f'next, in Git Bash: cd "{FLAT.resolve().as_posix()}" && grep . * | LC_ALL=C sort | sha256sum')
