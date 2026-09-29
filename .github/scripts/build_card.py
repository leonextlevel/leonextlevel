"""Gera assets/card.svg, o painel do perfil no tema planta técnica.

Com CARD_TOKEN definido, busca os dados do GitHub via GraphQL e salva em
assets/stats.json. Sem token, reaproveita o último stats.json salvo.
"""
import datetime as dt
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
STATS_FILE = ASSETS / "stats.json"
ICONS = json.loads((Path(__file__).parent / "icons.json").read_text())

LOGIN = os.environ.get("CARD_LOGIN", "leonextlevel")

PROFILE = {
    "name": "LEANDRO BUENO",
    "role": "Desenvolvedor de Software",
    "company": "Globant",
    "location": "São José dos Campos, SP",
    "tagline": "Pythonista sempre que possível",
    "status": "compilando ideias",
    "about": [
        "Construo sistemas completos",
        "com integrações e automações,",
        "do backend à infraestrutura.",
        "Busco soluções simples,",
        "eficientes e bem documentadas.",
    ],
    "focus": ["sistemas completos", "integrações", "automações"],
    "stack": [
        ("CLIENTE", ["javascript", "html5", "css"], None),
        ("API", ["python", "django", "fastapi", "flask"], None),
        ("DADOS", ["postgresql", "redis"], None),
        ("INFRA", ["docker", "linux"], None),
        ("CLOUD", ["cloud"], "AWS · GCP · Azure"),
    ],
    "zen": "Simple is better than complex.",
}

