from argparse import Namespace

from kizuna.output import emit_json
from kizuna.scaffold import create_project


async def run(args: Namespace) -> int:
    target = create_project(args.directory)
    if args.json:
        emit_json({"created": str(target)})
    else:
        print(f"Created {target}")
        print(f'  cd "{target}"')
        print("  python -m pip install -e .")
        print("  kizuna doctor")
        print("Add your bot token to .env, then run python -m bot.")
    return 0
