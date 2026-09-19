import os
import json
import urllib.request
from datetime import datetime

USERNAME = os.getenv("GITHUB_USERNAME", "ryurujxx")
TOKEN = os.environ["GH_TOKEN"]

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          firstDay
          contributionDays {
            date
            contributionCount
            weekday
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {"login": USERNAME}
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "ryujxx-profile-activity"
    }
)

with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"][-53:]
total = calendar["totalContributions"]

counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
positive = sorted(c for c in counts if c > 0)

def level(count):
    if count <= 0:
        return 0
    if not positive:
        return 1
    # Quantile-ish thresholds so the pink levels adapt to the user's own activity.
    q1 = positive[max(0, math.floor((len(positive)-1) * 0.25))]
    q2 = positive[max(0, math.floor((len(positive)-1) * 0.50))]
    q3 = positive[max(0, math.floor((len(positive)-1) * 0.75))]
    if count <= q1: return 1
    if count <= q2: return 2
    if count <= q3: return 3
    return 4

import math

palette = ["#FFF8F9", "#FBE6EB", "#F5C9D4", "#EDA8BA", "#DC819B"]
text = "#8E8387"
border = "#F8ECEF"

cell = 13
gap = 4
left = 42
top = 36
grid_w = 53 * (cell + gap) - gap
grid_h = 7 * (cell + gap) - gap
width = left + grid_w + 24
height = top + grid_h + 42

# Month labels
month_labels = []
seen = set()
for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        key = (dt.year, dt.month)
        if dt.day <= 7 and key not in seen:
            seen.add(key)
            month_labels.append((wi, dt.strftime("%b")))
        break

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}</style>',
    f'<rect width="100%" height="100%" fill="#FFFFFF"/>',
]

for wi, label in month_labels:
    x = left + wi * (cell + gap)
    parts.append(f'<text x="{x}" y="16" font-size="11" fill="{text}">{label}</text>')

for label, row in [("Mon",1),("Wed",3),("Fri",5)]:
    y = top + row*(cell+gap) + 10
    parts.append(f'<text x="0" y="{y}" font-size="10" fill="{text}">{label}</text>')

for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        row = int(day["weekday"])
        count = int(day["contributionCount"])
        lv = level(count)
        x = left + wi * (cell + gap)
        y = top + row * (cell + gap)
        fill = palette[lv]
        stroke = border if lv == 0 else fill
        date = day["date"]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
            f'fill="{fill}" stroke="{stroke}"><title>{date}: {count} contributions</title></rect>'
        )

# footer + legend
legend_y = top + grid_h + 26
parts.append(f'<text x="{left}" y="{legend_y}" font-size="10" fill="{text}">{total} contributions in the last year</text>')
legend_x = width - 150
parts.append(f'<text x="{legend_x-30}" y="{legend_y}" font-size="10" fill="{text}">Less</text>')
for i, c in enumerate(palette):
    x = legend_x + i*17
    parts.append(f'<rect x="{x}" y="{legend_y-10}" width="11" height="11" rx="2" fill="{c}" stroke="{border if i==0 else c}"/>')
parts.append(f'<text x="{legend_x+90}" y="{legend_y}" font-size="10" fill="{text}">More</text>')
parts.append('</svg>')

out = os.path.join(os.path.dirname(__file__), "..", "assets", "activity.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write("".join(parts))
print(f"Wrote {out}")
