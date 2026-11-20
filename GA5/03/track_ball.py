"""GA5 Q3: track the initially-red ball through every frame and report its centre at given frames.

Run: uv run --with opencv-python-headless --with numpy --with scipy track_ball.py video.webm 205 357 696
Detects every ball each frame (Hough circles of the known radius), then tracks ALL balls jointly with
one-to-one Hungarian matching on velocity-predicted positions, so neighbours can't be swapped greedily.
"""
import sys
import cv2, numpy as np
from scipy.optimize import linear_sum_assignment

path, want = sys.argv[1], [int(x) for x in sys.argv[2:]]
cap = cv2.VideoCapture(path)
ok, first = cap.read()
hsv = cv2.cvtColor(first, cv2.COLOR_BGR2HSV)
red = ((hsv[..., 0] < 10) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 80)
R = float(np.sqrt(red.sum() / np.pi))                      # ball radius from the red disc area
ys, xs = np.nonzero(red)
red_c = np.array([xs.mean(), ys.mean()])


def detect(frame):
    """Disc centres = peaks of the distance transform of the non-background mask (splits touching discs)."""
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = (g < 215).astype(np.uint8)
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    peak = (dist == cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(R), int(R))))) & (dist > R * 0.6)
    n, _, _, cents = cv2.connectedComponentsWithStats(peak.astype(np.uint8))
    return cents[1:]


pos = detect(first)
me = int(np.linalg.norm(pos - red_c, axis=1).argmin())
vel = np.zeros_like(pos)
nd = []
track, worst, i, last = {0: pos[me].copy()}, 0.0, 0, first
while True:
    ok, f = cap.read()
    if not ok:
        break
    i += 1
    det = detect(f)
    if len(det):
        pred = pos + vel
        cost = np.linalg.norm(pred[:, None] - det[None], axis=2)
        r, c = linear_sum_assignment(cost)
        good = np.ones(len(r), bool)  # every ball is detected every frame, so match all of them
        newpos = pred.copy()                                   # unmatched balls coast on prediction
        newpos[r[good]] = det[c[good]]
        nd.append(len(det))
        if me in r[good]:
            worst = max(worst, float(cost[me, c[list(r).index(me)]]))   # how far my ball jumped
        vel = newpos - pos
        pos = newpos
    track[i] = pos[me].copy()
    last = f
x, y = track[max(track)]
cv2.imwrite("last_crop.png", cv2.resize(last[max(0, int(y) - 45):int(y) + 45, max(0, int(x) - 45):int(x) + 45], None, fx=4, fy=4,
                                        interpolation=cv2.INTER_NEAREST))
print("detections min/median/max", min(nd), int(np.median(nd)), max(nd))
print(f"radius {R:.1f}, balls tracked {len(pos)}, frames {i + 1}, worst match residual for my ball {worst:.1f}px")
print("final", round(x), round(y))
print("; ".join(f"{round(track[k][0])},{round(track[k][1])}" for k in want))
