# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy"]
# ///
from pathlib import Path
from PIL import Image
import numpy as np

HERE = Path(__file__).parent
src = Image.open(HERE / "jigsaw.webp").convert("RGB")
W, H = src.size
N = 5
print("source size:", W, H, "| divisible by 5?", W % N == 0, H % N == 0)
tw, th = W // N, H // N

M = [
(0,0,2,1),(0,1,1,1),(0,2,4,1),(0,3,0,3),(0,4,0,1),
(1,0,1,4),(1,1,2,0),(1,2,2,4),(1,3,4,2),(1,4,2,2),
(2,0,0,0),(2,1,3,2),(2,2,4,3),(2,3,3,0),(2,4,3,4),
(3,0,1,0),(3,1,2,3),(3,2,3,3),(3,3,4,4),(3,4,0,2),
(4,0,3,1),(4,1,1,2),(4,2,1,3),(4,3,0,4),(4,4,4,0),
]

out = Image.new("RGB", (W, H))
for sr, sc, orr, oc in M:
    tile = src.crop((sc * tw, sr * th, (sc + 1) * tw, (sr + 1) * th))
    out.paste(tile, (oc * tw, orr * th))

a = np.asarray(out, dtype=np.float64)
lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]

# JS Math.round = round half UP. np.round = banker's rounding. Use floor(x+0.5).
g = np.floor(lum + 0.5).clip(0, 255).astype(np.uint8)

rgb = np.dstack([g, g, g])                      # 3 identical channels, like the canvas
Image.fromarray(rgb, mode="RGB").save(HERE / "gray.png", format="PNG")
print("saved gray.png")