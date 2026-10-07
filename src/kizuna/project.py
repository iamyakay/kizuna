import importlib
import inspect
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import discord
from discord.ext import commands

from kizuna.config import ProjectConfig
from kizuna.errors import ProjectError


@asynccontextmanager
async def open_bot(config: ProjectConfig) -> AsyncIterator[commands.Bot]:
    original_path = sys.path.copy()
    sys.path.insert(0, str(config.source))
    sys.path.insert(1, str(config.root))
    try:
        module_name, function_name = config.factory.split(":")
        try:
            module = importlib.import_module(module_name)
            module_file = getattr(module, "__file__", None)
            if module_file is None:
                raise ProjectError("The factory module must be a Python file in this project.")
            if not Path(module_file).resolve().is_relative_to(config.root):
                raise ProjectError("The factory resolved outside the project. Rename its module.")
            factory = getattr(module, function_name)
            bot = factory()
            if inspect.isawaitable(bot):
                bot = await bot
        except ProjectError:
            raise
        except Exception as exc:
            raise ProjectError(
                f"Cannot load {config.factory} ({type(exc).__name__}). "
                "Check the factory and install the project's dependencies."
            ) from None
        if not isinstance(bot, commands.Bot):
            raise ProjectError("The factory must return a discord.ext.commands.Bot instance.")
        async with bot:
            yield bot
    finally:
        sys.path[:] = original_path


def target_guild(bot: commands.Bot, guild_id: int | None) -> discord.Object | None:
    if guild_id is None:
        return None
    guild = discord.Object(id=guild_id)
    bot.tree.copy_global_to(guild=guild)
    return guild


def local_commands(bot: commands.Bot, guild: discord.Object | None) -> list[dict[str, Any]]:
    if bot.tree.translator is not None:
        raise ProjectError("Command translators are not supported by this version of Kizuna.")
    return [command.to_dict(bot.tree) for command in bot.tree.get_commands(guild=guild)]
