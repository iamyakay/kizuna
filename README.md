<p align="center">
  <img src="assets/banner.svg" alt="Kizuna: a quiet city, a bright moon, and one more command before sunrise" width="100%">
</p>

# Kizuna

A terminal toolkit for discord.py bots. Create a project, check its setup, and see exactly which application commands will change before syncing them.

Your Python command definitions stay the source of truth. Kizuna loads your bot through a small factory function and uses discord.py for Discord requests. No second command manifest to keep in sync.

```text
kizuna init my-bot
kizuna doctor
kizuna commands diff --guild 123456789012345678
kizuna commands sync --guild 123456789012345678 --apply
```

## What it does

- Creates a bot with a `src/` layout, a cog, configuration, and a test.
- Checks the factory, dependencies, token configuration, and loaded commands offline.
- Verifies authentication and configured guild access with `doctor --online`.
- Lists local commands or fetches registered commands from Discord.
- Compares command names, descriptions, options, permissions, contexts, and NSFW settings.
- Previews syncs and requires explicit flags for command deletion or an empty tree.
- Produces JSON output for scripts and a nonzero exit code for command drift in CI.

Kizuna is an early developer toolkit built on discord.py. It does not replace the library or wrap every Discord endpoint.

## Install from source

Requires Python 3.11 or newer. This package has not been published to PyPI. From this repository, create a dedicated virtual environment:

```text
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS and Linux:

```sh
source .venv/bin/activate
```

Then install:

```text
python -m pip install -e .
kizuna --help
```

If shell activation is unavailable, run the environment's Python directly, for example `.venv\Scripts\python.exe -m kizuna --help` on Windows.

## Create your first bot

```text
kizuna init my-bot
cd my-bot
python -m pip install -e .
kizuna doctor
kizuna commands list
```

Copy `.env.example` to `.env`, then set `DISCORD_TOKEN` to your application's bot token. Environment variables take precedence over the file. Kizuna reads only the configured token variable and does not load the file into your process environment.

Install the bot in a test server through the [Discord Developer Portal](https://discord.com/developers/applications), with the `bot` and `applications.commands` scopes. Replace the example guild ID below with that server's ID:

```text
kizuna commands diff --guild 123456789012345678
kizuna commands sync --guild 123456789012345678 --apply
python -m bot
```

The generated bot has a `/ping` command and does not need privileged intents. Keep it running to receive interactions. Registering commands alone does not run the bot.

## Preview before syncing

```text
$ kizuna commands diff --guild 123456789012345678
Commands: guild 123456789012345678
  + ping [slash]
  ~ search [slash] (description, options)
  - old-command [slash]
  3 changed, 0 unchanged
```

`commands sync` without `--apply` only previews. If commands would be removed, add `--allow-delete` after reviewing the diff. Clearing a nonempty remote scope requires both `--allow-delete` and `--allow-empty`.

Use `--global` to target global commands. Guild deployment copies global definitions into the selected guild and includes guild-specific commands. A global definition wins if the same name and command type exist in both scopes. Sync replaces the selected scope's full command set, so use a factory that loads every command you want to keep there.

## Use an existing bot

Add `kizuna.toml` to its root:

```toml
factory = "bot.app:create_bot"
source = "src"
token_env = "DISCORD_TOKEN"
guild_id = "123456789012345678"
```

`guild_id` is optional. Without it, commands target the global scope unless `--guild` is supplied. Use `source = "."` for projects without a `src/` directory.

The factory can be synchronous or asynchronous. It must return a configured `commands.Bot` without logging in, starting the gateway, or syncing commands:

```python
import discord
from discord.ext import commands


async def create_bot() -> commands.Bot:
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
    await bot.load_extension("bot.cogs.general")
    return bot
```

Load extensions in the factory so offline commands see the same tree as online commands. Factories and extensions are Python code and execute when Kizuna loads a project. Only use a project you trust. Online commands also call the bot's `login`, which runs its `setup_hook`; keep that hook free of command syncs and gateway waits.

## Commands

| Command | Purpose | Discord connection |
| --- | --- | --- |
| `kizuna init PATH` | Create a bot in a new directory | No |
| `kizuna doctor` | Check local configuration and command loading | No |
| `kizuna doctor --online` | Also verify authentication and configured guild access | Yes |
| `kizuna commands list` | List local application commands | No |
| `kizuna commands list --remote` | Fetch registered commands | Yes |
| `kizuna commands diff` | Compare local and registered commands | Yes |
| `kizuna commands sync` | Preview the current sync plan | Yes, reads only |
| `kizuna commands sync --apply` | Apply the current plan | Yes, writes |

Put options after the leaf command, such as `kizuna commands list --project ../my-bot --json`. All commands support `--json`. Commands that load a project support `--project PATH` and otherwise search the current directory and its parents for `kizuna.toml`.

`commands diff --check` exits with `1` when commands differ. Successful commands exit with `0`; configuration and request errors exit with `2`. Doctor exits with `1` when a completed check fails. A missing token is a warning in offline mode.

## Python API

The comparison engine works with Discord command payloads:

```python
from kizuna import plan_commands

local = [{"name": "ping", "description": "Check the bot.", "type": 1}]
plan = plan_commands(local, [])
print(plan.to_dict())
```

For a configured, logged-in discord.py bot, `CommandService` provides `local()`, `remote()`, `plan()`, and `sync()`. Its sync defaults to a preview, just like the CLI. See [the Python API guide](docs/python-api.md).

## Project layout

```text
kizuna/
  src/kizuna/
    cli.py
    config.py
    project.py
    application.py
    diff.py
    scaffold.py
    commands/
    templates/bot/
  tests/
  examples/
  docs/
  assets/
  .github/workflows/
  pyproject.toml
```

## Development

```text
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m ruff check .
python -m build
```
v
Tests use local fixtures and mocked Discord responses. No real bot token is needed. The GitHub Actions workflow runs the suite on Windows and Linux with Python 3.11 through 3.14, then checks wheel installation and scaffold generation.

Read [configuration](docs/configuration.md), [command syncing](docs/command-sync.md), and [contributing](CONTRIBUTING.md) for details. The current release does not support command translators; comparisons also leave application-level context and installation defaults unmanaged unless explicitly set in code.

MIT licensed. Built independently, with [discord.py](https://github.com/Rapptz/discord.py).
