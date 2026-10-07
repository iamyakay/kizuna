import copy
import unittest

from kizuna.diff import plan_commands


def command(name="ping", **fields):
    return {"name": name, "description": "Check the bot.", "type": 1, **fields}


class CommandDiffTests(unittest.TestCase):
    def test_reports_add_update_and_remove(self):
        local = [command(), command("new")]
        remote = [command(description="Old description"), command("old")]
        changes = {(item.name, item.action) for item in plan_commands(local, remote).changes}
        self.assertEqual(changes, {("ping", "update"), ("new", "add"), ("old", "remove")})

    def test_ignores_server_metadata(self):
        remote = command(id="123", application_id="456", version="789", guild_id="101")
        self.assertEqual(plan_commands([command()], [remote]).unchanged, 1)

    def test_normalizes_absent_option_defaults(self):
        option = {"type": 3, "name": "query", "description": "Search text"}
        remote = {**option, "required": False, "autocomplete": False, "choices": [],
                  "channel_types": [], "options": [], "min_length": None,
                  "name_localizations": {}, "description_localizations": None}
        self.assertFalse(plan_commands([command(options=[option])],
                                       [command(options=[remote])]).changes)

    def test_detects_nested_option_change(self):
        option = {"type": 1, "name": "find", "description": "Find a record", "options": [
            {"type": 3, "name": "query", "description": "Text", "required": True}
        ]}
        remote = copy.deepcopy(option)
        remote["options"][0]["required"] = False
        plan = plan_commands([command(options=[option])], [command(options=[remote])])
        self.assertEqual(plan.changes[0].fields, ("options",))

    def test_preserves_option_order(self):
        options = [{"type": 3, "name": name, "description": name} for name in ("first", "last")]
        self.assertTrue(plan_commands([command(options=options)],
                                      [command(options=list(reversed(options)))]).changes)

    def test_normalizes_choice_localizations(self):
        option = {"type": 3, "name": "mode", "description": "Mode",
                  "choices": [{"name": "Fast", "value": "fast"}]}
        remote = copy.deepcopy(option)
        remote["choices"][0]["name_localizations"] = {}
        self.assertFalse(plan_commands([command(options=[option])],
                                       [command(options=[remote])]).changes)

    def test_detects_zero_permissions(self):
        plan = plan_commands([command(default_member_permissions="0")], [command()])
        self.assertEqual(plan.changes[0].fields, ("default_member_permissions",))

    def test_normalizes_permission_integer(self):
        self.assertFalse(plan_commands([command(default_member_permissions=8)],
                                       [command(default_member_permissions="8")]).changes)

    def test_distinguishes_context_menu_types(self):
        self.assertEqual(len(plan_commands([command(type=2)], [command(type=3)]).changes), 2)

    def test_rejects_duplicates(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            plan_commands([command(), command()], [])

    def test_ignores_unmanaged_context_defaults(self):
        self.assertFalse(plan_commands([command(contexts=None, integration_types=None)],
                                       [command(contexts=[0, 1, 2], integration_types=[0])]).changes)

    def test_compares_explicit_contexts_as_sets(self):
        self.assertFalse(plan_commands([command(contexts=[0, 1])],
                                       [command(contexts=[1, 0])]).changes)
        self.assertTrue(plan_commands([command(contexts=[0])],
                                      [command(contexts=[1])]).changes)

    def test_guild_ignores_global_only_fields(self):
        self.assertFalse(plan_commands([command(contexts=[0], dm_permission=False)],
                                       [command(contexts=[1], dm_permission=True)], guild=True).changes)

    def test_inputs_are_not_mutated(self):
        local = [command(options=[{"type": 3, "name": "text", "description": "Text"}])]
        original = copy.deepcopy(local)
        plan_commands(local, copy.deepcopy(local))
        self.assertEqual(local, original)

    def test_empty_tree_reports_deletions(self):
        self.assertTrue(plan_commands([], [command()]).has_deletions)

    def test_nsfw_changes_are_visible(self):
        self.assertEqual(plan_commands([command(nsfw=True)], [command()]).changes[0].fields,
                         ("nsfw",))

    def test_equivalent_number_bounds_do_not_trigger_changes(self):
        option = {"name": "amount", "type": 10, "description": "Amount", "min_value": 1}
        remote = {**option, "min_value": 1.0}
        self.assertFalse(plan_commands([command(options=[option])],
                                       [command(options=[remote])]).changes)
