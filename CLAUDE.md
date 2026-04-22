# Claudex

This repo is the source of the global scaffolding installed to `~/.claude/` and `~/.codex/` by `./install.sh`.

Source → artifact:

- `templates/AGENTS.md` → `~/.claude/AGENTS.md` (copy), `~/.codex/AGENTS.md` (symlink)
- `templates/agents/*.md` → `~/.claude/agents/*.md`

The scaffolding is global-only. Do not reintroduce `AGENTS.md`, `@AGENTS.md`, or `.claude/agents/` at the project root — that would put claudex under its own published rules and double-load them on every `/memory` dump.

Re-run `./install.sh` after edits; restart Claude Code / Codex to reload.
