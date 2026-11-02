"""Checks for stats.py that need no network: python tools/test_stats.py"""
import xml.etree.ElementTree as ET
from collections import Counter

from stats import buckets, longest_streak, render, shares

assert longest_streak([0, 1, 1, 0, 1, 1, 1, 0]) == 3
assert longest_streak([0, 0]) == 0
assert buckets(list(range(60)), n=2, size=28) == [sum(range(4, 32)), sum(range(32, 60))]

# Rust has no hue, so it folds into Other with the fourth-largest language
rows = shares(Counter({"Go": 50, "Rust": 20, "TypeScript": 15, "Python": 10, "Svelte": 5}))
assert [r[0] for r in rows] == ["Go", "TypeScript", "Python", "Other"]
assert abs(sum(r[2] for r in rows) - 100) < 1e-9
assert rows[-1][2] == 25

days = [{"contributionCount": n} for n in [0, 3, 0, 7] * 100]
user = {
    "contributionsCollection": {
        "totalPullRequestContributions": 4,
        "contributionCalendar": {"totalContributions": 1000, "weeks": [{"contributionDays": days}]},
    },
    "repositories": {"nodes": [{"languages": {"edges": [
        {"size": 9, "node": {"name": "C++"}}, {"size": 1, "node": {"name": "HTML"}}]}}]},
}
svg = ET.fromstring(render(user))
assert "C++ 100.0%" in svg.find("{http://www.w3.org/2000/svg}desc").text
print("ok")
