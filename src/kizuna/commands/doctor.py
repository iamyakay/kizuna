from argparse import Namespace
from importlib.metadata import version

from kizuna.config import load_config
from kizuna.errors import ConfigurationError
from kizuna.output import emit_json
from kizuna.project import local_commands, open_bot, target_guild


async def run(args: Namespace) -> int:
    config = load_config(args.project)
    checks = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    add("configuration", "pass", str(config.root / "kizuna.toml"))
    add("discord.py", "pass", version("discord.py"))
    token = None
    try:
        token = config.token()
        add("token", "pass", f"{config.token_env} is set; value hidden")
    except ConfigurationError as exc:
        add("token", "fail" if args.online else "warn", str(exc))
    async with open_bot(config) as bot:
        if args.online and token:
            await bot.login(token)
            app = await bot.application_info()
            add("authentication", "pass", f"Bot authenticated; application {app.id}")
        guild = target_guild(bot, config.guild_id)
        commands = local_commands(bot, guild)
        add("factory", "pass", config.factory)
        add("commands", "pass" if commands else "warn", f"{len(commands)} commands loaded")
        if not commands:
            add("loading", "warn", "Register commands in the factory, before login or startup.")
        intents = [name for name, enabled in bot.intents if enabled]
        add("intents", "pass", ", ".join(intents) or "none")
        if args.online and token and guild:
            await bot.fetch_guild(guild.id)
            add("guild", "pass", f"Bot can access guild {guild.id}")
    ok = not any(check["status"] == "fail" for check in checks)
    if args.json:
        emit_json({"ok": ok, "online": args.online, "checks": checks})
    else:
        for check in checks:
            print(f"[{check['status']}] {check['name']}: {check['detail']}")
        if not args.online:
            print("Offline check. Use --online to verify authentication and configured guild access.")
    return 0 if ok else 1
