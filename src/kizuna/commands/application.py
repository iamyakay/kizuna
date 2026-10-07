from argparse import Namespace

from kizuna.application import CommandService
from kizuna.config import load_config
from kizuna.output import emit_json, show_plan
from kizuna.project import open_bot


async def run(args: Namespace) -> int:
    config = load_config(args.project)
    guild_id = None if args.global_scope else (args.guild or config.guild_id)
    scope = f"guild {guild_id}" if guild_id else "global"
    async with open_bot(config) as bot:
        online = args.action != "list" or args.remote
        if online:
            await bot.login(config.token())
        service = CommandService(bot, guild_id)
        if args.action == "list":
            commands = await service.remote() if args.remote else service.local()
            if args.json:
                emit_json({"scope": scope, "source": "remote" if args.remote else "local",
                           "commands": commands})
            else:
                print(f"Commands: {scope} ({'remote' if args.remote else 'local'})")
                for command in commands:
                    print(f"  {command['name']} [type {command.get('type', 1)}]")
                print(f"  {len(commands)} commands")
            return 0
        if args.action == "diff":
            plan = await service.plan()
            if args.json:
                emit_json({"scope": scope, **plan.to_dict()})
            else:
                show_plan(plan, scope)
            return 1 if args.check and plan.changes else 0
        result = await service.sync(
            apply=args.apply, allow_delete=args.allow_delete, allow_empty=args.allow_empty
        )
        if args.json:
            emit_json({"scope": scope, "applied": result.applied,
                       "command_count": result.command_count, **result.plan.to_dict()})
        else:
            show_plan(result.plan, scope)
            if result.applied:
                print(f"Synced {result.command_count} commands.")
            elif result.plan.changes:
                print("Preview only. Run again with --apply to sync.")
    return 0
