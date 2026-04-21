# AGENT

Minimal, opinionated prompt scaffolding for Claude Code and Codex. Produces obviously-correct, elegantly-simple code and architecture by design.

## What's here

```
AGENTS.md              # Mission, non-negotiables, role split, pipelines (content)
CLAUDE.md              # Claude Code entry — one line: @AGENTS.md
.claude/agents/
  arch.md              # Architecture specialist
  dev.md               # Implementation + self-verification specialist
  plan.md              # Requirement → plan.md for unattended execution
  refine.md            # Empirical refinement of an existing implementation
  research.md          # Domain investigation, comparison, recommendation
  review.md            # Severity × Confidence critique with BLOCK/INVESTIGATE/ACCEPT verdict
install.sh             # Install to ~/.claude and ~/.codex
```

## Install

```bash
./install.sh
```

Pushes to:

- `~/.claude/CLAUDE.md` (imports `@AGENTS.md`)
- `~/.claude/AGENTS.md` (the real content)
- `~/.claude/agents/{arch,dev,plan,research,review}.md`
- `~/.codex/AGENTS.md` → symlink to `~/.claude/AGENTS.md`

Idempotent. Existing files are backed up with a timestamp suffix.

Re-run after any change in this repo.

## CLAUDE.md vs AGENTS.md

| File | Read by | Role |
|------|---------|------|
| `CLAUDE.md` | Claude Code (native) | One-line entry: `@AGENTS.md` |
| `AGENTS.md` | Codex (native); Claude Code (via import) | Actual mission, non-negotiables, pipelines |

Claude Code does **not** read `AGENTS.md` directly. It reads `CLAUDE.md`, which imports `AGENTS.md` via `@AGENTS.md`. This gives one source of truth that both tools share.

## How to use

### 1. Just describe the task (default)

The main assistant routes to the right subagent(s) based on their `description` fields.

```
给 packages/foo 加个 rate limiter，60 req/min per-IP，Redis 做 counter
```

Main reads "multi-file change touching external dependency" → runs `arch → dev → review`.

### 2. Explicit delegation (when needed)

```
用 arch subagent 先出设计，别直接写代码
```

### 3. Prompting Contract (recommended for non-trivial work)

```
Goal: [one sentence]
Context: [relevant paths, current state, what's already known]
Constraints: [stack, perf, compat, dependency edges]
Done when: [observable, checkable outcomes]
```

This maps directly onto what `arch` / `dev` / `plan` consume.

## Pipelines

Declared in `AGENTS.md`. Main assistant picks automatically based on task shape:

| Task | Pipeline |
|------|----------|
| Feature or bugfix | `dev → review` |
| Architecture / multi-module change | `arch → dev → review` |
| Greenfield / 0-to-1 | `parallel research (per domain) → arch → plan → dev → review` |
| Algorithm / implementation improvement | `refine` (optionally → `dev → review`) |
| Long-running / unattended | `plan → loop(next task in plan.md)` |

## Greenfield / 0-to-1 workflow

For starting a new project where the approach isn't yet decided, use parallel research to de-risk the unknowns before architecture.

**Order: `research (parallel) → arch → plan → dev → review`.** Research comes first — you can't design what you haven't scoped. Plan comes after arch — task decomposition is cheap only once the shape is fixed.

**Parallel research is native, not DIY.** Claude Code's main assistant can launch multiple subagents in a single turn; they run concurrently in isolated context windows and return notes independently. Anthropic's [multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) documents ~90% latency reduction from this pattern. Important limit: subagents cannot themselves spawn subagents — parallel fan-out must originate at the main assistant.

Invocation example:

```
Goal: 从零做一个 X（一句话描述）
需要先做三路并行调研（main assistant 开三个 research subagent 并行跑）：
- Domain A: [比如数据库选型，decision metric: write QPS + p99 延迟]
- Domain B: [比如 API 范式，decision metric: 客户端 SDK 工程量]
- Domain C: [比如部署形态，decision metric: 运维复杂度]

三份调研回来后用 arch 综合，给出 2-3 个整体方案供我选择。
Constraints: [...]
Done when: 我选定方案后，plan agent 写 plan.md。
```

Main assistant fan-outs three `research` calls in one turn, collects the notes, delegates to `arch` with all three as context. Arch's worst-case-condition rule (see `arch.md` workflow step 2) makes the tradeoffs explicit. You either let arch pick or tell it to present options in the Prompting Contract.

If you don't want to choose up front, replace the last Done-when with: "arch presents 2-3 options with tradeoffs; I select one before plan runs."

## Long-running / unattended workflow

For tasks that span hours or where session resilience matters, use the `plan + loop` pattern.

**Step 1.** Have the plan agent write `plan.md` at the project root:

```
用 plan agent 把这个需求转成 plan.md：
Goal: 把 ingestion 去重从 Redis SET 迁到 Bloom Filter
Constraints: 假阳性 < 0.1%, 不增 p99 延迟, 仅用现有依赖
Done when: bench 显示内存 < 2GB, 现有 dedup 测试全绿, review 返回 ACCEPT
```

**Step 2.** Start `/loop` in auto-accept mode (`shift+tab` toggles):

```
/loop 15m read plan.md, run the next unchecked task using the agent named by its prefix, check it off when its done-condition is satisfied, append a one-line note to # Notes. If all items under # Done when are checked, stop.
```

**Step 3.** Leave it running. Each iteration:

- starts with a clean context
- reads `plan.md` from disk
- advances one task
- updates the file

Crash recovery comes for free: state lives on disk.

**Research tasks don't need `/loop`.** The research agent has its own internal loop (with a hard budget). Just give it the question + decision metric:

```
Goal: 找一个在 1M 稀疏向量上 recall@10 ≥ 0.95 且 p99 < 2ms 的 ANN 索引
Baseline: FAISS-IVF
Hard budget: 5 实验
```

## Per-project overrides

When a specific repo needs rules that differ from the global mission (safety-critical code needs aggressive validation; some teams prefer strict DRY over AHA), drop a `./CLAUDE.md` at the repo root. It's loaded automatically and concatenated with the global rules; more specific wins on conflicts.

Same for subagents: `./.claude/agents/foo.md` in a repo overrides `~/.claude/agents/foo.md` of the same name.

Default case: no per-repo files. Global rules apply everywhere.

## Philosophy

Read `AGENTS.md`. Short version: code is liability, delete beats add, AHA over strict DRY/SOLID, validate at boundaries only, fail loudly, names over comments, obviously-correct over decoratively-abstract.
