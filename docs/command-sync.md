# Command syncing

Kizuna handles slash commands, command groups, and user/message context menus. It works with the tree returned by your factory and uses discord.py's `fetch_commands` and `sync` methods. Discord authentication, transport retries, and rate limits are handled by discord.py.

## Scope

The target is selected in this order:

1. `--global` explicitly selects global commands.
2. `--guild ID` selects that guild.
3. `guild_id` in `kizuna.toml` selects the configured guild.
4. Otherwise, commands target the global scope.

Guild operations call `copy_global_to` before inspecting the local tree. Existing guild-specific definitions are retained unless a global definition has the same name and type. This follows discord.py's behavior and makes a development guild a convenient place to test global commands.

Global and guild commands are separate remote scopes. Syncing one does not clear the other. If you previously registered commands in both scopes, both can appear in your test guild.

## Comparison

Commands are matched by name and command type. Renaming one therefore appears as a removal and an addition. Server-generated IDs and versions are ignored. Option order is preserved, including nested groups and choices. Empty localization maps and optional field defaults are normalized.

The diff reports which top-level fields changed. It compares permissions and NSFW flags explicitly because discord.py's remote `AppCommand.to_dict()` does not include them.

For global commands, explicit contexts and installation types are compared without regard to order. When the local definition leaves either unset, Kizuna treats the application's defaults as unmanaged and does not report a change for that field alone. Set these values explicitly if you want Kizuna to detect drift. A sync triggered by another change still sends discord.py's full command payload, including its default handling.

Command translators are rejected in this release because untranslated local payloads cannot be compared reliably with registered translations. Application entry point commands and other unsupported command types block sync planning rather than being removed by a bulk overwrite.

## Applying changes

```text
kizuna commands diff --guild 123456789012345678
kizuna commands sync --guild 123456789012345678
kizuna commands sync --guild 123456789012345678 --apply
```

The sync command fetches the remote tree again and computes a fresh plan. It does not apply a previously saved plan. If commands already match, it skips the write.

A bulk sync replaces the entire selected scope. Add `--allow-delete` when a reviewed change removes commands. Clearing a scope also requires `--allow-empty`. Other deployments can still modify Discord between the read and write; run a single command deployment at a time for a given application and scope.

```text
kizuna commands diff --check --json
```

This emits the plan as JSON and exits with `1` when changes exist. It exits with `2` on a configuration or request error. A successful sync does not prove that the bot's interaction handlers work; run the bot and test its commands in a development guild.

References: [discord.py command trees](https://discordpy.readthedocs.io/en/stable/interactions/api.html#commandtree), [Discord application commands](https://docs.discord.com/developers/interactions/application-commands).
