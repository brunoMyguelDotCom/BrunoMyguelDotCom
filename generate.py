import os
from pathlib import Path
import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

USERNAME = os.getenv("GITHUB_USERNAME", "brunoMyguelDotCom")
TOKEN = os.getenv("GITHUB_TOKEN", "")

NAME = "Bruno Myguel"
TITLE = "ENGENHARIA DE SOFTWARE & ENGENHARIA DE DADOS"
ROLE = "Estagiário de Engenharia de Dados na Crefaz"
BACKEND = "Java · Spring · Python · Pandas · PySpark"
INFRA = "AWS · Terraform · PostgreSQL"
SYSTEMS = "Linux · macOS · Windows"

ASCII_CHARS = "@%#*+=-:. "

session = requests.Session()
session.headers.update({
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})
if TOKEN:
    session.headers["Authorization"] = f"Bearer {TOKEN}"


def github(path):
    r = session.get("https://api.github.com" + path, timeout=30)
    r.raise_for_status()
    return r.json()


def get_stats():
    user = github(f"/users/{USERNAME}")

    repos = []
    page = 1
    while True:
        batch = github(
            f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner"
        )
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    commits = "n/a"
    try:
        r = session.get(
            "https://api.github.com/search/commits",
            params={"q": f"author:{USERNAME}", "per_page": 1},
            timeout=30,
        )
        if r.ok:
            commits = r.json().get("total_count", 0)
    except requests.RequestException:
        pass

    return {
        "repos": user.get("public_repos", 0),
        "lines": "n/a",
        "stars": stars,
        "commits": commits,
    }


def ascii_avatar():
    path = ASSETS / "avatar.jpg"

    if not path.exists():
        return [
            "   +----------------+",
            "   |                |",
            "   |  avatar.jpg    |",
            "   |                |",
            "   |  not found     |",
            "   |                |",
            "   +----------------+",
        ]

    image = Image.open(path).convert("L")
    image = ImageOps.fit(
        image,
        (30, 20),
        method=Image.Resampling.LANCZOS,
    )

    lines = []
    for y in range(image.height):
        line = ""
        for x in range(image.width):
            value = image.getpixel((x, y))
            index = int(value / 255 * (len(ASCII_CHARS) - 1))
            line += ASCII_CHARS[index]
        lines.append(line.rstrip())

    return lines


def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(dark):
    bg = "#0b0f14" if dark else "#f5f5f5"
    panel = "#111820" if dark else "#ffffff"
    fg = "#d7dee7" if dark else "#1f2933"
    muted = "#7f8b99" if dark else "#68737f"
    accent = "#8ab4f8" if dark else "#245ea8"
    border = "#26313d" if dark else "#d7dde4"

    try:
        stats = get_stats()
    except Exception:
        stats = {
            "repos": "n/a",
            "lines": "n/a",
            "stars": "n/a",
            "commits": "n/a",
        }

    avatar = ascii_avatar()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="590" viewBox="0 0 1100 590">',
        f'<rect width="1100" height="590" rx="18" fill="{bg}"/>',
        f'<rect x="24" y="24" width="1052" height="542" rx="12" fill="{panel}" stroke="{border}"/>',

        f'<text x="52" y="67" fill="{muted}" font-family="monospace" font-size="15">System initialized. Welcome, {NAME}.</text>',
        f'<text x="52" y="104" fill="{accent}" font-family="monospace" font-size="30" font-weight="700">{NAME}</text>',
        f'<text x="52" y="133" fill="{fg}" font-family="monospace" font-size="16">{esc(TITLE)}</text>',
        f'<line x1="52" y1="158" x2="1048" y2="158" stroke="{border}"/>',

        f'<text x="52" y="190" fill="{muted}" font-family="monospace" font-size="14">profile</text>',
        f'<text x="52" y="218" fill="{fg}" font-family="monospace" font-size="16">experiência   {esc(ROLE)}</text>',
        f'<text x="52" y="246" fill="{fg}" font-family="monospace" font-size="16">stack        {esc(BACKEND)}</text>',
        f'<text x="52" y="274" fill="{fg}" font-family="monospace" font-size="16">infra        {esc(INFRA)}</text>',
        f'<text x="52" y="302" fill="{fg}" font-family="monospace" font-size="16">sistemas    {esc(SYSTEMS)}</text>',
        f'<text x="52" y="330" fill="{fg}" font-family="monospace" font-size="16">especialidade  resolução de problemas complexos</text>',
        f'<text x="52" y="358" fill="{fg}" font-family="monospace" font-size="16">histórico    8 anos em assistência técnica de hardware</text>',
        f'<text x="52" y="386" fill="{fg}" font-family="monospace" font-size="16">formação    Engenharia de Software — UniCV</text>',
        f'<text x="52" y="414" fill="{fg}" font-family="monospace" font-size="16">            Certificações em Backend &amp; Sistemas Linux — Alura</text>',

        f'<rect x="850" y="176" width="196" height="250" rx="8" fill="{bg}" stroke="{border}"/>',
        f'<text x="866" y="198" fill="{muted}" font-family="monospace" font-size="11">avatar</text>',
    ]

    y = 216
    for line in avatar[:20]:
        lines.append(
            f'<text x="866" y="{y}" fill="{fg}" font-family="monospace" font-size="7">{esc(line)}</text>'
        )
        y += 9

    lines += [
        f'<text x="52" y="456" fill="{muted}" font-family="monospace" font-size="14">github stats</text>',
    ]

    stats_rows = [
        ("repositories", stats["repos"], 52),
        ("commits", stats["commits"], 280),
        ("stars", stats["stars"], 510),
        ("lines of code", stats["lines"], 740),
    ]

    for label, value, x in stats_rows:
        lines.extend([
            f'<text x="{x}" y="487" fill="{muted}" font-family="monospace" font-size="13">{label}</text>',
            f'<text x="{x}" y="520" fill="{accent}" font-family="monospace" font-size="25" font-weight="700">{esc(value)}</text>',
        ])

    lines += [
        f'<text x="52" y="550" fill="{muted}" font-family="monospace" font-size="13">onde o código toca o metal.</text>',
        "</svg>",
    ]

    return "\n".join(lines)


def main():
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "dark_mode.svg").write_text(build_svg(True), encoding="utf-8")
    (ASSETS / "light_mode.svg").write_text(build_svg(False), encoding="utf-8")


if __name__ == "__main__":
    main()
