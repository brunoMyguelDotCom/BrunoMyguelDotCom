import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STATS_FILE = ASSETS / "stats.json"

USERNAME = os.getenv(
    "GITHUB_USERNAME",
    "brunoMyguelDotCom",
)

TOKEN = os.getenv("GITHUB_TOKEN", "")

NAME = "Bruno Myguel"
TITLE = "ENGENHARIA DE SOFTWARE & ENGENHARIA DE DADOS"
ROLE = "Estagiário de Engenharia de Dados na Crefaz"

BACKEND = "Python · Pandas · PySpark"
DATA = "Java · Spring"
INFRA = "AWS · Terraform · PostgreSQL · ClickHouse"
SYSTEMS = "Linux · macOS · Windows"

ASCII_CHARS = "@%#*+=-:. "


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


# Valores usados somente quando ainda não existe
# nenhum valor real salvo anteriormente.
DEFAULT_STATS = {
    "repos": 32,
    "commits": 0,
    "stars": 0,
    "lines": 8274,
}


session = requests.Session()

session.headers.update(
    {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
)


if TOKEN:
    session.headers["Authorization"] = (
        f"Bearer {TOKEN}"
    )
else:
    print(
        "AVISO: GITHUB_TOKEN não foi encontrado."
    )


def github(path):
    response = session.get(
        "https://api.github.com" + path,
        timeout=30,
    )

    if not response.ok:
        print(
            f"GitHub API error: "
            f"{response.status_code}"
        )

        print(
            f"URL: {response.url}"
        )

        print(
            f"Response: "
            f"{response.text[:1000]}"
        )

    response.raise_for_status()

    return response.json()


def load_saved_stats():
    """
    Carrega o último conjunto de estatísticas
    que conseguiu ser obtido com sucesso.
    """

    if not STATS_FILE.exists():
        print(
            "stats.json não existe."
        )

        return DEFAULT_STATS.copy()

    try:
        content = STATS_FILE.read_text(
            encoding="utf-8"
        )

        saved = json.loads(content)

        stats = {}

        for key, default in DEFAULT_STATS.items():
            value = saved.get(
                key,
                default,
            )

            if isinstance(value, int):
                stats[key] = value
            else:
                stats[key] = default

        print(
            "Últimas estatísticas salvas:"
        )

        print(
            f"Repositories: "
            f"{stats['repos']}"
        )

        print(
            f"Commits: "
            f"{stats['commits']}"
        )

        print(
            f"Stars: "
            f"{stats['stars']}"
        )

        print(
            f"Lines: "
            f"{stats['lines']}"
        )

        return stats

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as error:

        print(
            "Erro ao carregar "
            "stats.json:"
        )

        print(error)

        print(
            "Usando valores padrão."
        )

        return DEFAULT_STATS.copy()


def save_stats(stats):
    """
    Salva somente quando uma coleta real
    foi concluída com sucesso.
    """

    STATS_FILE.parent.mkdir(
        exist_ok=True
    )

    STATS_FILE.write_text(
        json.dumps(
            stats,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "stats.json atualizado."
    )


def get_repositories():
    repositories = []
    page = 1

    while True:
        batch = github(
            f"/users/{USERNAME}/repos"
            f"?per_page=100"
            f"&page={page}"
            f"&type=owner"
            f"&sort=updated"
        )

        repositories.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return repositories


def count_lines_in_repository(
    repo,
    temp_root,
):
    repo_name = repo["name"]

    clone_url = repo["clone_url"]

    repo_path = (
        temp_root / repo_name
    )

    try:
        print(
            f"Clonando {repo_name}..."
        )

        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--quiet",
                clone_url,
                str(repo_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(
                f"Erro ao clonar "
                f"{repo_name}: "
                f"{result.stderr.strip()}"
            )

            return 0

        total_lines = 0

        for path in repo_path.rglob("*"):

            if not path.is_file():
                continue

            relative_path = (
                path.relative_to(
                    repo_path
                )
            )

            parts = (
                relative_path.parts
            )

            if any(
                folder in IGNORE_FOLDERS
                for folder in parts
            ):
                continue

            if (
                path.suffix.lower()
                not in CODE_EXTENSIONS
            ):
                continue

            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                total_lines += len(
                    content.splitlines()
                )

            except (
                OSError,
                UnicodeError,
            ):
                continue

        print(
            f"{repo_name}: "
            f"{total_lines} linhas"
        )

        return total_lines

    except subprocess.TimeoutExpired:
        print(
            f"Timeout ao clonar "
            f"{repo_name}"
        )

        return 0

    except Exception as error:
        print(
            f"Erro ao processar "
            f"{repo_name}: {error}"
        )

        return 0

    finally:
        if repo_path.exists():
            shutil.rmtree(
                repo_path,
                ignore_errors=True,
            )


def count_all_lines(repos):
    total_lines = 0

    with tempfile.TemporaryDirectory(
        prefix="github-stats-"
    ) as temp_dir:

        temp_root = Path(temp_dir)

        for repo in repos:

            total_lines += (
                count_lines_in_repository(
                    repo,
                    temp_root,
                )
            )

    return total_lines


def get_commit_count():
    response = session.get(
        "https://api.github.com/search/commits",
        params={
            "q": f"author:{USERNAME}",
            "per_page": 1,
        },
        timeout=30,
    )

    if not response.ok:
        print(
            "Erro ao buscar commits:"
            f" {response.status_code}"
        )

        print(
            response.text[:1000]
        )

        response.raise_for_status()

    return response.json().get(
        "total_count",
        0,
    )


def collect_real_stats():
    """
    Faz a coleta completa.

    Se qualquer etapa crítica falhar,
    a função lança uma exceção para que
    o programa use os dados anteriores.
    """

    print(
        f"Coletando estatísticas de "
        f"{USERNAME}..."
    )

    github(
        f"/users/{USERNAME}"
    )

    repos = get_repositories()

    print(
        f"Repositórios encontrados: "
        f"{len(repos)}"
    )

    stars = sum(
        repo.get(
            "stargazers_count",
            0,
        )
        for repo in repos
    )

    total_lines = count_all_lines(
        repos
    )

    commits = get_commit_count()

    stats = {
        "repos": len(repos),
        "commits": commits,
        "stars": stars,
        "lines": total_lines,
    }

    return stats


def get_stats():
    """
    Prioridade:

    1. Estatísticas reais atuais.
    2. Últimas estatísticas salvas.
    3. Valores padrão.

    O stats.json só é alterado quando
    a coleta real termina com sucesso.
    """

    previous_stats = (
        load_saved_stats()
    )

    try:
        real_stats = (
            collect_real_stats()
        )

        print(
            "Estatísticas reais "
            "coletadas com sucesso."
        )

        print(
            f"Repositories: "
            f"{real_stats['repos']}"
        )

        print(
            f"Commits: "
            f"{real_stats['commits']}"
        )

        print(
            f"Stars: "
            f"{real_stats['stars']}"
        )

        print(
            f"Lines: "
            f"{real_stats['lines']}"
        )

        save_stats(
            real_stats
        )

        return real_stats

    except Exception as error:

        print(
            "================================"
        )

        print(
            "FALHA AO COLETAR ESTATÍSTICAS"
        )

        print(
            f"Erro: {error}"
        )

        print(
            "================================"
        )

        print(
            "Mantendo as últimas "
            "estatísticas válidas."
        )

        return previous_stats


def ascii_avatar():
    path = (
        ASSETS / "avatar.jpg"
    )

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

    image = Image.open(
        path
    ).convert("L")

    image = ImageOps.fit(
        image,
        (160, 70),
        method=Image.Resampling.LANCZOS,
    )

    lines = []

    for y in range(
        image.height
    ):

        line = ""

        for x in range(
            image.width
        ):

            value = image.getpixel(
                (x, y)
            )

            index = int(
                value
                / 255
                * (
                    len(ASCII_CHARS)
                    - 1
                )
            )

            line += (
                ASCII_CHARS[index]
            )

        lines.append(
            line.rstrip()
        )

    return lines


def esc(value):
    return (
        str(value)
        .replace(
            "&",
            "&amp;",
        )
        .replace(
            "<",
            "&lt;",
        )
        .replace(
            ">",
            "&gt;",
        )
    )


def build_svg(
    dark,
    stats,
):
    bg = (
        "#0b0f14"
        if dark
        else "#f5f5f5"
    )

    panel = (
        "#111820"
        if dark
        else "#ffffff"
    )

    fg = (
        "#d7dee7"
        if dark
        else "#1f2933"
    )

    muted = (
        "#7f8b99"
        if dark
        else "#68737f"
    )

    accent = (
        "#8ab4f8"
        if dark
        else "#245ea8"
    )

    border = (
        "#26313d"
        if dark
        else "#d7dde4"
    )

    start_it = datetime(
        2018,
        4,
        1,
    )

    start_deg = datetime(
        2025,
        2,
        1,
    )

    now = datetime.now()

    diff_it = (
        now - start_it
    )

    years_it = (
        diff_it.days // 365
    )

    months_it = (
        diff_it.days % 365
    ) // 30

    diff_deg = (
        now - start_deg
    )

    years_deg = (
        diff_deg.days // 365
    )

    months_deg = (
        diff_deg.days % 365
    ) // 30

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

    avatar_lines = (
        ascii_avatar()
    )

    max_line_length = (
        max(
            len(line)
            for line in avatar_lines
        )
        if avatar_lines
        else 0
    )

    num_lines = len(
        avatar_lines
    )

    font_size = 3.5

    line_height = 3.5

    char_width = (
        font_size * 0.6
    )

    avatar_width_px = (
        max_line_length
        * char_width
    )

    avatar_height_px = (
        num_lines
        * line_height
    )

    padding = 20

    box_width = (
        avatar_width_px
        + (padding * 2)
    )

    box_height = (
        avatar_height_px
        + (padding * 2)
    )

    box_x = 710
    box_y = 176

    text_x = (
        box_x + padding
    )

    text_y = (
        box_y + padding
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',

        (
            '<svg '
            'xmlns="http://www.w3.org/2000/svg" '
            'width="1200" '
            'height="590" '
            'viewBox="0 0 1100 590">'
        ),

        (
            '<rect '
            'width="1100" '
            'height="590" '
            'rx="18" '
            f'fill="{bg}"/>'
        ),

        (
            '<rect '
            'x="24" '
            'y="24" '
            'width="1052" '
            'height="542" '
            'rx="12" '
            f'fill="{panel}" '
            f'stroke="{border}"/>'
        ),

        (
            '<text '
            'x="52" '
            'y="67" '
            f'fill="{muted}" '
            'font-family="monospace" '
            'font-size="15">'
            'Bem vindo ao meu github!'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="104" '
            f'fill="{accent}" '
            'font-family="monospace" '
            'font-size="30" '
            'font-weight="700">'
            f'{NAME}'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="133" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f'{esc(TITLE)}'
            '</text>'
        ),

        (
            '<line '
            'x1="52" '
            'y1="158" '
            'x2="1048" '
            'y2="158" '
            f'stroke="{border}"/>'
        ),

        (
            '<text '
            'x="52" '
            'y="190" '
            f'fill="{muted}" '
            'font-family="monospace" '
            'font-size="14">'
            'profile'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="218" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            'Cargo:'
            '</text>'
        ),

        (
            '<text '
            'x="120" '
            'y="218" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f'{esc(ROLE)}'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="246" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            'Stack:'
            '</text>'
        ),

        (
            '<text '
            'x="120" '
            'y="246" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f'{esc(BACKEND)} | '
            f'{esc(DATA)}'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="274" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            'Infra:'
            '</text>'
        ),

        (
            '<text '
            'x="120" '
            'y="274" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f'{esc(INFRA)}'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="302" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            'Sistemas:'
            '</text>'
        ),

        (
            '<text '
            'x="144" '
            'y="302" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f'{esc(SYSTEMS)}'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="340" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            'Experiência:'
            '</text>'
        ),

        (
            '<text '
            'x="174" '
            'y="340" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f'{esc(it_text)}'
            '</text>'
        ),

        (
            '<text '
            'x="52" '
            'y="368" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16" '
            'font-weight="700">'
            'Formação:'
            '</text>'
        ),

        (
            '<text '
            'x="150" '
            'y="368" '
            f'fill="{fg}" '
            'font-family="monospace" '
            'font-size="16">'
            f'{esc(deg_text)}'
            '</text>'
        ),
    ]

    current_y = text_y

    for line in avatar_lines:

        lines.append(
            (
                '<text '
                f'x="{text_x}" '
                f'y="{current_y}" '
                f'fill="{fg}" '
                'font-family="monospace" '
                f'font-size="{font_size}" '
                'xml:space="preserve">'
                f'{esc(line)}'
                '</text>'
            )
        )

        current_y += line_height

    lines.append(
        (
            '<text '
            'x="52" '
            'y="456" '
            f'fill="{muted}" '
            'font-family="monospace" '
            'font-size="14">'
            'github stats:'
            '</text>'
        )
    )

    stats_rows = [
        (
            "repositories",
            stats["repos"],
            52,
        ),
        (
            "commits",
            stats["commits"],
            280,
        ),
        (
            "stars",
            stats["stars"],
            510,
        ),
        (
            "lines of code",
            stats["lines"],
            740,
        ),
    ]

    for label, value, x in stats_rows:

        lines.extend(
            [
                (
                    '<text '
                    f'x="{x}" '
                    'y="487" '
                    f'fill="{muted}" '
                    'font-family="monospace" '
                    'font-size="13">'
                    f'{label}'
                    '</text>'
                ),

                (
                    '<text '
                    f'x="{x}" '
                    'y="520" '
                    f'fill="{accent}" '
                    'font-family="monospace" '
                    'font-size="25" '
                    'font-weight="700">'
                    f'{esc(value)}'
                    '</text>'
                ),
            ]
        )

    lines.extend(
        [
            (
                '<text '
                'x="52" '
                'y="550" '
                f'fill="{muted}" '
                'font-family="monospace" '
                'font-size="14" '
                'font-style="italic">'
                'onde o código toca o metal.'
                '</text>'
            ),

            '</svg>',
        ]
    )

    return "\n".join(lines)


def main():
    ASSETS.mkdir(
        exist_ok=True
    )

    stats = get_stats()

    print(
        "================================"
    )

    print(
        "ESTATÍSTICAS FINAIS"
    )

    print(
        f"Repositories: "
        f"{stats['repos']}"
    )

    print(
        f"Commits: "
        f"{stats['commits']}"
    )

    print(
        f"Stars: "
        f"{stats['stars']}"
    )

    print(
        f"Lines: "
        f"{stats['lines']}"
    )

    print(
        "================================"
    )

    dark_svg = build_svg(
        True,
        stats,
    )

    light_svg = build_svg(
        False,
        stats,
    )

    (
        ASSETS / "dark_mode.svg"
    ).write_text(
        dark_svg,
        encoding="utf-8",
    )

    (
        ASSETS / "light_mode.svg"
    ).write_text(
        light_svg,
        encoding="utf-8",
    )

    print(
        "SVGs gerados com sucesso."
    )


if __name__ == "__main__":
    main()