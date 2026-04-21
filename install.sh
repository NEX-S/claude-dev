#!/usr/bin/env bash
set -euo pipefail

# Install AGENTS.md + 4 subagents globally for Claude Code and Codex.
# Idempotent: existing files are backed up with a timestamp suffix.

SRC="$(cd "$(dirname "$0")" && pwd)"
STAMP=".bak.$(date +%Y%m%d-%H%M%S)"

backup() {
  local f="$1"
  if [[ -L "$f" ]]; then
    rm "$f"
  elif [[ -e "$f" ]]; then
    mv "$f" "${f}${STAMP}"
    echo "  backup: $f -> ${f}${STAMP}"
  fi
}

echo "Source: $SRC"

# Claude Code
mkdir -p ~/.claude/agents
backup ~/.claude/AGENTS.md
cp "$SRC/AGENTS.md" ~/.claude/AGENTS.md
echo "  wrote: ~/.claude/AGENTS.md"

backup ~/.claude/CLAUDE.md
printf '@AGENTS.md\n' > ~/.claude/CLAUDE.md
echo "  wrote: ~/.claude/CLAUDE.md"

for a in arch dev plan refine research review; do
  backup ~/.claude/agents/$a.md
  cp "$SRC/.claude/agents/$a.md" ~/.claude/agents/$a.md
  echo "  wrote: ~/.claude/agents/$a.md"
done

# Codex (shares the same AGENTS.md)
mkdir -p ~/.codex
backup ~/.codex/AGENTS.md
ln -s ~/.claude/AGENTS.md ~/.codex/AGENTS.md
echo "  link:  ~/.codex/AGENTS.md -> ~/.claude/AGENTS.md"

echo
echo "Done. Restart Claude Code / Codex to load."