BG = "#0B1626"
PANEL = "#0E1E33"
GRID_MINOR = "#12253E"
GRID_MAJOR = "#183253"
FRAME = "#24476F"
CYAN = "#5CD6FF"
AMBER = "#FFC857"
TEXT = "#DCE8F7"
MUTED = "#7F9BBE"
DIM = "#3E5F86"
LEVELS = {
    "NONE": "#11263F",
    "FIRST_QUARTILE": "#15466B",
    "SECOND_QUARTILE": "#1D6C9C",
    "THIRD_QUARTILE": "#35A3D4",
    "FOURTH_QUARTILE": CYAN,
}
LANG_COLORS = [AMBER, CYAN, "#2F8FD8", "#A7E8FF", "#C9953A", DIM]
MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FONT = "'JetBrains Mono','Fira Code','SFMono-Regular',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"
CW = 0.6  # largura média de um caractere monoespaçado, em em

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionLevel } }
      }
    }
  }
}
"""


# ------------------------------------------------------------------ dados
def fetch_stats(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise SystemExit(f"Erro na API do GitHub: {payload['errors']}")
    user = payload["data"]["user"]
    repos = user["repositories"]
    contrib = user["contributionsCollection"]

    langs = Counter()
    for repo in repos["nodes"]:
        for edge in repo["languages"]["edges"]:
            langs[edge["node"]["name"]] += edge["size"]
    total = sum(langs.values()) or 1
    top = [(name, round(100 * size / total, 1)) for name, size in langs.most_common(5)]
    rest = round(100 - sum(p for _, p in top), 1)
    if rest > 0.1 and len(langs) > 5:
        top.append(("Outras", rest))

    return {
        "updated": dt.date.today().isoformat(),
        "since": int(user["createdAt"][:4]),
        "repos": repos["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos["nodes"]),
        "followers": user["followers"]["totalCount"],
        "commits": contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"],
        "prs": contrib["totalPullRequestContributions"],
        "contributions": contrib["contributionCalendar"]["totalContributions"],
        "languages": top,
        "weeks": [
            [(d["date"], d["contributionLevel"]) for d in w["contributionDays"]]
            for w in contrib["contributionCalendar"]["weeks"]
        ],
    }


def load_stats():
    token = os.environ.get("CARD_TOKEN")
    if token:
        stats = fetch_stats(token)
        STATS_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n")
        return stats
    if STATS_FILE.exists():
        return json.loads(STATS_FILE.read_text())
    return {"since": 2019, "languages": [], "weeks": []}


def empty_weeks():
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks = []
    for w in range(53):
        days = [start + dt.timedelta(days=w * 7 + d) for d in range(7)]
        weeks.append([(d.isoformat(), "NONE") for d in days if d <= today])
    return weeks


# ------------------------------------------------------------------ desenho
def t(x, y, s, size=12, fill=TEXT, weight=400, anchor="start", ls=0, extra=""):
    lsattr = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{lsattr}{extra}>{s}</text>')


def tw(s, size, ls=0):
    return len(s) * (size * CW + ls) - ls


CLOUD = "M7 18.5h10.2a4.3 4.3 0 0 0 .5-8.57A6.2 6.2 0 0 0 5.9 9.3 4.6 4.6 0 0 0 7 18.5z"


def icon(name, x, y, size, color):
    s = size / 24
    if name == "cloud":
        return (f'<path transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" fill="none" stroke="{color}" '
                f'stroke-width="{1.6 / s:.2f}" stroke-linejoin="round" d="{CLOUD}"/>')
    return f'<path transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" fill="{color}" d="{ICONS[name]}"/>'


def fmt(n):
    if n is None:
        return "…"
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def box(x, y, w, h, num, title, note=""):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL}" fill-opacity=".92" stroke="{FRAME}"/>'
    out += f'<rect x="{x + 12}" y="{y + 11}" width="28" height="18" rx="4" fill="none" stroke="{AMBER}"/>'
    out += t(x + 26, y + 24, num, 10, AMBER, 700, "middle")
    out += t(x + 50, y + 24.5, title, 10.5, TEXT, 700, ls=2)
    if note:
        out += t(x + w - 14, y + 24, note, 9.5, MUTED, anchor="end", ls=0.5)
    return out


STYLE = """
  .blink { animation: blink 1.1s steps(1) infinite; }
  .spin { transform-box: fill-box; transform-origin: center; animation: spin 24s linear infinite; }
  .spin-rev { transform-box: fill-box; transform-origin: center; animation: spin 40s linear infinite reverse; }
  .pulse { transform-box: fill-box; transform-origin: center; animation: pulse 2s ease-out infinite; }
  .scan { animation: scan 9s linear infinite; }
  @keyframes blink { 50% { opacity: 0; } }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes pulse { 0% { transform: scale(1); opacity: .9; } 100% { transform: scale(3.2); opacity: 0; } }
  @keyframes scan { from { transform: translateX(0); } to { transform: translateX(var(--scan)); } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
"""


def header(p, s):
    b = t(40, 38, f"// {LOGIN} / README.md", 10.5, MUTED, ls=1)
    b += t(800, 38, f"REV {s.get('updated', '…')}  ·  atualizado todo dia", 10.5, MUTED, anchor="end", ls=1)

    b += t(40, 88, p["name"], 40, TEXT, 800, ls=3)
    role = p["role"]
    b += t(40, 118, role, 16, CYAN, 600)
    if p["company"]:
        x = 40 + tw(role + " ", 16)
        b += t(x, 118, "@", 16, AMBER, 700) + t(x + tw("@ ", 16), 118, p["company"], 16, CYAN, 600)
    b += t(40, 146, "&gt;&gt;&gt;", 13, AMBER, 700) + t(74, 146, p["tagline"], 13, MUTED)
    b += f'<rect class="blink" x="{74 + tw(p["tagline"], 13) + 6:.0f}" y="135" width="8" height="14" fill="{AMBER}"/>'

    years = dt.date.today().year - s.get("since", 2019)
    rows = [("LOCAL", p["location"]), ("EMPRESA", p["company"]),
            ("NO GITHUB", f"desde {s.get('since', 2019)} ({years} anos)"), ("STATUS", p["status"])]
    for i, (k, v) in enumerate(rows):
        y = 70 + i * 23
        b += t(446, y, k, 9, CYAN, 700, ls=1)
        if k == "STATUS":
            b += f'<circle class="pulse" cx="530" cy="{y - 3.5}" r="3.5" fill="{AMBER}"/>'
            b += f'<circle cx="530" cy="{y - 3.5}" r="3.5" fill="{AMBER}"/>'
            b += t(540, y, v, 11, TEXT)
        else:
            b += t(524, y, v, 11, TEXT)

    cx, cy = 758, 104
    b += f'<line x1="{cx - 54}" y1="{cy}" x2="{cx + 58}" y2="{cy}" stroke="{DIM}" stroke-dasharray="2 5"/>'
    b += f'<line x1="{cx}" y1="{cy - 58}" x2="{cx}" y2="{cy + 60}" stroke="{DIM}" stroke-dasharray="2 5"/>'
    b += f'<circle class="spin" cx="{cx}" cy="{cy}" r="48" fill="none" stroke="{CYAN}" stroke-width="1.3" stroke-dasharray="3 8"/>'
    b += f'<circle class="spin-rev" cx="{cx}" cy="{cy}" r="38" fill="none" stroke="{AMBER}" stroke-opacity=".6" stroke-dasharray="30 10 4 10"/>'
    b += f'<circle cx="{cx}" cy="{cy}" r="29" fill="{PANEL}" stroke="{FRAME}"/>'
    b += icon("python", cx - 17, cy - 17, 34, AMBER)
    b += (f'<circle r="3.5" fill="{CYAN}"><animateMotion dur="8s" repeatCount="indefinite" '
          f'path="M{cx - 48} {cy}a48 48 0 1 0 96 0a48 48 0 1 0 -96 0"/></circle>')
    return b


def whoami(p, x, y, w, h):
    b = box(x, y, w, h, "01", "WHOAMI")
    b += t(x + 16, y + 56, "Oi! Sou o Leandro.", 14, AMBER, 700)
    for i, line in enumerate(p["about"]):
        b += t(x + 16, y + 82 + i * 18, line, 12, TEXT)
    b += f'<line x1="{x + 16}" y1="{y + 172}" x2="{x + w - 16}" y2="{y + 172}" stroke="{FRAME}" stroke-dasharray="3 4"/>'
    for i, item in enumerate(p["focus"]):
        yy = y + 194 + i * 18
        b += t(x + 16, yy, "▸", 11, AMBER, 700) + t(x + 32, yy, item, 11.5, CYAN)
    return b


def stack(p, x, y, w, h):
    b = box(x, y, w, h, "02", "STACK")
    sx = x + 22
    top, step = y + 56, 40
    rows = p["stack"]
    bottom = top + step * (len(rows) - 1)
    b += f'<line x1="{sx}" y1="{top}" x2="{sx}" y2="{bottom}" stroke="{CYAN}" stroke-opacity=".5"/>'
    b += (f'<circle r="3" fill="{AMBER}"><animateMotion dur="3.2s" repeatCount="indefinite" '
          f'path="M{sx} {top}V{bottom}"/></circle>')
    for i, (label, icons, note) in enumerate(rows):
        cy = top + i * step
        color = AMBER if label == "API" else CYAN
        if i:
            b += f'<line x1="{x + 36}" y1="{cy - step / 2}" x2="{x + w - 14}" y2="{cy - step / 2}" stroke="{FRAME}" stroke-dasharray="3 4"/>'
        b += f'<circle cx="{sx}" cy="{cy}" r="4" fill="{PANEL}" stroke="{color}" stroke-width="1.5"/>'
        b += t(x + 38, cy + 3.5, label, 9.5, color, 700, ls=1.5)
        for k, name in enumerate(icons):
            b += icon(name, x + 112 + k * 30, cy - 10, 20, color)
        if note:
            b += t(x + 112 + len(icons) * 30 - 2, cy + 3.5, note, 10, TEXT)
    return b


def telemetry(s, x, y, w, h):
    b = box(x, y, w, h, "03", "TELEMETRIA", "github ao vivo")
    years = dt.date.today().year - s.get("since", 2019)
    cells = [("REPOS", s.get("repos")), ("ESTRELAS", s.get("stars")), ("SEGUIDORES", s.get("followers")),
             ("COMMITS/ANO", s.get("commits")), ("PRS/ANO", s.get("prs")), ("ANOS NO GH", years)]
    cw = (w - 24) / 3
    for i, (label, val) in enumerate(cells):
        cx = x + 14 + (i % 3) * cw
        cy = y + 62 + (i // 3) * 46
        b += t(cx, cy, fmt(val), 19, AMBER if i == 3 else TEXT, 800)
        b += t(cx, cy + 15, label, 8.5, MUTED, ls=0.5)

    b += t(x + 14, y + 162, "LINGUAGENS", 9, CYAN, 700, ls=1.5)
    langs = s.get("languages") or []
    bx, by, bw = x + 14, y + 170, w - 28
    b += f'<clipPath id="bar"><rect x="{bx}" y="{by}" width="{bw}" height="7" rx="3.5"/></clipPath>'
    b += f'<rect x="{bx}" y="{by}" width="{bw}" height="7" rx="3.5" fill="{LEVELS["NONE"]}"/>'
    cur = bx
    for i, (_, pct) in enumerate(langs):
        seg = bw * pct / 100
        b += f'<rect clip-path="url(#bar)" x="{cur:.1f}" y="{by}" width="{seg:.1f}" height="7" fill="{LANG_COLORS[i]}"/>'
        cur += seg
    if not langs:
        b += t(x + 14, y + 200, "sincronizando…", 10.5, MUTED)
    colw = (w - 28) / 2
    for i, (name, pct) in enumerate(langs[:6]):
        lx = x + 14 + (i % 2) * colw
        ly = y + 196 + (i // 2) * 17
        name = name if len(name) <= 11 else name.split()[0][:11]
        b += f'<circle cx="{lx + 4}" cy="{ly - 3.5}" r="3.5" fill="{LANG_COLORS[i]}"/>'
        b += t(lx + 13, ly, name, 10.5, TEXT)
        b += t(lx + colw - 10, ly, f"{pct:.0f}%", 10, MUTED, anchor="end")
    return b


def heatmap(s, x, y, w, h):
    total = s.get("contributions")
    note = f"{fmt(total)} contribuições nos últimos 12 meses" if total is not None else "sincronizando…"
    b = box(x, y, w, h, "04", "CONTRIBUIÇÕES", note)
    weeks = s.get("weeks") or empty_weeks()
    cell, gap = 10, 3
    gw = len(weeks) * (cell + gap) - gap
    gx, gy = x + (w - gw) / 2 + 10, y + 58
    last_month = None
    for wi, week in enumerate(weeks):
        wx = gx + wi * (cell + gap)
        first = dt.date.fromisoformat(week[0][0])
        if first.month != last_month and first.day <= 7 and wi < len(weeks) - 2:
            b += t(wx, gy - 7, MONTHS[first.month - 1], 8.5, MUTED)
            last_month = first.month
        for date, level in week:
            dy = (dt.date.fromisoformat(date).weekday() + 1) % 7
            b += (f'<rect x="{wx:.1f}" y="{gy + dy * (cell + gap)}" width="{cell}" height="{cell}" rx="2" '
                  f'fill="{LEVELS.get(level, LEVELS["NONE"])}"/>')
    for d, label in [(1, "seg"), (3, "qua"), (5, "sex")]:
        b += t(gx - 8, gy + d * (cell + gap) + 8, label, 8, MUTED, anchor="end")
    gh = 7 * (cell + gap) - gap
    b += (f'<rect class="scan" style="--scan:{gw:.0f}px" x="{gx - 1:.1f}" y="{gy - 3}" width="2" '
          f'height="{gh + 6}" fill="{CYAN}" opacity=".45"/>')
    return b


def render():
    p, s = PROFILE, load_stats()
    W, H = 840, 630
    body = header(p, s)
    top, bh = 168, 250
    cw, gap = 252, 14
    body += whoami(p, 28, top, cw, bh)
    body += stack(p, 28 + cw + gap, top, cw, bh)
    body += telemetry(s, 28 + 2 * (cw + gap), top, cw, bh)
    body += heatmap(s, 28, top + bh + 12, 784, 162)
    fy = H - 22
    body += t(40, fy, "&gt;&gt;&gt; import this", 10.5, AMBER, 700)
    body += t(40 + tw(">>> import this", 10.5) + 14, fy, p["zen"], 10.5, MUTED)
    body += t(800, fy, f"PROJETO {LOGIN}  ·  ESCALA 1:1  ·  FL. 01/01", 10, MUTED, anchor="end", ls=1)

    ticks = ""
    m, L = 12, 12
    for cx, cy, dx, dy in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        ticks += f'<path d="M{cx} {cy + dy * L}V{cy}H{cx + dx * L}" fill="none" stroke="{CYAN}" stroke-opacity=".55"/>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<style>{STYLE}</style>
<defs>
  <pattern id="gmin" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M10 0H0V10" fill="none" stroke="{GRID_MINOR}" stroke-width=".6"/></pattern>
  <pattern id="gmaj" width="50" height="50" patternUnits="userSpaceOnUse"><rect width="50" height="50" fill="url(#gmin)"/><path d="M50 0H0V50" fill="none" stroke="{GRID_MAJOR}"/></pattern>
  <clipPath id="clip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{BG}" stroke="{FRAME}"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="url(#gmaj)" clip-path="url(#clip)" opacity=".9"/>
{ticks}
{body}
</svg>
'''
    (ASSETS / "card.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    render()
