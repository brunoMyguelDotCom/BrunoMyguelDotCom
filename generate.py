import base64
import os
from datetime import datetime
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

BACKEND = "Python · Pandas · PySpark"
DATA = "Java · Spring"
INFRA = "AWS · Terraform · PostgreSQL · ClickHouse"
SYSTEMS = "Linux · macOS · Windows"

ASCII_CHARS = "@%#*+=-:. "


session = requests.Session()

session.headers.update(
    {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
)

if TOKEN:
    session.headers["Authorization"] = f"Bearer {TOKEN}"
else:
    print("AVISO: GITHUB_TOKEN não foi encontrado.")


def github(path):
    response = session.get(
        "https://api.github.com" + path,
        timeout=30,
    )

    if not response.ok:
        print(f"GitHub API error: {response.status_code}")
        print(f"URL: {response.url}")
        print(f"Response: {response.text[:1000]}")

    response.raise_for_status()

    return response.json()


def get_stats():
    user = github(f"/users/{USERNAME}")

    repos = []
    page = 1

    while True:
        batch = github(
            f"/users/{USERNAME}/repos" f"?per_page=100" f"&page={page}" f"&type=owner"
        )

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    CODE_EXTENSIONS = {
        ".py",
        ".java",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".html",
        ".css",
        ".sql",
        ".sh",
        ".yml",
        ".yaml",
        ".json",
        ".cpp",
        ".c",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
    }

    IGNORE_FOLDERS = {
        "node_modules",
        ".git",
        "venv",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        "target",
        ".idea",
        ".vscode",
    }

    total_lines = 0

    for repo in repos:
        repo_name = repo["name"]

        try:
            default_branch = repo.get(
                "default_branch",
                "main",
            )

            tree = github(
                f"/repos/{USERNAME}/{repo_name}"
                f"/git/trees/{default_branch}?recursive=1"
            )

            for item in tree.get("tree", []):
                if item["type"] != "blob":
                    continue

                path = item["path"]

                if any(folder in path.split("/") for folder in IGNORE_FOLDERS):
                    continue

                if not any(path.endswith(ext) for ext in CODE_EXTENSIONS):
                    continue

                try:
                    content_data = github(
                        f"/repos/{USERNAME}/{repo_name}" f"/contents/{path}"
                    )

                    encoded_content = content_data.get(
                        "content",
                        "",
                    )

                    if not encoded_content:
                        continue

                    decoded_content = base64.b64decode(encoded_content).decode(
                        "utf-8",
                        errors="ignore",
                    )

                    total_lines += len(decoded_content.splitlines())

                except Exception as error:
                    print(f"Erro ao ler {repo_name}/{path}: " f"{error}")

        except Exception as error:
            print(f"Erro ao processar repositório " f"{repo_name}: {error}")

            continue

    commits = "n/a"

    try:
        response = session.get(
            "https://api.github.com/search/commits",
            params={
                "q": f"author:{USERNAME}",
                "per_page": 1,
            },
            timeout=30,
        )

        if response.ok:
            commits = response.json().get(
                "total_count",
                0,
            )
        else:
            print(f"Erro ao buscar commits: " f"{response.status_code}")
            print(response.text[:1000])

    except requests.RequestException as error:
        print(f"Erro ao buscar commits: {error}")

    return {
        "repos": len(repos),
        "lines": total_lines,
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
        (160, 70),
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
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(dark):
    bg = "#0b0f14" if dark else "#f5f5f5"
    panel = "#111820" if dark else "#ffffff"
    fg = "#d7dee7" if dark else "#1f2933"
    muted = "#7f8b99" if dark else "#68737f"
    accent = "#8ab4f8" if dark else "#245ea8"
    border = "#26313d" if dark else "#d7dde4"

    try:
        stats = get_stats()

    except Exception as error:
        print(f"Erro ao coletar estatísticas: {error}")

        stats = {
            "repos": "n/a",
            "lines": "n/a",
            "stars": "n/a",
            "commits": "n/a",
        }

    start_it = datetime(2018, 4, 1)
    start_deg = datetime(2025, 2, 1)

    now = datetime.now()

    diff_it = now - start_it

    years_it = diff_it.days // 365
    months_it = (diff_it.days % 365) // 30

    diff_deg = now - start_deg

    years_deg = diff_deg.days // 365
    months_deg = (diff_deg.days % 365) // 30

    it_text = (
        f"{years_it} anos e "
        f"{months_it} meses de experiência "
        f"na área da informática"
    )

    deg_text = (
        f"{years_deg} anos e "
        f"{months_deg} meses de bacharelado "
        f"de Eng. de Software (4 anos)"
    )

    avatar_lines = ascii_avatar()

    max_line_length = max(len(line) for line in avatar_lines) if avatar_lines else 0

    num_lines = len(avatar_lines)

    font_size = 3.5
    line_height = 3.5
    char_width = font_size * 0.6

    avatar_width_px = max_line_length * char_width

    avatar_height_px = num_lines * line_height

    padding = 20

    box_width = avatar_width_px + (padding * 2)

    box_height = avatar_height_px + (padding * 2)

    box_x = 710
    box_y = 176

    text_x = box_x + padding
    text_y = box_y + padding

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            "<svg "
            'xmlns="http://www.w3.org/2000/svg" '
            'width="1200" '
            'height="590" '
            'viewBox="0 0 1100 590">'
        ),
        ("<rect " 'width="1100" ' 'height="590" ' 'rx="18" ' f'fill="{bg}"/>'),
        (
            "<rect "
            'x="24" '
            'y="24" '
            'width="1052" '
            'height="542" '
            'rx="12" '
            f'fill="{panel}" '
            f'stroke="{border}"/>'
        ),
        (
            "<text "
            'x="52" '
            'y="67" '
            f'fill="{muted}" '
            'font-family="monospace" '
            'font-size="15">'
            "Bem vindo ao meu github!"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="104" '
            f'fill="{accent}" '
            'font-family="monospace" '
            'font-size="30" '
            'font-weight="700">'
            f"{NAME}"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="133" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f"{esc(TITLE)}"
            "</text>"
        ),
        (
            "<line "
            'x1="52" '
            'y1="158" '
            'x2="1048" '
            'y2="158" '
            f'stroke="{border}"/>'
        ),
        (
            "<text "
            'x="52" '
            'y="190" '
            f'fill="{muted}" '
            'font-family="monospace" '
            'font-size="14">'
            "profile"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="218" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            "Cargo:"
            "</text>"
        ),
        (
            "<text "
            'x="120" '
            'y="218" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f"{esc(ROLE)}"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="246" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            "Stack:"
            "</text>"
        ),
        (
            "<text "
            'x="120" '
            'y="246" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f"{esc(BACKEND)} | {esc(DATA)}"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="274" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            "Infra:"
            "</text>"
        ),
        (
            "<text "
            'x="120" '
            'y="274" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f"{esc(INFRA)}"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="302" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            "Sistemas:"
            "</text>"
        ),
        (
            "<text "
            'x="144" '
            'y="302" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f"{esc(SYSTEMS)}"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="340" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            "Experiência:"
            "</text>"
        ),
        (
            "<text "
            'x="174" '
            'y="340" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f"{esc(it_text)}"
            "</text>"
        ),
        (
            "<text "
            'x="52" '
            'y="368" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            "Formação:"
            "</text>"
        ),
        (
            "<text "
            'x="150" '
            'y="368" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f"{esc(deg_text)}"
            "</text>"
        ),
    ]

    current_y = text_y

    for line in avatar_lines:
        lines.append(
            (
                "<text "
                f'x="{text_x}" '
                f'y="{current_y}" '
                f'fill="{fg}" '
                'font-family="monospace" '
                f'font-size="{font_size}" '
                'xml:space="preserve">'
                f"{esc(line)}"
                "</text>"
            )
        )

        current_y += line_height

    lines += [
        (
            "<text "
            'x="52" '
            'y="456" '
            f'fill="{muted}" '
            'font-family="monospace" '
            'font-size="14">'
            "github stats:"
            "</text>"
        ),
    ]

    stats_rows = [
        ("repositories", stats["repos"], 52),
        ("commits", stats["commits"], 280),
        ("stars", stats["stars"], 510),
        ("lines of code", stats["lines"], 740),
    ]

    for label, value, x in stats_rows:
        lines.extend(
            [
                (
                    "<text "
                    f'x="{x}" '
                    'y="487" '
                    f'fill="{muted}" '
                    'font-family="monospace" '
                    'font-size="13">'
                    f"{label}"
                    "</text>"
                ),
                (
                    "<text "
                    f'x="{x}" '
                    'y="520" '
                    f'fill="{accent}" '
                    'font-family="monospace" '
                    'font-size="25" '
                    'font-weight="700">'
                    f"{esc(value)}"
                    "</text>"
                ),
            ]
        )

    lines += [
        (
            "<text "
            'x="52" '
            'y="550" '
            f'fill="{muted}" '
            'font-family="monospace" '
            'font-size="14" '
            'font-style="italic">'
            "onde o código toca o metal."
            "</text>"
        ),
        "</svg>",
    ]

    return "\n".join(lines)


def main():
    ASSETS.mkdir(exist_ok=True)

    (ASSETS / "dark_mode.svg").write_text(
        build_svg(True),
        encoding="utf-8",
    )

    (ASSETS / "light_mode.svg").write_text(
        build_svg(False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
