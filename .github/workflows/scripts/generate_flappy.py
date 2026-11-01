import os
import html
from datetime import date
from pathlib import Path

import requests

USERNAME = os.environ.get("GITHUB_USERNAME", "PhanQuoc0209")
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            weekday
            contributionCount
          }
        }
      }
    }
  }
}
"""

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": QUERY, "variables": {"login": USERNAME}},
    headers={"Authorization": f"Bearer {TOKEN}"},
    timeout=30,
)
response.raise_for_status()
data = response.json()
if data.get("errors"):
    raise RuntimeError(f"GitHub GraphQL error: {data['errors']}")
user = data.get("data", {}).get("user")
if not user:
    raise RuntimeError(f"GitHub user not found: {USERNAME}")
weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
if not weeks:
    raise RuntimeError("GitHub returned an empty contribution calendar")

# Original contribution counts, recolored from green to blue.
def shade(count: int) -> str:
    if count == 0:
        return "#EAF4FC"
    if count <= 2:
        return "#CDE8FA"
    if count <= 5:
        return "#91CEF5"
    if count <= 9:
        return "#4BADEB"
    return "#0878C9"

cell, gap = 10, 3
step = cell + gap
left, top = 27, 28
width = left + len(weeks) * step + 10
height = top + 7 * step + 12
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution graph with animated blue bird and obstacles">',
    '<title>GitHub Flappy Bird contribution graph</title>',
    '<rect width="100%" height="100%" rx="10" fill="#FFFFFF"/>',
]

# Weekday labels
for label, weekday in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
    y = top + weekday * step + 8
    parts.append(f'<text x="1" y="{y}" font-family="Arial,sans-serif" font-size="8" fill="#7A8794">{label}</text>')

# Month labels
last_month = None
for wi, week in enumerate(weeks):
    if not week["contributionDays"]:
        continue
    first_day = date.fromisoformat(week["contributionDays"][0]["date"])
    if first_day.month != last_month:
        x = left + wi * step
        parts.append(f'<text x="{x}" y="13" font-family="Arial,sans-serif" font-size="9" fill="#7A8794">{html.escape(first_day.strftime("%b"))}</text>')
        last_month = first_day.month

# Contribution cells: real dates/counts from GitHub, custom blue palette.
parts.append('<g id="contribution-grid">')
for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        x = left + wi * step
        y = top + int(day["weekday"]) * step
        count = int(day["contributionCount"])
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{shade(count)}">'
            f'<title>{html.escape(day["date"])}: {count} contributions</title></rect>'
        )
parts.append('</g>')

# Three pairs of obstacles moving from right to left over the real contribution grid.
# Each obstacle pair leaves a clear passage in the center.
obstacle_top, opening_top, opening_bottom = 34, 58, 105
obstacle_bottom = height - 3
pipe_w = 16
parts.append('<g id="obstacles" opacity="0.92">')
for delay in ("0s", "-2.7s", "-5.4s"):
    parts.append(
        f'<g transform="translate(0 0)">'
        f'<rect x="0" y="{obstacle_top}" width="{pipe_w}" height="{opening_top-obstacle_top}" rx="3" fill="#176FA8"/>'
        f'<rect x="-2" y="{opening_top-5}" width="{pipe_w+4}" height="7" rx="2" fill="#64BDF2"/>'
        f'<rect x="0" y="{opening_bottom}" width="{pipe_w}" height="{obstacle_bottom-opening_bottom}" rx="3" fill="#176FA8"/>'
        f'<rect x="-2" y="{opening_bottom}" width="{pipe_w+4}" height="7" rx="2" fill="#64BDF2"/>'
        f'<animateTransform attributeName="transform" type="translate" from="{width+20} 0" to="-25 0" dur="8s" begin="{delay}" repeatCount="indefinite"/>'
        f'</g>'
    )
parts.append('</g>')

# Round blue bird, with a small animated wing and gentle vertical bob.
bird_y = (opening_top + opening_bottom) / 2
parts.append(
    f'<g id="bird">'
    f'<animateTransform attributeName="transform" type="translate" values="130 {bird_y-4};130 {bird_y+4};130 {bird_y-4}" dur="1s" repeatCount="indefinite"/>'
    '<circle cx="0" cy="0" r="9" fill="#38A9F5" stroke="#0878C9" stroke-width="1.2"/>'
    '<ellipse cx="-2" cy="3" rx="4.5" ry="3" fill="#BDE5FF">'
    '<animateTransform attributeName="transform" type="rotate" values="-20 -2 3;20 -2 3;-20 -2 3" dur="0.35s" repeatCount="indefinite"/>'
    '</ellipse>'
    '<circle cx="3" cy="-3" r="1.8" fill="#FFFFFF"/>'
    '<circle cx="3.5" cy="-3" r="0.8" fill="#17324D"/>'
    '<path d="M8,-1 L14,2 L8,4 Z" fill="#FFB84D"/>'
    '</g>'
)
parts.append('</svg>')

Path("dist").mkdir(exist_ok=True)
Path("dist/github-flappy.svg").write_text("\n".join(parts), encoding="utf-8")
print(f"Generated dist/github-flappy.svg for {USERNAME}")
