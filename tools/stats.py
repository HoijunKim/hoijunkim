"""
Draw profile/stats.svg: activity in the last 12 months and the language mix
of public repos, from the GitHub GraphQL API.

    GITHUB_TOKEN=... python tools/stats.py

The profile workflow runs it with the default Actions token, so the card shows
what a visitor sees: public repos, and private work only as the daily counts
of the contribution graph. Nothing is written if the request fails.
"""
import json
import os
import urllib.request
from collections import Counter
from xml.sax.saxutils import escape

LOGIN = os.environ.get("GITHUB_REPOSITORY_OWNER", "hoijunkim")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile", "stats.svg")
HIDE = {"CSS", "HTML", "SCSS", "NSIS"}  # markup and installer scripts, not code
SHOWN = 3  # languages drawn before the rest fold into Other

# The card is always dark, like the screenshots above it. Colours follow
# GitHub's dark UI; each language keeps its hue whatever its rank.
SURFACE, BORDER, TEXT, MUTED, ACCENT = "#161b22", "#30363d", "#e6edf3", "#9198a1", "#3987e5"
OTHER = "#6e7681"
LANG = {"TypeScript": "#3987e5", "Svelte": "#d95926", "Go": "#199e70", "Python": "#c98500",
        "JavaScript": "#d55181", "C++": "#008300", "Astro": "#9085e9", "C": "#e66767"}
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
W, H, P = 840, 270, 24
COL = (W - 2 * P) / 4

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalPullRequestContributions
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      nodes { languages(first: 20) { edges { size node { name } } } }
    }
  }
}"""


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", body, {
        "Authorization": "bearer " + os.environ["GITHUB_TOKEN"],
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {data['errors']}")
    return data["data"]["user"]


def longest_streak(counts):
    best = run = 0
    for n in counts:
        run = run + 1 if n else 0
        best = max(best, run)
    return best


def buckets(counts, n=12, size=28):
    """Sums of the last n blocks of `size` days, oldest first."""
    tail = counts[-n * size:]
    return [sum(tail[i:i + size]) for i in range(0, len(tail), size)]


def shares(sizes):
    """(name, colour, percent) for the largest languages, then Other."""
    total = sum(sizes.values())
    # ponytail: a language without a hue in LANG folds into Other; give it one when it matters
    top = [k for k, _ in sizes.most_common() if k in LANG][:SHOWN]
    rows = [(k, LANG[k], 100 * sizes[k] / total) for k in top]
    rest = total - sum(sizes[k] for k in top)
    if rest:
        rows.append(("Other", OTHER, 100 * rest / total))
    return rows


def render(user):
    c = user["contributionsCollection"]
    cal = c["contributionCalendar"]
    counts = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    tiles = [("Contributions", cal["totalContributions"]),
             ("Active days", sum(1 for n in counts if n)),
             ("Longest streak, days", longest_streak(counts)),
             ("Pull requests", c["totalPullRequestContributions"])]
    sizes = Counter()
    for repo in user["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            if e["node"]["name"] not in HIDE:
                sizes[e["node"]["name"]] += e["size"]
    rows = shares(sizes)

    out = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="{SURFACE}" stroke="{BORDER}"/>',
           f'<text x="{P}" y="44" class="head">Last 12 months</text>']
    for i, (label, value) in enumerate(tiles):
        x = P + i * COL
        if i:
            out.append(f'<line x1="{x}" y1="64" x2="{x}" y2="142" stroke="{BORDER}"/>')
            x += 20
        out.append(f'<text x="{x}" y="78">{label}</text>')
        out.append(f'<text x="{x}" y="112" class="value">{value:,}</text>')

    # trend under the first tile: contributions per four weeks, the latest one marked
    pts = buckets(counts)
    top = max(pts) or 1
    xy = [(P + i * 150 / (len(pts) - 1), 142 - 20 * v / top) for i, v in enumerate(pts)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    out.append(f'<polyline points="{line}" fill="none" stroke="{MUTED}" stroke-width="2" '
               'stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<circle cx="{xy[-1][0]:.1f}" cy="{xy[-1][1]:.1f}" r="5" fill="{ACCENT}" '
               f'stroke="{SURFACE}" stroke-width="2"/>')

    out.append(f'<line x1="{P}" y1="166" x2="{W - P}" y2="166" stroke="{BORDER}"/>')
    out.append(f'<text x="{P}" y="196" class="head">Languages in public repos</text>')
    # one 8px bar with rounded ends, parts split by a 2px gap
    x, span, bar = P, W - 2 * P - 2 * (len(rows) - 1), []
    for _, colour, pct in rows:
        bar.append(f'<rect x="{x:.1f}" y="212" width="{span * pct / 100:.1f}" height="8" fill="{colour}"/>')
        x += span * pct / 100 + 2
    out.append(f'<g clip-path="url(#bar)">{"".join(bar)}</g>')
    for j, (name, colour, pct) in enumerate(rows):
        lx = P + j * COL
        out.append(f'<circle cx="{lx + 4}" cy="242" r="4" fill="{colour}"/>')
        out.append(f'<text x="{lx + 14}" y="246"><tspan fill="{TEXT}">{escape(name)}</tspan> {pct:.1f}%</text>')

    desc = "; ".join(f"{label}: {value:,}" for label, value in tiles) + ". Languages: " + \
        ", ".join(f"{escape(name)} {pct:.1f}%" for name, _, pct in rows) + "."
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">GitHub activity in the last 12 months</title>
<desc id="desc">{desc}</desc>
<style>text{{font-family:{FONT};font-size:12px;fill:{MUTED}}}.head{{font-size:14px;font-weight:600;fill:{TEXT}}}.value{{font-size:28px;font-weight:600;fill:{TEXT}}}</style>
<defs><clipPath id="bar"><rect x="{P}" y="212" width="{W - 2 * P}" height="8" rx="4"/></clipPath></defs>
{chr(10).join(out)}
</svg>
"""


def main():
    svg = render(fetch())
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(svg.split("<desc", 1)[1].split("</desc>", 1)[0])


if __name__ == "__main__":
    main()
