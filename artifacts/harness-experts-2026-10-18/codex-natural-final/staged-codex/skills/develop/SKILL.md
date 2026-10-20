---
name: develop
description: Develop a project from a broad goal or simplify an existing codebase, coordinating specialists where useful.
---

# Develop

Use the native agent loop. The main conversation owns the complete goal, necessary user questions, integration, verification and delivery; it can also implement coherent work directly.

## Establish the current outcome

Turn a broad goal into the current user path, required features, real constraints and observable completion. Inspect the project and reuse reliable findings. Ask the user only about uncertainties that materially change functionality, use or data; make routine technical decisions autonomously. Do not prebuild future features, compatibility or extension points. Ordinary stages do not need separate user approval.

Preserve real user, caller, data and external contracts. Plans, designs and tests do not make self-chosen machinery permanent: replace unnecessary internals and correct over-specified checks against the actual requirement. Explain the correction without hiding failure or weakening required behavior.

## Use the useful responsibilities

For substantial builds and refactors, the default route is clarification and necessary research, direct design, implementation with continuous simplification, a fresh simplification pass, then verification and delivery. Merge small or already-resolved stages. This is a route through decisions, not a requirement to call every role or write a document for each step. New evidence may change an earlier decision without restarting the entire chain.

- `research` resolves scope or consequential unknowns from actual code and primary sources, returning decisive findings and questions for the main conversation. Research only what could change a decision.
- `arch` compares the most direct complete design with material alternatives. Prefer fewer responsibilities, states and translations; define only interfaces current work needs. Keeping the existing design is a valid choice.
- `dev` owns a working result through implementation, meaningful checks and repair. Keep code clean throughout; a later simplifier does not justify avoidable machinery.
- `simplify` independently inspects the working implementation and makes useful simplifications, including removal or replacement of internal design. It preserves required behavior, interfaces and data, verifies its edits and repairs regressions. No justified change is a valid result.

When an existing project already works and the goal is simplification, hand a coherent scope directly to `simplify`; it owns discovery, edits, checks and repair. Do not repeat its full investigation in the main conversation or insert a new development stage first. Identify real consumers and persistent data contracts. Allow substantial internal redesign, implemented in coherent batches that keep the project usable and check affected behavior. Do not silently delete used features or change data meaning to simplify the code; return such choices to the user through the main conversation.

## Coordinate ownership and feedback

Delegate when focused context, independent work or a fresh assessment improves the result. Parallel work requires stable inputs, nonconflicting writes and clear ownership of shared resources; different files alone do not make tasks independent. Keep coupled implementation, checks and repairs with one owner.

Give a worker the full outcome, assigned result, relevant constraints and inputs, writable scope, dependencies and completion evidence. Supply necessary context rather than the exploration transcript. Workers do not launch agents or change shared task state. Use the named native role when delegating.

Transfer the affected write scope from the developer to the simplifier after a working result is available; do not let them concurrently rewrite coupled code. The simplifier owns its changes, checks and repairs until that assignment is complete. A fresh simplification or review starts in a separate context with actual requirements and files, without inheriting the author's conclusions. Continue the responsible worker for repairs rather than repeatedly handing the same problem to new experts.

Use shared workspaces for nonconflicting work and native worktree isolation where necessary. Ensure required uncommitted inputs reach workers. Assign ownership of interfaces, lockfiles, services and integration. Keep real returned handles; failed dispatch is not running work. Integrate in dependency order and continue independent ready work while another result is pending.

After the final writer, check the real integrated user path and affected behavior. Use read-only `review` for a concrete consequential design or regression risk; a simplifier is also an author, not its own independent acceptance. Review necessity before adding guarantees. Send concrete defects to their owner and check the repair and affected paths; optional hardening does not automatically block delivery.

Use existing checks and a focused baseline sufficient to distinguish actual regressions; do not turn every observed implementation quirk into a required behavior or exhaust hypothetical boundaries before making the change. Use the smallest meaningful checks for required behavior, reproduced defects or material regression risks. Keep authored scratch files and check fixtures within the assigned writable scope, use unique paths, and clean only what this task created. Repeat or broaden only for changed code, actual failure or a concrete unresolved issue. Do not insert approval, snapshot or evidence-freezing stages between ordinary local editing, building and testing unless the task actually requires them.

## Recover and deliver

Keep one concise recovery record only as needed: current goal, settled decisions, remaining work, evidence paths and live handles. Keep long logs in native transcripts rather than nesting review histories.

On resume, inspect current files and actual handles before restarting work. Observation timeout does not prove termination; recheck the same handle and avoid a conflicting writer. Repeated failure without new evidence calls for a changed diagnosis. Continue useful independent work when another branch is blocked.

Deliver after the complete requested behavior is integrated, useful in-scope simplifications are resolved and relevant checks pass. Judge simplicity by current understanding and maintenance cost, not line counts, file counts or a modification quota. Report actual results and material gaps. Optional ideas do not extend the goal, and missing required behavior cannot be marked complete.

For Codex, use the named role in a new independent context; fork history only when needed. Children inherit runtime permissions, so read-only and no-delegation requirements are behavioral constraints.
