import os, json, base64, urllib.request, html

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "weekly-coding.svg")
API_KEY = os.getenv("WAKATIME_API_KEY", "").strip()

palette = ["#DC819B", "#EDA8BA", "#F5C9D4", "#FBE6EB", "#FFF1F5"]
text = "#4F484B"
muted = "#8E8387"
track = "#FFF6F8"
border = "#EEE6E8"

def write_svg(total="WakaTime not connected", languages=None, note="Add WAKATIME_API_KEY to enable weekly stats"):
    languages = languages or []
    width, height = 420, 180
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}</style>',
        '<rect width="100%" height="100%" rx="10" fill="#FFFFFF" stroke="#EEE6E8"/>',
        f'<text x="22" y="28" font-size="11" fill="{muted}">Coding time</text>',
        f'<text x="22" y="58" font-size="27" font-weight="600" fill="{text}">{html.escape(total)}</text>',
    ]
    if languages:
        max_seconds = max(float(x.get("total_seconds", 0) or 0) for x in languages) or 1
        y = 83
        for i, lang in enumerate(languages[:3]):
            name = str(lang.get("name","Other"))
            secs = float(lang.get("total_seconds",0) or 0)
            pct = max(0.04, min(1, secs/max_seconds))
            hrs = int(secs//3600)
            mins = int((secs%3600)//60)
            t = f"{hrs}h {mins:02d}m" if hrs else f"{mins}m"
            parts += [
                f'<text x="22" y="{y+9}" font-size="11" fill="{text}">{html.escape(name)}</text>',
                f'<rect x="105" y="{y}" width="215" height="10" rx="5" fill="{track}"/>',
                f'<rect x="105" y="{y}" width="{215*pct:.1f}" height="10" rx="5" fill="{palette[i]}"/>',
                f'<text x="334" y="{y+9}" font-size="10" fill="{muted}">{t}</text>',
            ]
            y += 28
    else:
        parts += [
            f'<rect x="22" y="84" width="280" height="10" rx="5" fill="{track}"/>',
            f'<rect x="22" y="84" width="185" height="10" rx="5" fill="#F5C9D4"/>',
        ]
    parts.append(f'<text x="22" y="160" font-size="9.5" fill="{muted}">{html.escape(note)}</text>')
    parts.append('</svg>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(parts))

if not API_KEY:
    write_svg()
    raise SystemExit(0)

token = base64.b64encode(API_KEY.encode()).decode()
req = urllib.request.Request(
    "https://wakatime.com/api/v1/users/current/stats/last_7_days",
    headers={"Authorization": f"Basic {token}", "User-Agent": "ryujxx-profile-weekly"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    data = payload.get("data", {})
    total = data.get("human_readable_total_including_other_language") or data.get("human_readable_total") or "0 mins"
    langs = data.get("languages", [])
    langs = sorted(langs, key=lambda x: float(x.get("total_seconds", 0) or 0), reverse=True)
    write_svg(total=total, languages=langs, note="Last 7 days · WakaTime")
except Exception as e:
    write_svg(total="WakaTime unavailable", note="The last update could not load WakaTime data")
