"""Q4 Calculate variance: print the sample variance (N-1) of q-calculate-variance.json, rounded to 2 decimals.

Run: uv run q04_calculate_variance.py path/to/q-calculate-variance.json
"""
import json, statistics, sys

if len(sys.argv) < 2:
    sys.exit(__doc__)
data = json.load(open(sys.argv[1]))
print(round(statistics.variance(data), 2))
