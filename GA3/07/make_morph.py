"""GA3 Q7: landmark-based face morph (Delaunay warp + cross-dissolve) from photo A to photo B."""
import subprocess, sys, os
import numpy as np, cv2
from scipy.spatial import Delaunay

A_PATH, B_PATH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
# Hand-placed landmarks (pixel coords in the 960px-wide downloads), same order for both faces:
# eyeL, eyeR, browL, browR, noseTip, mouthL, mouthR, mouthC, chin, jawL, jawR, lowJawL, lowJawR, templeL, templeR, hairline
PA = np.float32([[415,490],[580,483],[405,440],[590,435],[505,585],[440,655],[575,650],[508,660],[510,775],
                 [350,640],[680,640],[395,730],[630,725],[345,470],[685,470],[510,300]])
PB = np.float32([[398,493],[590,493],[395,448],[595,445],[505,610],[430,700],[590,700],[505,705],[505,810],
                 [295,640],[700,640],[360,760],[650,760],[265,460],[700,450],[500,180]])
W, H = 320, 400
EYES = np.float32([[118, 170], [202, 170]])            # common eye positions in the output frame

def align(img, pts):
    """Similarity transform putting the two eye centres at EYES."""
    (x1, y1), (x2, y2) = pts[0], pts[1]
    (u1, v1), (u2, v2) = EYES
    s = np.hypot(u2 - u1, v2 - v1) / np.hypot(x2 - x1, y2 - y1)
    ang = np.arctan2(v2 - v1, u2 - u1) - np.arctan2(y2 - y1, x2 - x1)
    c, n = s * np.cos(ang), s * np.sin(ang)
    M = np.float32([[c, -n, u1 - (c * x1 - n * y1)], [n, c, v1 - (n * x1 + c * y1)]])
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    p = np.hstack([pts, np.ones((len(pts), 1), np.float32)]) @ M.T
    return out.astype(np.float32), p.astype(np.float32)

A = cv2.imread(A_PATH, cv2.IMREAD_COLOR)
B = cv2.cvtColor(cv2.imread(B_PATH, cv2.IMREAD_GRAYSCALE), cv2.COLOR_GRAY2BGR)
A, pa = align(A, PA); B, pb = align(B, PB)
border = np.float32([[0,0],[W/2,0],[W-1,0],[W-1,H/2],[W-1,H-1],[W/2,H-1],[0,H-1],[0,H/2]])
pa, pb = np.vstack([pa, border]), np.vstack([pb, border])
tris = Delaunay((pa + pb) / 2).simplices

def warp(img, src, dst):
    out = np.zeros_like(img)
    for t in tris:
        s, d = src[t].astype(np.float32), dst[t].astype(np.float32)
        r = cv2.boundingRect(d); x, y, w, h = r
        if w == 0 or h == 0: continue
        dl = d - [x, y]
        M = cv2.getAffineTransform(s, dl.astype(np.float32))
        patch = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        mask = np.zeros((h, w, 3), np.float32); cv2.fillConvexPoly(mask, np.int32(dl), (1, 1, 1), cv2.LINE_AA)
        roi = out[y:y + h, x:x + w]
        mh, mw = roi.shape[:2]
        roi[:] = roi * (1 - mask[:mh, :mw]) + patch[:mh, :mw] * mask[:mh, :mw]
    return out

frames_dir = os.path.join(os.path.dirname(OUT) or ".", "_frames"); os.makedirs(frames_dir, exist_ok=True)
FPS, HOLD, STEPS = 20, 10, 50
ts = [0.0] * HOLD + [0.5 - 0.5 * np.cos(np.pi * k / (STEPS - 1)) for k in range(STEPS)] + [1.0] * HOLD   # ease in/out
for i, t in enumerate(ts):
    pt = ((1 - t) * pa + t * pb).astype(np.float32)
    f = (1 - t) * warp(A, pa, pt) + t * warp(B, pb, pt)
    cv2.imwrite(os.path.join(frames_dir, f"f{i:03d}.png"), np.clip(f, 0, 255).astype(np.uint8))
for crf in (20, 23, 26, 30, 34, 38):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(frames_dir, "f%03d.png"),
                    "-c:v", "libx264", "-preset", "veryslow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], check=True)
    if os.path.getsize(OUT) < 95_000: break
print("frames", len(ts), "crf", crf, "bytes", os.path.getsize(OUT))
