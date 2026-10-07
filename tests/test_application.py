import unittest
from importlib.metadata import PackageNotFoundError, version
from unittest.mock import AsyncMock

try:
    version("discord.py")
except PackageNotFoundError:
    HAS_DISCORD = False
else:
    HAS_DISCORD = True

if HAS_DISCORD:
    import discord
    from discord import app_commands
    from discord.ext import commands

    from kizuna.application import CommandService

from kizuna.errors import ProjectError


@unittest.skipUnless(HAS_DISCORD, "Install discord.py to run Discord integration tests.")
class CommandServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
        await self.bot.__aenter__()
        self.addAsyncCleanup(self.bot.close)

        @self.bot.tree.command(description="Check the bot.")
        async def ping(interaction: discord.Interaction):
            pass

        self.bot.tree.fetch_commands = AsyncMock(return_value=[])
        self.bot.tree.sync = AsyncMock(return_value=[])

    async def test_preview_does_not_sync(self):
        result = await CommandService(self.bot).sync()
        self.assertFalse(result.applied)
        self.assertEqual(result.plan.changes[0].action, "add")
        self.bot.tree.sync.assert_not_awaited()

    async def test_apply_syncs_selected_guild(self):
        result = await CommandService(self.bot, 123).sync(apply=True)
        self.assertTrue(result.applied)
        self.assertEqual(self.bot.tree.sync.call_args.kwargs["guild"].id, 123)

    def remote(self, **fields):
        payload = {"id": "123", "application_id": "456", "name": "ping",
                   "description": "Check the bot.", "type": 1, **fields}
        return app_commands.AppCommand(data=payload, state=self.bot._connection)

    async def test_remote_serialization_keeps_permissions_and_nsfw(self):
        self.bot.tree.fetch_commands.return_value = [
            self.remote(default_member_permissions="8", nsfw=True, dm_permission=False)
        ]
        result = (await CommandService(self.bot).remote())[0]
        self.assertEqual(result["default_member_permissions"], "8")
        self.assertTrue(result["nsfw"])
        self.assertFalse(result["dm_permission"])

    async def test_noop_does_not_sync(self):
        self.bot.tree.fetch_commands.return_value = [self.remote()]
        result = await CommandService(self.bot).sync(apply=True)
        self.assertFalse(result.applied)
        self.bot.tree.sync.assert_not_awaited()

    async def test_removal_requires_explicit_flag(self):
        self.bot.tree.fetch_commands.return_value = [self.remote(name="old")]
        with self.assertRaisesRegex(ProjectError, "allow-delete"):
            await CommandService(self.bot).sync(apply=True)
        self.bot.tree.sync.assert_not_awaited()

    async def test_empty_tree_requires_both_flags(self):
        self.bot.tree.clear_commands(guild=None)
        self.bot.tree.fetch_commands.return_value = [self.remote()]
        with self.assertRaisesRegex(ProjectError, "allow-empty"):
            await CommandService(self.bot).sync(apply=True, allow_delete=True)
        with self.assertRaisesRegex(ProjectError, "allow-delete"):
            await CommandService(self.bot).sync(apply=True, allow_empty=True)
        result = await CommandService(self.bot).sync(
            apply=True, allow_empty=True, allow_delete=True
        )
        self.assertTrue(result.applied)

    async def test_same_name_context_menus_remain_separate(self):
        async def user_menu(interaction: discord.Interaction, user: discord.User):
            pass

        async def message_menu(interaction: discord.Interaction, message: discord.Message):
            pass

        self.bot.tree.add_command(app_commands.ContextMenu(name="Inspect", callback=user_menu))
        self.bot.tree.add_command(app_commands.ContextMenu(name="Inspect", callback=message_menu))
        plan = await CommandService(self.bot).plan()
        self.assertEqual(len(plan.changes), 3)

    async def test_unsupported_remote_types_block_sync(self):
        self.bot.tree.fetch_commands.return_value = [self.remote(type=4)]
        with self.assertRaisesRegex(ProjectError, "unsupported"):
            await CommandService(self.bot).sync(apply=True, allow_delete=True)
        self.bot.tree.sync.assert_not_awaited()
