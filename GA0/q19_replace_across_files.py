"""Q19 Replace across files: unzip q-replace-across-files.zip and replace "IITM" (any case) with "IIT Madras" in all files.

Run: uv run q19_replace_across_files.py path/to/q-replace-across-files.zip   (then run the sha256sum command it prints)
"""
import re, shutil, sys, zipfile
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
ZIP = Path(sys.argv[1])
OUT = ZIP.with_name(ZIP.stem + "_replaced")   # new folder next to the zip
print("using", ZIP.name)

shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir()
zipfile.ZipFile(ZIP).extractall(OUT)

# work on bytes so line endings stay exactly as they were
for p in OUT.rglob("*"):
    if p.is_file():
        b = p.read_bytes()
        p.write_bytes(re.sub(rb"(?i)iitm", b"IIT Madras", b))

print([str(p.relative_to(OUT)) for p in OUT.rglob("*")][:10])
print(f'next, in Git Bash: cd "{OUT.resolve().as_posix()}" && cat * | sha256sum')
