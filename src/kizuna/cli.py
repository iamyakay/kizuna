import argparse
import asyncio
import sys
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version

from kizuna import __version__
from kizuna.errors import ConfigurationError, KizunaError
from kizuna.output import emit_json


def discord_id(value: str) -> int:
    from kizuna.config import snowflake

    try:
        return snowflake(value)
    except ConfigurationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", type=Path, help="directory containing kizuna.toml")
    parser.add_argument("--json", action="store_true", help="print machine readable JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kizuna", description="A toolkit for discord.py bots.")
    parser.add_argument("--version", action="version", version=f"kizuna {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("init", help="create a discord.py project")
    create.add_argument("directory", type=Path)
    create.add_argument("--json", action="store_true")
    create.set_defaults(handler="init")
    check = subparsers.add_parser("doctor", help="check your project and bot configuration")
    common(check)
    check.add_argument("--online", action="store_true", help="also verify token and guild access")
    check.set_defaults(handler="doctor")
    command = subparsers.add_parser("commands", help="inspect and sync application commands")
    actions = command.add_subparsers(dest="action", required=True)
    for name, help_text in (
        ("list", "list local or registered commands"),
        ("diff", "compare local commands with Discord"),
        ("sync", "preview changes, or sync with --apply"),
    ):
        action = actions.add_parser(name, help=help_text)
        common(action)
        scope = action.add_mutually_exclusive_group()
        scope.add_argument("--guild", type=discord_id, help="target a development guild")
        scope.add_argument("--global", dest="global_scope", action="store_true")
        if name == "list":
            action.add_argument("--remote", action="store_true", help="fetch commands from Discord")
        elif name == "diff":
            action.add_argument("--check", action="store_true", help="exit with 1 if commands differ")
        else:
            action.add_argument("--apply", action="store_true", help="apply the current plan")
            action.add_argument("--allow-delete", action="store_true", help="allow command removal")
            action.add_argument("--allow-empty", action="store_true", help="allow an empty local tree")
        action.set_defaults(handler="application")
    return parser


async def dispatch(args: argparse.Namespace) -> int:
    if args.handler == "init":
        from kizuna.commands.init import run

        return await run(args)
    try:
        version("discord.py")
        import aiohttp
        import discord

        from kizuna.commands import application, doctor
    except (ImportError, PackageNotFoundError):
        raise KizunaError(
            "Discord dependencies are unavailable. Install Kizuna's dependencies "
            "in a dedicated virtual environment."
        ) from None
    try:
        handler = doctor.run if args.handler == "doctor" else application.run
        return await handler(args)
    except discord.LoginFailure:
        message = "Discord rejected the bot token. Check the configured environment variable."
    except discord.Forbidden:
        message = "Discord denied access. Check the bot installation and target guild."
    except discord.NotFound:
        message = "Discord could not find that resource. Check the application or guild ID."
    except discord.HTTPException as exc:
        message = f"Discord request failed (HTTP {exc.status}, code {exc.code})."
    except discord.RateLimited:
        message = "Discord requested a long rate limit wait. Retry later."
    except discord.DiscordException as exc:
        message = f"discord.py could not complete the operation ({type(exc).__name__})."
    except (aiohttp.ClientError, TimeoutError):
        message = "Could not reach Discord. Check your connection and try again."
    raise KizunaError(message)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return asyncio.run(dispatch(args))
    except KizunaError as exc:
        message = str(exc)
    except OSError:
        message = "Cannot access a required file or directory. Check the path and permissions."
    except KeyboardInterrupt:
        return 130
    if args.json:
        emit_json({"error": message})
    else:
        print(f"error: {message}", file=sys.stderr)
    return 2
