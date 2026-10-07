from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class CommandChange:
    action: Literal["add", "update", "remove"]
    name: str
    type: int
    fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommandPlan:
    changes: tuple[CommandChange, ...]
    unchanged: int

    @property
    def has_deletions(self) -> bool:
        return any(change.action == "remove" for change in self.changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changes": [asdict(change) for change in self.changes],
            "unchanged": self.unchanged,
        }


def _option(value: dict[str, Any]) -> dict[str, Any]:
    result = {key: item for key, item in value.items() if item is not None}
    result.setdefault("required", False)
    result.setdefault("autocomplete", False)
    for key in ("choices", "channel_types", "options"):
        result.setdefault(key, [])
    for key in ("name_localizations", "description_localizations"):
        result.setdefault(key, {})
    result["channel_types"] = sorted(result["channel_types"])
    result["options"] = [_option(item) for item in result["options"]]
    result["choices"] = [
        {**item, "name_localizations": item.get("name_localizations") or {}}
        for item in result["choices"]
    ]
    return result


def _command(value: dict[str, Any], *, guild: bool) -> dict[str, Any]:
    result = {
        "type": int(value.get("type", 1)),
        "name": value["name"],
        "description": value.get("description") or "",
        "options": [_option(item) for item in value.get("options", [])],
        "name_localizations": value.get("name_localizations") or {},
        "description_localizations": value.get("description_localizations") or {},
        "default_member_permissions": value.get("default_member_permissions"),
        "nsfw": value.get("nsfw", False),
    }
    if result["default_member_permissions"] is not None:
        result["default_member_permissions"] = str(result["default_member_permissions"])
    if not guild:
        result["dm_permission"] = value.get("dm_permission", True)
        for key in ("contexts", "integration_types"):
            result[key] = sorted(value[key]) if value.get(key) is not None else None
    return result


def _index(commands: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    result = {}
    for command in commands:
        key = (int(command.get("type", 1)), command["name"])
        if key in result:
            raise ValueError(f"Duplicate command: {key[1]} (type {key[0]}).")
        result[key] = command
    return result


def plan_commands(
    local: list[dict[str, Any]],
    remote: list[dict[str, Any]],
    *,
    guild: bool = False,
) -> CommandPlan:
    desired, current = _index(local), _index(remote)
    changes = []
    unchanged = 0
    for key in sorted(desired.keys() | current.keys()):
        command_type, name = key
        if key not in current:
            changes.append(CommandChange("add", name, command_type))
        elif key not in desired:
            changes.append(CommandChange("remove", name, command_type))
        else:
            before = _command(current[key], guild=guild)
            after = _command(desired[key], guild=guild)
            for field in ("contexts", "integration_types"):
                if not guild and after[field] is None:
                    before[field] = None
            fields = tuple(
                field for field in sorted(after)
                if before[field] != after[field]
            )
            if fields:
                changes.append(CommandChange("update", name, command_type, fields))
            else:
                unchanged += 1
    return CommandPlan(tuple(changes), unchanged)
