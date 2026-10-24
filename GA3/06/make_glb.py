"""Build a textured 3D face relief GLB from the assigned Zapata photograph."""
import io, json, struct, sys
import numpy as np
from PIL import Image, ImageFilter

src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
X0, Y0, X1, Y1 = 200, 70, 760, 930                 # head + neck crop in the 960x1312 photo
crop = im.crop((X0, Y0, X1, Y1)); W, H = crop.size
gray = np.asarray(crop.convert("L").filter(ImageFilter.GaussianBlur(6)), dtype=np.float32) / 255.0

NX, NY = 110, 170
xs, ys = np.linspace(0, W - 1, NX), np.linspace(0, H - 1, NY)
gx, gy = np.meshgrid(xs, ys)
px, py = gx + X0, gy + Y0                            # photo pixel coords
cx, cy, rx, ry = 480, 520, 250, 390                  # head ellipse (photo coords)
u, v = (px - cx) / rx, (py - cy) / ry
r2 = u ** 2 + v ** 2
z = 0.62 * np.sqrt(np.clip(1 - 0.92 * u ** 2, 0, 1)) * np.clip(1 - 0.35 * np.clip(v, 0, None) ** 2, 0.2, 1)   # head dome
g = lambda x0, y0, sx, sy: np.exp(-(((px - x0) / sx) ** 2 + ((py - y0) / sy) ** 2) / 2)
z += 0.20 * g(503, 560, 26, 70) + 0.10 * g(505, 600, 30, 25)       # nose ridge + tip
z -= 0.07 * g(398, 493, 40, 22) + 0.07 * g(590, 493, 40, 22)       # eye sockets
z += 0.04 * g(398, 455, 60, 14) + 0.04 * g(590, 455, 60, 14)       # brow ridge
z += 0.05 * g(490, 680, 120, 30)                                    # mustache volume
z += 0.03 * g(345, 610, 45, 60) + 0.03 * g(640, 610, 45, 60)        # cheekbones
z += 0.04 * (gray[np.clip(gy.astype(int), 0, H - 1), np.clip(gx.astype(int), 0, W - 1)] - 0.5)  # fine relief
neck = (np.abs(px - 480) < 175) & (py > 780)
keep = (r2 <= 1.0) | neck
z = np.where(neck & (r2 > 1.0), 0.30, z)

S = 0.0006                                            # metres per pixel (~0.34 m wide)
pos = np.stack([(px - cx) * S, -(py - cy) * S, z * rx * S], -1).reshape(-1, 3).astype(np.float32)
uv = np.stack([gx / (W - 1), gy / (H - 1)], -1).reshape(-1, 2).astype(np.float32)
idx = []
K = keep.reshape(-1)
for j in range(NY - 1):
    for i in range(NX - 1):
        a, b, c, d = j * NX + i, j * NX + i + 1, (j + 1) * NX + i, (j + 1) * NX + i + 1
        if K[a] and K[b] and K[c] and K[d]:
            idx += [a, c, b, b, c, d]
idx = np.array(idx, dtype=np.uint32)
used = np.unique(idx); remap = np.full(len(pos), -1, np.int64); remap[used] = np.arange(len(used))
pos, uv, idx = pos[used], uv[used], remap[idx].astype(np.uint32)  # drop vertices outside the head mask
# normals
nrm = np.zeros_like(pos); tri = idx.reshape(-1, 3)
fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
for k in range(3): np.add.at(nrm, tri[:, k], fn)
nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
nrm[nrm[:, 2] < 0] *= -1
# texture
buf = io.BytesIO(); crop.resize((512, 1024)).save(buf, "JPEG", quality=85); img = buf.getvalue()

chunks, views, off = [], [], 0
def add(data, target=None):
    global off
    pad = (-len(data)) % 4; chunks.append(data + b"\0" * pad)
    v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
    if target: v["target"] = target
    views.append(v); off += len(data) + pad; return len(views) - 1
vp, vn, vt, vi, vimg = add(pos.tobytes(), 34962), add(nrm.astype(np.float32).tobytes(), 34962), add(uv.tobytes(), 34962), add(idx.tobytes(), 34963), add(img)
gltf = {"asset": {"version": "2.0", "generator": "ga3-q6-face-relief"},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "EmilianoZapataFace"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]}],
        "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.85}, "doubleSided": True}],
        "textures": [{"source": 0, "sampler": 0}], "samplers": [{"magFilter": 9729, "minFilter": 9987}],
        "images": [{"bufferView": vimg, "mimeType": "image/jpeg"}],
        "accessors": [
            {"bufferView": vp, "componentType": 5126, "count": len(pos), "type": "VEC3", "min": pos.min(0).tolist(), "max": pos.max(0).tolist()},
            {"bufferView": vn, "componentType": 5126, "count": len(pos), "type": "VEC3"},
            {"bufferView": vt, "componentType": 5126, "count": len(uv), "type": "VEC2"},
            {"bufferView": vi, "componentType": 5125, "count": len(idx), "type": "SCALAR"}],
        "bufferViews": views, "buffers": [{"byteLength": off}]}
js = json.dumps(gltf, separators=(",", ":")).encode(); js += b" " * ((-len(js)) % 4)
binb = b"".join(chunks)
glb = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binb), 0x004E4942) + binb
open(out, "wb").write(glb)
print("vertices", len(pos), "triangles", len(idx) // 3, "bytes", len(glb))
