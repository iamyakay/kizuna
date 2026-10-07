import argparse
import asyncio
import json
from pathlib import Path

from kizuna.application import CommandService
from kizuna.config import load_config, snowflake
from kizuna.project import open_bot


async def preview(project: Path, guild_id: int | None) -> None:
    config = load_config(project)
    async with open_bot(config) as bot:
        await bot.login(config.token())
        service = CommandService(bot, guild_id or config.guild_id)
        plan = await service.plan()
        print(json.dumps(plan.to_dict(), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preview a bot's command changes without syncing.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--guild", type=snowflake)
    args = parser.parse_args()
    asyncio.run(preview(args.project, args.guild))
