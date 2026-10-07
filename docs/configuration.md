# Configuration

Kizuna reads `kizuna.toml` from the project root. With no `--project` argument, it searches upward from the current directory. An explicit project path must contain its own configuration file.

| Setting | Default | Meaning |
| --- | --- | --- |
| `factory` | Required | Import path such as `bot.app:create_bot` |
| `source` | `src` | Source directory relative to the project root |
| `token_env` | `DISCORD_TOKEN` | Environment variable containing the bot token |
| `guild_id` | Unset | Default command deployment guild |

Unknown settings are rejected so a misspelled key does not silently change behavior. The source directory must exist inside the project. IDs can be TOML strings or integers and must be positive 64-bit values.

```toml
factory = "my_bot.app:create_bot"
source = "src"
token_env = "MY_BOT_TOKEN"
guild_id = "123456789012345678"
```

For online commands, Kizuna checks the configured environment variable first, then the project root's `.env`. An explicitly empty environment variable is treated as missing and does not fall back to the file. Variable interpolation is disabled, and the file does not modify process environment variables.

Supply only the raw bot token, without a `Bot` or `Bearer` prefix. Kizuna does not accept tokens as command-line arguments or store them in TOML.

Offline checks load your Python factory and extensions. Register all commands before returning the bot. If command loading lives only in `setup_hook`, move it to a shared factory so offline and online inspection use the same definitions. Do not start the bot inside the factory.

Kizuna restores the Python import path after loading a project. Imported modules remain in Python's module cache. When using the Python API with multiple projects that share module names, inspect them in separate processes.

`doctor --online` verifies token authentication and access to the configured guild. It does not verify every channel permission, gateway connectivity, or privileged intent approval in the Developer Portal.
