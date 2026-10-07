# Contributing

Start with a reproducible bug or a specific workflow that takes too many steps. Keep changes focused and include a regression test when behavior changes.

Use Python 3.11 or newer in a dedicated virtual environment:

```text
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m ruff check .
python -m build
```

Discord tests use real discord.py command objects with mocked network methods. Do not add tests that need a real token, server, or internet connection. Keep snapshots and fixtures free of credentials.

Source files live under `src/kizuna`. CLI adapters belong in `commands`, command comparison in `diff.py`, and generated bot files in `templates/bot`. Keep behavior reusable from Python instead of putting all of it in argument handlers.

Write a concise conventional commit title such as `fix: preserve command permissions in remote diffs`. Explain the concrete failure and resulting behavior in the pull request. Prefer clear names and small functions. This project avoids code comments and em dashes.

The package name is `kizuna-discord`, the import name is `kizuna`, and the terminal command is `kizuna`. Publishing a release requires checking package name availability, running the full test suite and wheel smoke test, and testing sync against a dedicated Discord development application.
