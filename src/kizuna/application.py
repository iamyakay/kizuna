from dataclasses import dataclass
from typing import Any

from discord.ext import commands

from kizuna.diff import CommandPlan, plan_commands
from kizuna.errors import ProjectError
from kizuna.project import local_commands, target_guild


@dataclass(frozen=True)
class SyncResult:
    plan: CommandPlan
    applied: bool
    command_count: int


class CommandService:
    def __init__(self, bot: commands.Bot, guild_id: int | None = None):
        self.bot = bot
        self.guild = target_guild(bot, guild_id)

    def local(self) -> list[dict[str, Any]]:
        return local_commands(self.bot, self.guild)

    async def remote(self) -> list[dict[str, Any]]:
        commands = await self.bot.tree.fetch_commands(guild=self.guild)
        return [
            {
                **command.to_dict(),
                "default_member_permissions": (
                    str(command.default_member_permissions.value)
                    if command.default_member_permissions is not None else None
                ),
                "dm_permission": command.dm_permission,
                "nsfw": command.nsfw,
            }
            for command in commands
        ]

    async def plan(self) -> CommandPlan:
        remote = await self.remote()
        self.validate_remote(remote)
        return plan_commands(self.local(), remote, guild=self.guild is not None)

    @staticmethod
    def validate_remote(remote: list[dict[str, Any]]) -> None:
        if any(command.get("type", 1) not in (1, 2, 3) for command in remote):
            raise ProjectError("This scope contains unsupported command types. Sync is disabled.")

    async def sync(
        self,
        *,
        apply: bool = False,
        allow_delete: bool = False,
        allow_empty: bool = False,
    ) -> SyncResult:
        local = self.local()
        remote = await self.remote()
        self.validate_remote(remote)
        plan = plan_commands(local, remote, guild=self.guild is not None)
        if not apply or not plan.changes:
            return SyncResult(plan, False, len(local))
        if not local and not allow_empty:
            raise ProjectError("The local tree is empty. Use --allow-empty to clear this scope.")
        if plan.has_deletions and not allow_delete:
            raise ProjectError("This sync removes commands. Review the diff, then use --allow-delete.")
        synced = await self.bot.tree.sync(guild=self.guild)
        return SyncResult(plan, True, len(synced))
