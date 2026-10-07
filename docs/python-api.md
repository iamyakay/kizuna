# Python API

`plan_commands(local, remote, guild=False)` accepts lists of Discord command payload dictionaries and returns a `CommandPlan`. It does not access Discord or mutate the payloads.

A plan contains `changes`, `unchanged`, and a `has_deletions` property. Each `CommandChange` has an action, name, command type, and tuple of changed fields. `plan.to_dict()` produces a JSON-compatible dictionary.

```python
from kizuna import plan_commands

local = [{"name": "ping", "description": "Check the bot.", "type": 1}]
remote = [{"name": "ping", "description": "Old description", "type": 1}]

plan = plan_commands(local, remote)
for change in plan.changes:
    print(change.action, change.name, change.fields)
```

`CommandService` operates on a discord.py `commands.Bot`. The caller owns its login and lifetime. Supply a guild ID to copy global definitions into that guild before comparing or syncing.

```python
from kizuna.application import CommandService


async def preview(bot, guild_id):
    service = CommandService(bot, guild_id)
    result = await service.sync()
    return result.plan.to_dict()
```

`local()` reads serialized command definitions. `remote()` fetches registered commands. `plan()` compares them. `sync(apply=False, allow_delete=False, allow_empty=False)` returns a `SyncResult` with the plan, whether a write occurred, and the resulting local command count. All methods that contact Discord require a logged-in bot.

Use `kizuna.config.load_config` and `kizuna.project.open_bot` if you want the same factory loading and cleanup as the CLI. `open_bot` is an asynchronous context manager. See [the runnable preview example](../examples/preview_commands.py).
