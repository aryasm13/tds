"""GA5 Q3 verification: multi-ball tracking with forward-backward consistency.

Run: uv run --with opencv-python-headless --with numpy --with scipy track_fb.py video.webm 205 357 696
Detects all balls in every frame once, then tracks all of them jointly (Hungarian matching on a
constant-velocity prediction). Tracks forward from the red ball and backward from where it ends;
the answer is trusted only if the backward track returns to the red ball in frame 0.
"""
import sys
import cv2, numpy as np
from scipy.optimize import linear_sum_assignment

path, want = sys.argv[1], [int(x) for x in sys.argv[2:]]
cap = cv2.VideoCapture(path)
frames_det, first, last = [], None, None
R = None
while True:
    ok, f = cap.read()
    if not ok:
        break
    if first is None:
        first = f
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        red = ((hsv[..., 0] < 10) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 80)
        R = float(np.sqrt(red.sum() / np.pi))
        ys, xs = np.nonzero(red)
        red_c = np.array([xs.mean(), ys.mean()])
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    mask = (g < 215).astype(np.uint8)
    # fill holes (the numbers printed on the balls at the end): flood-fill the background from a corner
    n_h, lab, st, _ = cv2.connectedComponentsWithStats(1 - mask)
    small = np.isin(lab, [j for j in range(1, n_h) if st[j, cv2.CC_STAT_AREA] < 0.6 * np.pi * R * R])
    mask = mask | small.astype(np.uint8)
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    peak = (dist == cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(R), int(R))))) & (dist > R * 0.6)
    _, _, _, cents = cv2.connectedComponentsWithStats(peak.astype(np.uint8))
    frames_det.append(cents[1:])
    last = f
N = len(frames_det)


def run(order, start_xy, alpha):
    pos = frames_det[order[0]].copy()
    me = int(np.linalg.norm(pos - start_xy, axis=1).argmin())
    vel = np.zeros_like(pos)
    out = {order[0]: pos[me].copy()}
    for k in order[1:]:
        det = frames_det[k]
        pred = pos + alpha * vel
        r, c = linear_sum_assignment(np.linalg.norm(pred[:, None] - det[None], axis=2))
        new = pred.copy()
        new[r] = det[c]
        vel = new - pos
        pos = new
        out[k] = pos[me].copy()
    return out


best = None
for alpha in (1.0, 0.8, 0.5, 0.0):
    fwd = run(list(range(N)), red_c, alpha)
    bwd = run(list(range(N - 1, -1, -1)), fwd[N - 1], alpha)
    err0 = float(np.linalg.norm(bwd[0] - red_c))
    agree = float(np.mean([np.linalg.norm(fwd[k] - bwd[k]) < 3 for k in range(N)]))
    print(f"alpha={alpha}: backward lands {err0:.1f}px from red start, fwd/bwd agree on {agree:.0%} of frames, "
          f"answer: " + "; ".join(f"{round(fwd[k][0])},{round(fwd[k][1])}" for k in want) + f" | final {np.round(fwd[N-1])}")
    if best is None or (err0, -agree) < (best[0], -best[1]):
        best = (err0, agree, fwd)

fwd = best[2]
x, y = fwd[N - 1]
crop = last[max(0, int(y) - 40):int(y) + 40, max(0, int(x) - 40):int(x) + 40]
cv2.imwrite("last_crop.png", cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST))
print("BEST:", "; ".join(f"{round(fwd[k][0])},{round(fwd[k][1])}" for k in want), "final", np.round(fwd[N - 1]))
