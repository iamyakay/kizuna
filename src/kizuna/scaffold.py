import re
import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

from kizuna.errors import ProjectError

TEMPLATES = {
    "pyproject.toml.tmpl": "pyproject.toml",
    "kizuna.toml.tmpl": "kizuna.toml",
    "env.tmpl": ".env.example",
    "gitignore.tmpl": ".gitignore",
    "readme.md.tmpl": "README.md",
    "app.py.tmpl": "src/bot/app.py",
    "main.py.tmpl": "src/bot/__main__.py",
    "ping.py.tmpl": "src/bot/cogs/ping.py",
    "test_bot.py.tmpl": "tests/test_bot.py",
}


def create_project(destination: Path) -> Path:
    target = destination.absolute()
    name = target.name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
        raise ProjectError("Use a project name containing letters, numbers, hyphens or underscores.")
    if target.exists() or target.is_symlink():
        raise ProjectError("That path already exists. Choose a new directory.")
    if not target.parent.is_dir():
        raise ProjectError("The parent directory does not exist.")
    temporary = Path(tempfile.mkdtemp(prefix=".kizuna-", dir=target.parent))
    try:
        resources = files("kizuna").joinpath("templates", "bot")
        for template, relative in TEMPLATES.items():
            content = resources.joinpath(template).read_text(encoding="utf-8")
            path = temporary / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content.replace("{{name}}", name), encoding="utf-8")
        for relative in ("src/bot/__init__.py", "src/bot/cogs/__init__.py"):
            (temporary / relative).touch()
        temporary.rename(target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target
