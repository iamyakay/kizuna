import ast
import tempfile
import tomllib
import unittest
from pathlib import Path

from kizuna.errors import ProjectError
from kizuna.scaffold import create_project


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_creates_installable_project(self):
        target = create_project(self.root / "my-bot")
        metadata = tomllib.loads((target / "pyproject.toml").read_text())
        self.assertEqual(metadata["project"]["name"], "my-bot")
        self.assertTrue((target / "src/bot/cogs/ping.py").is_file())
        self.assertTrue((target / "tests/test_bot.py").is_file())
        self.assertFalse((target / ".env").exists())
        for source in target.rglob("*.py"):
            ast.parse(source.read_text())

    def test_existing_directory_is_never_overwritten(self):
        target = self.root / "existing"
        target.mkdir()
        marker = target / "keep.txt"
        marker.write_text("keep")
        with self.assertRaises(ProjectError):
            create_project(target)
        self.assertEqual(marker.read_text(), "keep")

    def test_invalid_name_leaves_no_partial_directory(self):
        with self.assertRaises(ProjectError):
            create_project(self.root / "bad name")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_parent_is_reported(self):
        with self.assertRaisesRegex(ProjectError, "parent"):
            create_project(self.root / "missing" / "my-bot")
