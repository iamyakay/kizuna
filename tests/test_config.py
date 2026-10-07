import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kizuna.config import load_config, snowflake
from kizuna.errors import ConfigurationError


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        (self.root / "src").mkdir()
        self.write('factory = "bot.app:create_bot"\n')

    def write(self, content):
        (self.root / "kizuna.toml").write_text(content, encoding="utf-8")

    def test_default_settings(self):
        config = load_config(self.root)
        self.assertEqual(config.source, self.root / "src")
        self.assertEqual(config.token_env, "DISCORD_TOKEN")

    def test_unknown_settings_are_rejected(self):
        self.write('factory = "bot.app:create_bot"\ntoken = "secret"\n')
        with self.assertRaisesRegex(ConfigurationError, "Unknown"):
            load_config(self.root)

    def test_toml_error_does_not_echo_values(self):
        self.write('factory = "private-secret\n')
        with self.assertRaises(ConfigurationError) as result:
            load_config(self.root)
        self.assertNotIn("private-secret", str(result.exception))

    def test_source_cannot_escape_project(self):
        self.write('factory = "bot.app:create_bot"\nsource = ".."\n')
        with self.assertRaises(ConfigurationError):
            load_config(self.root)

    def test_environment_wins_over_dotenv(self):
        (self.root / ".env").write_text("DISCORD_TOKEN=file-value\n", encoding="utf-8")
        with patch.dict(os.environ, {"DISCORD_TOKEN": "environment-value"}):
            self.assertEqual(load_config(self.root).token(), "environment-value")

    def test_empty_environment_is_not_replaced(self):
        (self.root / ".env").write_text("DISCORD_TOKEN=file-value\n", encoding="utf-8")
        with patch.dict(os.environ, {"DISCORD_TOKEN": ""}):
            with self.assertRaises(ConfigurationError):
                load_config(self.root).token()

    def test_dotenv_does_not_modify_process_environment(self):
        (self.root / ".env").write_text("DISCORD_TOKEN=file-value\n", encoding="utf-8")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(load_config(self.root).token(), "file-value")
            self.assertNotIn("DISCORD_TOKEN", os.environ)

    def test_token_validation_does_not_echo_value(self):
        with patch.dict(os.environ, {"DISCORD_TOKEN": "Bot private-secret"}):
            with self.assertRaises(ConfigurationError) as result:
                load_config(self.root).token()
        self.assertNotIn("private-secret", str(result.exception))

    def test_snowflake_boundaries(self):
        self.assertEqual(snowflake(str(2**64 - 1)), 2**64 - 1)
        for value in (0, -1, 2**64, "abc", "1.5", True, "１２３"):
            with self.subTest(value=value), self.assertRaises(ConfigurationError):
                snowflake(value)

    def test_discovers_config_from_child_directory(self):
        previous = Path.cwd()
        try:
            os.chdir(self.root / "src")
            self.assertEqual(load_config().root, self.root)
        finally:
            os.chdir(previous)

    def test_explicit_project_does_not_fall_back_to_parent(self):
        with self.assertRaises(ConfigurationError):
            load_config(self.root / "src")
