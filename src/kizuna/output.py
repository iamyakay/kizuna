import json
from typing import Any

from kizuna.diff import CommandPlan


def emit_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=True))


def show_plan(plan: CommandPlan, scope: str) -> None:
    print(f"Commands: {scope}")
    symbols = {"add": "+", "update": "~", "remove": "-"}
    names = {1: "slash", 2: "user", 3: "message"}
    for change in plan.changes:
        fields = f" ({', '.join(change.fields)})" if change.fields else ""
        kind = names.get(change.type, str(change.type))
        print(f"  {symbols[change.action]} {change.name} [{kind}]{fields}")
    if not plan.changes:
        print("  Everything is up to date.")
    print(f"  {len(plan.changes)} changed, {plan.unchanged} unchanged")
