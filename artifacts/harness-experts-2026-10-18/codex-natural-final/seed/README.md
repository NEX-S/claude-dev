# Local task ledger

Use only the Python standard library. `python3 tasks.py --db PATH COMMAND`
accepts `add TITLE`, `list`, `done ID`, and `export`.

`add` prints the new integer ID. `list` prints a JSON array ordered by ID,
with exactly `id`, `title`, and boolean `done`. `done` completes an existing
record. `export` prints ordered Markdown lines `- [ ] TITLE` / `- [x] TITLE`.
Titles are preserved, including surrounding spaces and Unicode; a whitespace-only
title is invalid. Data persists across calls. Missing task IDs are errors.
All user-operation failures use a nonzero exit, diagnostic stderr and no
success stdout. A fresh database is created automatically.

`existing.db` is the database already in use. Its `tasks` table has `id`
INTEGER PRIMARY KEY AUTOINCREMENT, `title` TEXT NOT NULL and `done` INTEGER
NOT NULL DEFAULT 0 CHECK(done IN (0,1)). Preserve its data and compatibility.
The application has no library callers or other storage backends. Its internal
classes, module boundaries and settings are implementation choices.
