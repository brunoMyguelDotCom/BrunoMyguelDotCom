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


def github(path):
    r = session.get(
        "https://api.github.com" + path,
        timeout=30,
    )

    r.raise_for_status()

    return r.json()


def get_stats():
    user = github(f"/users/{USERNAME}")

    repos = []
    page = 1

    while True:
        batch = github(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    # Extensões de arquivos que queremos contar como código
    CODE_EXTENSIONS = {
        ".py", ".java", ".js", ".ts", ".tsx", ".jsx", ".html", ".css",
        ".sql", ".sh", ".yml", ".yaml", ".json", ".cpp", ".c", ".cs",
        ".go", ".rs", ".php", ".rb", ".swift", ".kt"
    }
    # Pastas que devem ser ignoradas
    IGNORE_FOLDERS = {
        "node_modules", ".git", "venv", ".venv", "__pycache__",
        "dist", "build", "target", ".idea", ".vscode"
    }

    total_lines = 0
    for repo in repos:
        repo_name = repo["name"]
        try:
            # Tenta buscar a árvore recursiva da branch padrão
            default_branch = repo.get("default_branch", "main")
            tree = github(f"/repos/{USERNAME}/{repo_name}/git/trees/{default_branch}?recursive=1")

            for item in tree.get("tree", []):
                if item["type"] == "blob":
                    path = item["path"]
                    # Ignora arquivos em pastas proibidas
                    if any(folder in path.split("/") for folder in IGNORE_FOLDERS):
                        continue

                    # Ignora arquivos que não tenham as extensões de código
                    if not any(path.endswith(ext) for ext in CODE_EXTENSIONS):
                        continue

                    # Pega o conteúdo do arquivo para contar as linhas
                    content_data = github(f"/repos/{USERNAME}/{repo_name}/contents/{path}")
                    import base64
                    encoded_content = content_data.get("content", "")
                    if encoded_content:
                        decoded_content = base64.b64decode(encoded_content).decode("utf-8", errors="ignore")
                        total_lines += len(decoded_content.splitlines())
        except Exception:
            continue

    commits = "n/a"

    try:
        r = session.get(
            "https://api.github.com/search/commits",
            params={
                "q": f"author:{USERNAME}",
                "per_page": 1,
            },
            timeout=30,
        )

        if r.ok:
            commits = r.json().get("total_count", 0)

    except requests.RequestException:
        pass

    return {
        "repos": user.get("public_repos", 0),
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

    # Converte a imagem para escala de cinza.
    # Isso gera um único valor de luminosidade por pixel.
    image = Image.open(path).convert("L")

    # Caracteres de terminal são mais altos que largos.
    # Reduzimos a altura para evitar que o rosto fique esticado.
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

    except Exception:
        stats = {
            "repos": "n/a",
            "lines": "n/a",
            "stars": "n/a",
            "commits": "n/a",
        }

    # Cálculo de experiência e bacharelado
    # Definido para resultar em 8 anos e 5 meses em Setembro de 2026
    start_it = datetime(2018, 4, 1)
    # Bacharelado começou em Fevereiro de 2025
    start_deg = datetime(2025, 2, 1)
    now = datetime.now()

    diff_it = now - start_it
    years_it = diff_it.days // 365
    months_it = (diff_it.days % 365) // 30

    diff_deg = now - start_deg
    years_deg = diff_deg.days // 365
    months_deg = (diff_deg.days % 365) // 30

    it_text = f"{years_it} anos e {months_it} meses de experiência na área da informática"
    deg_text = f"{years_deg} anos e {months_deg} meses de bacharelado de Eng. de Software (4 anos)"

    avatar_lines = ascii_avatar()


    # Cálculo dinâmico do tamanho do avatar
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
        "<svg "
        'xmlns="http://www.w3.org/2000/svg" '
        'width="1200" '
        'height="590" '
        'viewBox="0 0 1100 590">',
        f"<rect " f'width="1100" ' f'height="590" ' f'rx="18" ' f'fill="{bg}"/>',
        f"<rect "
        f'x="24" '
        f'y="24" '
        f'width="1052" '
        f'height="542" '
        f'rx="12" '
        f'fill="{panel}" '
        f'stroke="{border}"/>',
        f"<text "
        f'x="52" '
        f'y="67" '
        f'fill="{muted}" '
        f'font-family="monospace" '
        f'font-size="15">'
        f"Bem vindo ao meu github!"
        f"</text>",
        f"<text "
        f'x="52" '
        f'y="104" '
        f'fill="{accent}" '
        f'font-family="monospace" '
        f'font-size="30" '
        f'font-weight="700">'
        f"{NAME}"
        f"</text>",
        f"<text "
        f'x="52" '
        f'y="133" '
        f'fill="{fg}" '
        f'font-family="monospace" '
        f'font-size="16">'
        f"{esc(TITLE)}"
        f"</text>",
        f"<line "
        f'x1="52" '
        f'y1="158" '
        f'x2="1048" '
        f'y2="158" '
        f'stroke="{border}"/>',
        f"<text "
        f'x="52" '
        f'y="190" '
        f'fill="{muted}" '
        f'font-family="monospace" '
        f'font-size="14">'
        f"profile"
        f"</text>",
        f"<text x='52' y='218' fill='{fg}' font-family='monospace' font-size='16' font-weight='700'>Cargo:</text>",
        f"<text x='120' y='218' fill='{fg}' font-family='monospace' font-size='16'>{esc(ROLE)}</text>",
        f"<text x='52' y='246' fill='{fg}' font-family='monospace' font-size='16' font-weight='700'>Stack:</text>",
        f"<text x='120' y='246' fill='{fg}' font-family='monospace' font-size='16'>{esc(BACKEND)} | {esc(DATA)}</text>",
        f"<text x='52' y='274' fill='{fg}' font-family='monospace' font-size='16' font-weight='700'>Infra:</text>",
        f"<text x='120' y='274' fill='{fg}' font-family='monospace' font-size='16'>{esc(INFRA)}</text>",
        f"<text x='52' y='302' fill='{fg}' font-family='monospace' font-size='16' font-weight='700'>Sistemas:</text>",
        f"<text x='144' y='302' fill='{fg}' font-family='monospace' font-size='16'>{esc(SYSTEMS)}</text>",
        f"<text x='52' y='340' fill='{fg}' font-family='monospace' font-size='16' font-weight='700'>Experiência:</text>",
        f"<text x='174' y='340' fill='{fg}' font-family='monospace' font-size='16'>{esc(it_text)}</text>",
        f"<text x='52' y='368' fill='{fg}' font-family='monospace' font-size='16' font-weight='700'>Formação:</text>",
        f"<text x='150' y='368' fill='{fg}' font-family='monospace' font-size='16'>{esc(deg_text)}</text>",
        # Caixa do avatar ASCII
        # (Removido o bloco de fundo do avatar)
    ]

    # Renderiza a imagem como ASCII dentro do SVG
    current_y = text_y

    for line in avatar_lines:
        lines.append(
            f"<text "
            f'x="{text_x}" '
            f'y="{current_y}" '
            f'fill="{fg}" '
            f'font-family="monospace" '
            f'font-size="{font_size}" '
            f'xml:space="preserve">'
            f"{esc(line)}"
            f"</text>"
        )

        current_y += line_height

    lines += [
        f"<text "
        f'x="52" '
        f'y="456" '
        f'fill="{muted}" '
        f'font-family="monospace" '
        f'font-size="14">'
        f"github stats:"
        f"</text>",
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
                f"<text "
                f'x="{x}" '
                f'y="487" '
                f'fill="{muted}" '
                f'font-family="monospace" '
                f'font-size="13">'
                f"{label}"
                f"</text>",
                f"<text "
                f'x="{x}" '
                f'y="520" '
                f'fill="{accent}" '
                f'font-family="monospace" '
                f'font-size="25" '
                f'font-weight="700">'
                f"{esc(value)}"
                f"</text>",
            ]
        )

    lines += [
        f"<text "
        f'x="52" '
        f'y="550" '
        f'fill="{muted}" '
        f'font-family="monospace" '
        f'font-size="14" '
        f'font-style="italic">'
        f"onde o código toca o metal."
        f"</text>",
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
