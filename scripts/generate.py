#!/usr/bin/env python3
"""Generate the animated SVG sections of the profile README from live GitHub data."""
import collections
import json
import math
import os
import urllib.request
from pathlib import Path

LOGIN = "gokuls456"
NAME = "GOKUL S"
ASSETS = Path(__file__).resolve().parent.parent / "assets"
TOKEN = os.environ["GH_TOKEN"]

INK, CHAR, ORANGE, AMBER, CREAM, MUTED, RED = (
    "#14100d", "#231710", "#ff7a18", "#ffb347", "#fff4e6", "#d9c8b8", "#c8451b",
)
SANS = "Helvetica,Arial,sans-serif"
DISPLAY = "Impact,'Arial Black',Helvetica,sans-serif"


def api(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("User-Agent", "profile-generator")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def fetch():
    repos = api(f"https://api.github.com/users/{LOGIN}/repos?per_page=100&type=owner")
    repos = [r for r in repos if not r["fork"] and r["name"] != LOGIN]
    query = """query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{contributionCount}}}}}}"""
    cal = api("https://api.github.com/graphql", {"query": query, "variables": {"l": LOGIN}})
    cal = cal["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
    days = [c for w in weeks for c in w]
    best = run = 0
    for c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    langs = collections.Counter(r["language"] for r in repos if r["language"])
    return {
        "repos": len(repos), "total": cal["totalContributions"], "active": sum(1 for c in days if c),
        "streak": best, "langs": langs.most_common(4), "weeks": weeks,
    }


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">'
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{INK}"/>'
            f'<stop offset=".65" stop-color="#2a1409"/><stop offset="1" stop-color="#7a2a08"/></linearGradient>'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{AMBER}" stop-opacity=".55"/>'
            f'<stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/></radialGradient></defs>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="url(#bg)" stroke="{ORANGE}" stroke-width="2"/>'
            f'{body}</svg>\n')


def text(x, y, s, size=18, fill=CREAM, weight=400, family=SANS, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>')


def spiral(cx, cy, turns=4.25, r_max=112, steps=240):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a, r = t * turns * 2 * math.pi, 4 + (r_max - 4) * t
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return "M" + " L".join(pts)


def rotating_spiral(cx, cy, r, width=8, dur=16, color=ORANGE):
    return (f'<path d="{spiral(cx, cy, r_max=r)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round">'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" '
            f'dur="{dur}s" repeatCount="indefinite"/></path>')


def fade_cycle(i, n, slot):
    """Opacity animation showing item i of n during its slot of a repeating loop."""
    total = n * slot
    a, b = i / n, (i + 1) / n
    eps = .25 / total
    times = [0, max(a - eps, 0), a, b - eps, b, 1]
    vals = ["0", "0", "1", "1", "0", "0"]
    if i == 0:
        times, vals = [0, b - eps, b, 1], ["1", "1", "0", "0"]
    return (f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" '
            f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" values="{";".join(vals)}"/>')


def avatar(x, y, s=1.0, pointing=False):
    """Original character: dark swept hair, code-plate headband, orange scarf."""
    skin, hair, coat = "#f0c29a", "#1c1a22", "#2b2f3a"
    arm = (f'<path d="M58 118 L126 92" stroke="{coat}" stroke-width="24" stroke-linecap="round"/>'
           f'<circle cx="132" cy="90" r="13" fill="{skin}"/><path d="M140 86 L170 78" stroke="{skin}" stroke-width="8" stroke-linecap="round"/>'
           if pointing else
           f'<path d="M58 124 L72 186" stroke="{coat}" stroke-width="24" stroke-linecap="round"/>')
    return f'''<g transform="translate({x} {y}) scale({s})">
<path d="M-62 112 Q-58 86 -22 80 L22 80 Q58 86 62 112 L70 214 L-70 214Z" fill="{coat}"/>
<path d="M-58 124 L-72 186" stroke="{coat}" stroke-width="24" stroke-linecap="round"/>{arm}
<path d="M-40 82 Q0 112 40 82 L46 100 Q0 130 -46 100Z" fill="{ORANGE}"/>
<path d="M34 96 L74 138 L52 142 L28 108Z" fill="{RED}"/>
<ellipse cx="0" cy="26" rx="47" ry="55" fill="{skin}"/>
<path d="M-52 16 L-64 -30 L-38 -20 L-40 -60 L-12 -38 L4 -74 L18 -40 L46 -60 L42 -20 L66 -28 L52 18 L40 -12 L-38 -12Z" fill="{hair}"/>
<rect x="-50" y="-14" width="100" height="24" rx="4" fill="#20242c"/>
<rect x="-27" y="-18" width="54" height="32" rx="4" fill="#aab3c0" stroke="#6b7482" stroke-width="2"/>
{text(0, 4, "&lt;/&gt;", 18, "#20242c", 700, SANS, "middle")}
<ellipse cx="-19" cy="32" rx="7" ry="9" fill="#20242c"><animate attributeName="ry" values="9;9;1;9;9" keyTimes="0;.9;.94;.98;1" dur="4.5s" repeatCount="indefinite"/></ellipse>
<ellipse cx="19" cy="32" rx="7" ry="9" fill="#20242c"><animate attributeName="ry" values="9;9;1;9;9" keyTimes="0;.9;.94;.98;1" dur="4.5s" repeatCount="indefinite"/></ellipse>
<path d="M-13 58 Q0 70 13 58" fill="none" stroke="#7a3b22" stroke-width="4" stroke-linecap="round"/>
</g>'''


def hero():
    roles = ["Full-stack builder", "Options systems engineer", "Web app shinobi"]
    cycling = "".join(
        f'<g opacity="{1 if i == 0 else 0}">{text(430, 214, r, 30, AMBER, 700)}{fade_cycle(i, 3, 3)}</g>'
        for i, r in enumerate(roles))
    corners = "".join(
        f'<path d="{d}" fill="none" stroke="{AMBER}" stroke-width="4"/>' for d in
        ["M60 76V48H88", "M332 76V48H304", "M60 300V328H88", "M332 300V328H304"])
    body = f'''<circle cx="1015" cy="188" r="210" fill="url(#glow)"/>
{rotating_spiral(1015, 188, 118)}
<rect x="60" y="48" width="272" height="280" fill="#100c0a" opacity=".55"/>{corners}
<circle cx="84" cy="72" r="6" fill="#ff3b30"><animate attributeName="opacity" values="1;.1;1" dur="1.4s" repeatCount="indefinite"/></circle>
{text(98, 78, "LIVE", 14, CREAM, 700)}
{avatar(196, 118)}
{text(430, 90, "SHINOBI FILE", 18, ORANGE, 700, SANS, "start", 'letter-spacing="4"')}
{text(428, 170, NAME, 84, CREAM, 400, DISPLAY)}
{cycling}
{text(430, 264, "Never go back on your commits. That is my ninja way.", 20, MUTED)}'''
    return svg(1200, 376, body, f"{NAME}, code shinobi")


def story_bars(n, slot, x=30, y=26, width=530):
    gap, w, out = 8, (width - (n - 1) * 8) / n, ""
    for i in range(n):
        bx = x + i * (w + gap)
        begin, end = i / n, (i + 1) / n
        times, vals = [0, begin, end, 1], [0, 0, w, 0]
        if i == n - 1:
            times, vals = [0, begin, 1], [0, 0, w]
        out += (f'<rect x="{bx:.1f}" y="{y}" width="{w:.1f}" height="5" rx="2.5" fill="#fff4e6" opacity=".2"/>'
                f'<rect x="{bx:.1f}" y="{y}" width="0" height="5" rx="2.5" fill="{ORANGE}">'
                f'<animate attributeName="width" dur="{n*slot}s" repeatCount="indefinite" '
                f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" values="{";".join(f"{v:.1f}" for v in vals)}"/></rect>')
    return out


def carousel(title, slides, label):
    n, slot, body = len(slides), 4, ""
    body += story_bars(n, slot) + text(30, 72, title, 26, ORANGE, 400, DISPLAY, "start", 'letter-spacing="1"')
    for i, (head, line1, line2, glyph) in enumerate(slides):
        body += (f'<g opacity="{1 if i == 0 else 0}">{glyph}{text(190, 170, head, 32, CREAM, 700)}'
                 f'{text(190, 208, line1, 19, MUTED)}{text(190, 236, line2, 19, MUTED)}{fade_cycle(i, n, slot)}</g>')
    return svg(590, 320, body, label)


def glyph_chart():
    bars = "".join(f'<rect x="{50+i*20}" y="{190-h}" width="12" height="{h}" fill="{ORANGE if i%2 else AMBER}"/>'
                   for i, h in enumerate([34, 62, 44, 88, 70]))
    return bars + f'<path d="M46 196H154" stroke="{CREAM}" stroke-width="3"/>'


def glyph_code():
    return text(102, 184, "&lt;/&gt;", 54, ORANGE, 700, SANS, "middle")


def glyph_bot():
    return (f'<path d="M46 182L156 118L120 216L100 170Z" fill="{ORANGE}"/>'
            f'<path d="M100 170L156 118" stroke="{INK}" stroke-width="3"/>')


def glyph_candles():
    out = ""
    for i, (a, b, c) in enumerate([(180, 40, 1), (162, 56, 0), (142, 62, 1), (126, 50, 1)]):
        x = 58 + i * 26
        out += (f'<path d="M{x+7} {a-14}V{a+b+14}" stroke="{CREAM}" stroke-width="2"/>'
                f'<rect x="{x}" y="{a}" width="14" height="{b}" fill="{AMBER if c else RED}"/>')
    return out


def glyph_scroll():
    return (f'<rect x="60" y="110" width="84" height="100" fill="{CREAM}"/><rect x="50" y="100" width="104" height="14" rx="7" fill="{ORANGE}"/>'
            f'<rect x="50" y="206" width="104" height="14" rx="7" fill="{ORANGE}"/>'
            f'<path d="{spiral(102, 160, turns=2.5, r_max=26, steps=80)}" fill="none" stroke="{RED}" stroke-width="4"/>')


def glyph_pad():
    return (f'<rect x="46" y="130" width="112" height="66" rx="30" fill="{ORANGE}"/>'
            f'<path d="M78 148v28M64 162h28" stroke="{INK}" stroke-width="7"/>'
            f'<circle cx="124" cy="152" r="7" fill="{INK}"/><circle cx="138" cy="172" r="7" fill="{INK}"/>')


def orbit():
    cx, cy = 300, 190
    rings = [(92, 12, [("JS", 0), ("TS", 180)]), (150, 20, [("Py", 90), ("HTML", 270)])]
    body = f'<circle cx="{cx}" cy="{cy}" r="170" fill="url(#glow)"/>{rotating_spiral(cx, cy, 44, 5, 8)}'
    for radius, dur, items in rings:
        body += f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{AMBER}" stroke-dasharray="3 10" stroke-width="2"/>'
        for label, start in items:
            a = math.radians(start)
            x, y = cx + radius * math.cos(a), cy + radius * math.sin(a)
            body += (f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/>'
                     f'<g transform="translate({x:.1f} {y:.1f})"><g><animateTransform attributeName="transform" type="rotate" from="0" to="-360" dur="{dur}s" repeatCount="indefinite"/>'
                     f'<circle r="27" fill="{INK}" stroke="{ORANGE}" stroke-width="3"/>{text(0, 5, label, 15, CREAM, 700, SANS, "middle")}</g></g></g>')
    body += text(610, 92, "JUTSU SCROLLS", 42, ORANGE, 400, DISPLAY)
    chips = ["Python", "TypeScript", "JavaScript", "HTML", "Options backtesting", "Telegram bots", "Web apps", "Market data"]
    for i, c in enumerate(chips):
        x, y = 610 + (i % 2) * 280, 130 + (i // 2) * 54
        body += (f'<rect x="{x}" y="{y}" width="264" height="42" rx="6" fill="{INK}" stroke="{ORANGE}"/>'
                 + text(x + 132, y + 27, c, 18, CREAM, 700, SANS, "middle"))
    return svg(1200, 380, body, "Tech stack: Python, TypeScript, JavaScript, HTML")


def badge(d):
    stats = [("Contributions, last year", d["total"]), ("Active days", d["active"]),
             ("Longest streak", f'{d["streak"]}d'), ("Public missions", d["repos"])]
    card = f'''<g><animateTransform attributeName="transform" type="rotate" values="-4 210 -20;4 210 -20;-4 210 -20" keyTimes="0;.5;1" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" dur="5s" repeatCount="indefinite"/>
<path d="M210 -20V40" stroke="{ORANGE}" stroke-width="10"/>
<rect x="80" y="40" width="260" height="346" rx="16" fill="#1b1512" stroke="{AMBER}" stroke-width="3"/>
<rect x="176" y="52" width="68" height="10" rx="5" fill="{ORANGE}"/>
{avatar(210, 142, .62)}
<rect x="80" y="282" width="260" height="104" fill="{ORANGE}" opacity=".95"/>
{text(210, 322, NAME, 34, INK, 400, DISPLAY, "middle")}
{text(210, 350, "Rank: Shinobi of Commits", 16, INK, 700, SANS, "middle")}
{text(210, 372, "@" + LOGIN, 14, INK, 700, SANS, "middle")}</g>'''
    body = card + text(420, 66, "SHINOBI STATS", 42, ORANGE, 400, DISPLAY)
    for i, (label, value) in enumerate(stats):
        x = 420 + i * 190
        body += (f'<rect x="{x}" y="90" width="176" height="104" rx="10" fill="{INK}" stroke="{ORANGE}"/>'
                 + text(x + 16, 146, value, 40, CREAM, 400, DISPLAY) + text(x + 16, 176, label, 13, MUTED))
    body += text(420, 238, "Public repos by language", 20, AMBER, 700)
    top = max([c for _, c in d["langs"]] or [1])
    for i, (lang, count) in enumerate(d["langs"]):
        y, w = 256 + i * 30, 500 * count / top
        body += (text(420, y + 16, lang, 15, CREAM, 700)
                 + f'<rect x="540" y="{y}" width="0" height="20" rx="3" fill="{ORANGE}"><animate attributeName="width" from="0" to="{w:.0f}" dur="1.6s" fill="freeze"/></rect>'
                 + text(1060, y + 16, count, 15, CREAM, 700, SANS, "end"))
    return svg(1200, 400, body, "Stats and language chart")


def city(d):
    dx, dy, ox, oy = 15, 7.5, 255, 135
    cells = sorted(((w, day, c) for w, week in enumerate(d["weeks"]) for day, c in enumerate(week)),
                   key=lambda t: t[0] + t[1])
    body = text(36, 58, "THE VILLAGE OF COMMITS", 34, ORANGE, 400, DISPLAY)
    body += text(36, 86, "Every building is a day of work. Rebuilt daily.", 17, MUTED)
    for w, day, c in cells:
        x, y = ox + (w - day) * dx, oy + (w + day) * dy
        h = 3 + min(c, 14) * 7
        roof = AMBER if c else "#3a2a20"
        left, right = (ORANGE, RED) if c else ("#2c2019", "#241a14")
        body += (f'<polygon points="{x},{y-h} {x+dx},{y+dy-h} {x},{y+2*dy-h} {x-dx},{y+dy-h}" fill="{roof}"/>'
                 f'<polygon points="{x-dx},{y+dy-h} {x},{y+2*dy-h} {x},{y+2*dy} {x-dx},{y+dy}" fill="{left}"/>'
                 f'<polygon points="{x+dx},{y+dy-h} {x},{y+2*dy-h} {x},{y+2*dy} {x+dx},{y+dy}" fill="{right}"/>')
    return svg(1200, 610, body, f'Contribution city: {d["total"]} contributions in the last year')


def footer():
    body = f'''<circle cx="210" cy="190" r="170" fill="url(#glow)"/>
{avatar(190, 104, 1, pointing=True)}
{text(490, 92, "SEND A MESSENGER HAWK", 44, ORANGE, 400, DISPLAY)}
<rect x="490" y="122" width="560" height="96" rx="12" fill="{INK}" stroke="{AMBER}" stroke-width="3">
<animate attributeName="stroke-opacity" values="1;.35;1" dur="2.2s" repeatCount="indefinite"/></rect>
{text(770, 186, "@" + LOGIN, 46, CREAM, 400, DISPLAY, "middle")}
{text(490, 266, "Find my missions on GitHub. Believe in the build.", 21, MUTED)}'''
    return svg(1200, 340, body, f"Connect with {LOGIN} on GitHub")


def main():
    ASSETS.mkdir(exist_ok=True)
    data = fetch()
    build = carousel("WHAT I BUILD", [
        ("Trading systems", "Backtests on real option premiums", "and strategy research for NIFTY", glyph_chart()),
        ("Web apps", "Full-stack products in", "TypeScript and JavaScript", glyph_code()),
        ("Signal alerts", "Strategy signals delivered", "straight to Telegram", glyph_bot()),
    ], "What I build")
    hobbies = carousel("OFF-MISSION", [
        ("Trading and markets", "Reading price action", "and testing ideas", glyph_candles()),
        ("Anime", "Where the ninja way", "comes from", glyph_scroll()),
        ("Gaming", "Side quests between", "shipping sessions", glyph_pad()),
    ], "Hobbies")
    files = {"hero": hero(), "build": build, "hobbies": hobbies, "orbit": orbit(),
             "badge": badge(data), "city": city(data), "footer": footer()}
    for name, content in files.items():
        (ASSETS / f"{name}.svg").write_text(content)
    print({k: v for k, v in data.items() if k != "weeks"})


if __name__ == "__main__":
    main()
