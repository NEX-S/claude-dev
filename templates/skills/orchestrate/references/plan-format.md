# Plan format

Use one `plan.md` with Goal, Constraints, Done when, Tasks, and Notes. Preserve the complete requested outcome. This is a coordination document, not an executable format or a substitute for runtime state. The coordinator maintains it; a planner may create or revise it only as explicitly assigned.

## Task fields

Keep a flat task list. Written order aids reading; `deps` controls execution. Each task has:

| Field | Meaning |
| --- | --- |
| `id` | A unique, stable identifier used by dependencies and evidence. |
| `role` | One of `arch`, `dev`, `review`, `research`, `refine`, `plan`, written as the task prefix `(role)`. |
| Task text | A bounded action with settled implementation inputs; name unresolved decisions as separate upstream work. |
| `deps` | Existing predecessor IDs, or `[]`. The graph must be acyclic. Include producer/consumer and ordered shared-write dependencies. |
| `owns` | Explicit writable paths or resources, or `[]` for read-only work. Overlapping writes require one owner or a dependency; a consumer cannot read a concurrently changing interface. |
| `acceptance` | Observable output plus commands or inspection criteria that establish the task result in its integrated location. Write it inline or as a separate `Acceptance:` line. |
| `state` | `pending`, `running`, `blocked`, or `done`. Check the task box only for `done`. |

`pending` means awaiting dispatch; it becomes ready only when dependencies are done and required resources are available. `running` means dispatched or awaiting integration and acceptance, not necessarily a live worker. `blocked` means a concrete obstacle prevents completion. `done` means the coordinator has integrated and accepted the result. A worker's status and a task's state are separate facts.

Goal-level Done when items describe complete user outcomes, not merely task completion. Include shared integration checks and independent review when appropriate to risk. A reviewer verdict supplements verification; it cannot replace it.

## Runtime notes

For each dispatch, record the task ID, actual returned agent/session handle, workspace or worktree path and branch, and relevant input revision or file snapshot. Never invent a handle from a task name. Record native runtime status separately from task state.

For each result or failure, record changed artifacts, integration location, actual verification commands and results, the revision or identifiable file state covered, and remaining issues. File hashes can identify uncommitted output when a commit is inappropriate. Record decisions, blockers, changed dependencies, and invalidated evidence here rather than in a second progress ledger.

Do not pre-fill runtime handles or successful results in a new plan. Recovery must compare these notes with current artifacts and actual tool state, following the orchestrate skill.

## Example

The adapter contract is already agreed. The two adapters have disjoint implementations and tests; the real importer consumes both only after they are integrated. The final review is read-only.

```markdown
# Goal

Let the existing importer accept CSV and JSON files through its current command.

# Constraints

- Each adapter returns list[dict[str, str]] to the existing record validator.
- Keep the command's error and exit-code contract; use the standard library.
- The coordinator owns this plan and serial integration; workers own only their listed files.

# Done when

- [ ] The importer reads both formats through the current command and rejects invalid records as before.
- [ ] python3 -m unittest discover -s tests exits 0 on the integrated result.
- [ ] Review findings affecting the requested behavior or maintainability are resolved.

# Tasks

- [ ] (dev) `id: csv`; `deps: []`; `owns: [src/csv_input.py, tests/test_csv_input.py]`; `state: pending`
  Implement the CSV adapter against the agreed record contract.
  Acceptance: python3 -m unittest discover -s tests -p test_csv_input.py exits 0 and covers valid rows and malformed CSV.

- [ ] (dev) `id: json`; `deps: []`; `owns: [src/json_input.py, tests/test_json_input.py]`; `state: pending`
  Implement the JSON adapter against the same agreed record contract.
  Acceptance: python3 -m unittest discover -s tests -p test_json_input.py exits 0 and covers valid rows and malformed JSON.

- [ ] (dev) `id: integrate`; `deps: [csv, json]`; `owns: [src/importer.py, tests/test_importer.py]`; `state: pending`
  Connect both adapters to the existing command and validator.
  Acceptance: python3 -m unittest discover -s tests exits 0, including real command invocations for both formats, invalid records, and failure exit codes.

- [ ] (review) `id: inspect`; `deps: [integrate]`; `owns: []`; `state: pending`
  Review the integrated command path, contracts, and verification evidence.
  Acceptance: Return a review tied to the inspected file state with concrete findings or ACCEPT; the coordinator assigns any necessary fixes before final completion.

# Notes
```

`csv` and `json` may run together. If `csv` fails, `json` can still finish; `integrate` stays ineligible. A worker finishing `csv` on a separate branch does not release `integrate` until integration and acceptance are complete. If a terminal worker is still recorded as running, collect and verify its work before deciding to retry.
