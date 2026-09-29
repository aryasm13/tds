import json, statistics
data = json.load(open("q-calculate-variance.json"))
print(round(statistics.variance(data), 2))   # 132.05