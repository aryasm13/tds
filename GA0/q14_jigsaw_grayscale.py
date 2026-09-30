# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy"]
# ///
"""Q14 Reconstruct and desaturate: unscramble the 5x5 jigsaw.webp using your mapping table, save it as grayscale PNG.

Run: uv run q14_jigsaw_grayscale.py path/to/jigsaw.webp mapping.txt [out.png]
"""
import re
import sys
from pathlib import Path
from PIL import Image
import numpy as np

if len(sys.argv) < 3:
    sys.exit(__doc__)
SRC, MAP = Path(sys.argv[1]), Path(sys.argv[2])
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else SRC.with_name("gray.png")   # default: next to the input

src = Image.open(SRC).convert("RGB")
W, H = src.size
N = 5
print("source size:", W, H, "| divisible by 5?", W % N == 0, H % N == 0)
tw, th = W // N, H // N

# mapping.txt = the table from YOUR question pasted as plain text, one tile per row:
#   Scrambled Row  Scrambled Column  Original Row  Original Column
# Header lines are fine: only the numbers are read, 4 per tile.
nums = [int(x) for x in re.findall(r"\d+", MAP.read_text(encoding="utf-8-sig"))]
if len(nums) != 4 * N * N:
    sys.exit(f"expected {N * N} rows of 4 numbers in {MAP}, found {len(nums)} numbers")
M = [tuple(nums[i:i + 4]) for i in range(0, len(nums), 4)]

out = Image.new("RGB", (W, H))
for sr, sc, orr, oc in M:
    tile = src.crop((sc * tw, sr * th, (sc + 1) * tw, (sr + 1) * th))
    out.paste(tile, (oc * tw, orr * th))

a = np.asarray(out, dtype=np.float64)
lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]

# JS Math.round = round half UP. np.round = banker's rounding. Use floor(x+0.5).
g = np.floor(lum + 0.5).clip(0, 255).astype(np.uint8)

rgb = np.dstack([g, g, g])                      # 3 identical channels, like the canvas
Image.fromarray(rgb, mode="RGB").save(OUT, format="PNG")
print("saved", OUT)
