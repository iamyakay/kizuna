import json
import os
import subprocess
import sys
import tempfile
import unittest
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    version("discord.py")
except PackageNotFoundError:
    HAS_DISCORD = False
else:
    HAS_DISCORD = True


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = Path(self.directory.name) / "test-bot"

    def cli(self, *args):
        environment = os.environ.copy()
        environment.pop("DISCORD_TOKEN", None)
        return subprocess.run(
            [sys.executable, "-m", "kizuna", *map(str, args)],
            capture_output=True, text=True, env=environment, timeout=20,
        )

    def test_help(self):
        result = self.cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doctor", result.stdout)

    def test_version(self):
        result = self.cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0.1.0", result.stdout)

    def test_init_json_and_existing_path_error(self):
        result = self.cli("init", self.project, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(json.loads(result.stdout)["created"]), self.project)
        result = self.cli("init", self.project, "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", json.loads(result.stdout)["error"])

    def test_invalid_scope_combination(self):
        result = self.cli("commands", "list", "--guild", "123", "--global")
        self.assertEqual(result.returncode, 2)

    def test_invalid_id(self):
        result = self.cli("commands", "list", "--guild", "abc")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    @unittest.skipIf(HAS_DISCORD, "Only applies when Discord dependencies are absent.")
    def test_missing_dependencies_produce_json_error(self):
        result = self.cli("doctor", "--project", self.project, "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("dependencies", json.loads(result.stdout)["error"])
        self.assertNotIn("Traceback", result.stderr)

    @unittest.skipUnless(HAS_DISCORD, "Install discord.py to load a generated bot.")
    def test_generated_project_loads_offline(self):
        self.assertEqual(self.cli("init", self.project).returncode, 0)
        result = self.cli("commands", "list", "--project", self.project, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = json.loads(result.stdout)["commands"]
        self.assertEqual([item["name"] for item in commands], ["ping"])
        result = self.cli("doctor", "--project", self.project, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
