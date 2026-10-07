import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from kizuna.errors import ConfigurationError


def snowflake(value: str | int) -> int:
    text = str(value)
    if not text.isascii() or not text.isdecimal() or not 0 < int(text) < 2**64:
        raise ConfigurationError("Discord IDs must be positive integers smaller than 2^64.")
    return int(text)


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    factory: str
    source: Path
    token_env: str = "DISCORD_TOKEN"
    guild_id: int | None = None

    def token(self) -> str:
        value = os.environ.get(self.token_env)
        if value is None:
            from dotenv import dotenv_values

            value = dotenv_values(self.root / ".env", interpolate=False).get(self.token_env)
        if not isinstance(value, str) or not value.strip():
            raise ConfigurationError(f"Set {self.token_env} in your environment or project .env.")
        value = value.strip()
        if value.lower().startswith(("bot ", "bearer ")) or any(c.isspace() for c in value):
            raise ConfigurationError(f"{self.token_env} must contain only the raw bot token.")
        return value


def load_config(directory: Path | None = None) -> ProjectConfig:
    root = (directory or Path.cwd()).resolve()
    candidates = [root] if directory is not None else [root, *root.parents]
    for candidate in candidates:
        path = candidate / "kizuna.toml"
        if path.is_file():
            root = candidate
            break
    else:
        raise ConfigurationError("No kizuna.toml found. Run kizuna init or use --project PATH.")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError("Cannot read kizuna.toml. Check its encoding and TOML syntax.") from exc
    allowed = {"factory", "source", "token_env", "guild_id"}
    unknown = set(data) - allowed
    if unknown:
        raise ConfigurationError("Unknown kizuna.toml settings: " + ", ".join(sorted(unknown)))
    factory = data.get("factory")
    if not isinstance(factory, str) or not re.fullmatch(r"\w+(?:\.\w+)*:\w+", factory):
        raise ConfigurationError('Set factory to "module:function", such as "bot.app:create_bot".')
    source_value = data.get("source", "src")
    if not isinstance(source_value, str):
        raise ConfigurationError("source must be a directory path.")
    source = (root / source_value).resolve()
    if not source.is_relative_to(root) or not source.is_dir():
        raise ConfigurationError("source must point to an existing directory inside the project.")
    token_env = data.get("token_env", "DISCORD_TOKEN")
    if not isinstance(token_env, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token_env):
        raise ConfigurationError("token_env must be an environment variable name.")
    guild_id = data.get("guild_id")
    if guild_id is not None:
        guild_id = snowflake(guild_id)
    return ProjectConfig(root, factory, source, token_env, guild_id)
