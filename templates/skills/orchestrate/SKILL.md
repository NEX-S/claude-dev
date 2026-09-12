---
name: orchestrate
description: Execute an agreed multi-task development plan using dependencies, parallel workers, integration checks, and resumable state. Use for planned execution or recovery, not a simple edit or unresolved architecture exploration.
---

# Orchestrate

Coordinate the agreed goal through one `plan.md` and the environment's available agent tools. Do not build a scheduler, assume a particular tool name, or change model, permissions, or concurrency limits. If worker tools are unavailable, execute ready tasks locally while keeping the same acceptance contract.

Use native subagents for bounded development tasks that need result-driven integration. For a stable, repeated flow that benefits from scripting, prefer an available native workflow runtime over a new runner. Verify the current tool catalog; a client version or documentation page alone does not establish availability. On Claude, load the native `workflow-authoring` skill when available and confirm how its current API loads the assigned roles and inherits model settings before using it.

Native workflows must preserve the acceptance and ownership rules below. Treat null or failed results as incomplete required work; do not discard them to produce a successful aggregate. Check replay semantics before allowing repeated writes, and revalidate artifacts after recovery. Let independent branches advance as their own prerequisites are accepted; use an all-results barrier only for a real join. Keep runtime state in the native harness and record only the task-to-handle mapping and acceptance evidence in the plan.

## Prepare the task graph

Read [the plan format](references/plan-format.md) before creating, validating, or resuming a plan. For a planning agent, supply a readable absolute reference path or the reference text along with the goal, constraints, and agreed interfaces. Resolve consequential missing decisions before dependent implementation; keep independent work moving.

One coordinator owns the shared plan, dispatch, and integration. Workers own only their assigned artifacts. Check the plan once at this boundary and when it changes:

- IDs are unique, all dependencies exist, and the graph has no cycle.
- Every task has a bounded action, an appropriate role, explicit writable ownership, and observable acceptance.
- Consumers depend on producers, including reads of interfaces another task is modifying. Shared files have one owner or ordered changes. Account for shared resources such as databases, ports, and generated output as well as paths.
- The full goal has acceptance coverage, including integration through the actual user entry point where relevant.

Do not assume parallel workers have filesystem isolation. Share a workspace only for disjoint changes against stable inputs. Use an available worktree or equivalent when separate checkouts are necessary; record its path and branch. Such isolation does not isolate shared services. Integrate separate branches serially.

## Dispatch ready work

Compute the ready set from `pending` tasks whose dependencies are all `done`. Exclude conflicts with running work and select mutually compatible candidates within actual available capacity. Dispatch independent ready tasks together when the benefit exceeds coordination overhead; do not select only the first unchecked row.

Give each worker:

- The bounded goal, constraints, role, and writable files or resources.
- Relevant input paths, settled interfaces, and dependency artifacts at the state the worker will consume.
- Acceptance checks and a request for changed paths, actual command/results, evidence revision or file state, and unresolved issues.
- An explicit notice that other workers are active, they must not revert others' changes, expand ownership, edit the shared plan, merge others' work, or spawn more agents.

After successful dispatch, record the returned agent/session handle and workspace, then mark `running`. Keep a task running while its completed worker result awaits integration and acceptance; record the worker's actual terminal status separately. A failed dispatch does not create a running task.

## Integrate and advance

Inspect each result and integrate it into the location successors will actually consume. Check ownership, resolve integration issues, and run the task's acceptance against that integrated state. Only then record evidence and set `done`; a completion message or passing tests on an isolated branch does not unlock dependents.

Recompute ready work immediately after each accepted integration. Do not wait for an unrelated slow task to finish an entire batch. Keep final integration checks dependent on all relevant producers; review evidence must identify the actual state inspected.

On failure, preserve the error, artifact state, and diagnosis. Mark the failed task `blocked`; its dependents remain ineligible while independent branches continue. Retry only with new diagnostic evidence or changed prerequisites, after confirming no previous writer remains active. Reset a retryable task to `pending` and record what changed.

If the goal, an interface, or a dependency changes, update affected tasks and invalidate evidence that no longer covers their inputs or results. Suspend conflicting work through the available tools and verify its status before replacement writes. Recheck affected acceptance before restoring `done`.

## Resume from evidence

Read the plan, inspect current files and Git state where available, and query recorded runtime handles. A `running` label is a note, not proof of a live process. An observation timeout or transient tool error is not proof of termination: query that same handle again or consult another authoritative runtime view.

Observe or take over a confirmed live worker. For a terminal worker, collect its result and inspect any partial changes before deciding what remains. Redispatch only after the previous handle is confirmed terminal or absent; uncertain state must not create duplicate writers. If a handle was never recorded, inspect the runtime's active jobs and the workspace before treating the task as stopped.

When nothing is ready, wait if a relevant handle is confirmed live. Otherwise investigate blocked tasks, missing evidence, or a malformed plan. Lack of ready work is not completion.

Finish only after every goal-level acceptance condition has current evidence in the integrated result. Record changes, checks, outcomes, the covered revision or file snapshot, and exact remaining gaps. The plan coordinates this evidence; it cannot replace the repository, runtime state, or verification results.
