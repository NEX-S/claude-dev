---
name: develop
description: Develop a project from a broad goal or simplify an existing codebase, coordinating specialists where useful.
---

# Develop

Use the native agent loop. The main conversation owns the complete goal, necessary user questions, integration, verification and delivery; it can also implement coherent work directly.

## Establish the current outcome

Turn a broad goal into the current user path, required features, real constraints and observable completion; state that understanding briefly in the main conversation. Inspect the project and reuse reliable findings. Ask the user only about uncertainties that materially change functionality, use or data; make routine technical decisions autonomously. Do not prebuild future features, compatibility or extension points. Ordinary stages do not need separate user approval.

For project-wide simplification, establish a concrete product or architecture outcome and assess the whole assigned scope before selecting work. Prioritize unnecessary responsibilities and repeated mechanisms that drive overall complexity. Do not let a worker substitute a convenient local cleanup for that broader outcome; existing features or internal guarantees need a current purpose, not merely callers or old tests.

Preserve real user, caller, data and external contracts. Plans, designs and tests do not make self-chosen machinery permanent: replace unnecessary internals and correct over-specified checks against the actual requirement. Explain the correction without hiding failure or weakening required behavior.

## Use the useful responsibilities

The default route is to clarify the current outcome, get the simplest complete user path working early, self-simplify, run meaningful checks and deliver. Research, design, independent simplification and review serve concrete decisions or problems; project size alone does not require them. Reuse settled findings instead of repeating stages. New evidence may change an earlier decision without restarting the entire chain. Do not create stage documents or call roles merely to complete a process.

- `research` resolves scope or consequential unknowns from actual code and primary sources, returning decisive findings and questions for the main conversation. Research only what could change a decision.
- `arch` compares the most direct complete design with material alternatives. Prefer fewer responsibilities, states and translations; define only interfaces current work needs. Keeping the existing design is a valid choice.
- `dev` owns a working result through implementation, self-simplification, meaningful checks and repair. Before handing off, personally inspect the actual path and your changes, apply worthwhile cleanup, then check affected behavior. Keep useful abstractions and deliberate duplication. This stays in the same assignment without a separate report or role; a later simplifier does not excuse avoidable machinery.
- `simplify` independently inspects the working implementation and makes useful simplifications, including removal or replacement of internal design. It preserves required behavior, interfaces and data, verifies its edits and repairs regressions. No justified change is a valid result.

When an existing project already works and the goal is simplification, hand a coherent scope directly to `simplify`; it owns discovery, edits, checks and repair. Do not repeat its full investigation in the main conversation or insert a new development stage first. Identify real consumers and persistent data contracts. Allow substantial internal redesign, implemented in coherent batches that keep the project usable and check affected behavior. Do not silently delete used features or change data meaning to simplify the code; return such choices to the user through the main conversation.

## Coordinate ownership and feedback

Delegate when focused context, independent work or a fresh assessment improves the result. Parallel work requires stable inputs, nonconflicting writes and clear ownership of shared resources; different files alone do not make tasks independent. Keep coupled implementation, checks and repairs with one owner.

Give a worker the full outcome, assigned result, relevant constraints and inputs, writable scope, dependencies and completion evidence. Supply necessary context rather than the exploration transcript. Workers do not launch agents or change shared task state. Use the named native role when delegating.

When a separate simplifier is warranted, transfer the affected write scope from the developer after a working result is available; do not let them concurrently rewrite coupled code. The simplifier owns its changes, checks and repairs until that assignment is complete. A fresh simplification or review starts in a separate context with actual requirements and files, without inheriting the author's conclusions. Continue the responsible worker for repairs rather than repeatedly handing the same problem to new experts.

Use shared workspaces for nonconflicting work and native worktree isolation where necessary. Ensure required uncommitted inputs reach workers. Assign ownership of interfaces, lockfiles, services and integration. Keep real returned handles; failed dispatch is not running work. Integrate in dependency order and continue independent ready work while another result is pending.

After the final writer, inspect the integrated code and actual check outputs against the required user path. Reuse results that still cover the current code, inputs and environment; run only missing or invalidated checks. A worker's summary is not evidence, but independent acceptance does not require repeating its investigation or passing checks. Use independent `simplify` for concrete structural complexity or an explicit cleanup goal, and read-only `review` for a concrete consequential design or regression risk. Send concrete defects to their owner and check the repair and affected paths; optional hardening does not automatically block delivery.

Use existing checks and a focused baseline sufficient to distinguish actual regressions; do not freeze incidental quirks or exhaust hypothetical boundaries. After a change, rerun checks for the behavior it can affect; an unrelated edit or rebuilt binary alone does not justify repeating a full matrix or benchmark. Honor explicit project and release gates. Keep authored scratch files and check fixtures within the assigned writable scope, use unique paths, and clean only what this task created. Do not insert approval, snapshot or evidence-freezing stages between ordinary editing, building and testing unless the task actually requires them.

## Recover and deliver

Keep one concise recovery record only as needed: current goal, settled decisions, remaining work, evidence paths and live handles. Keep long logs in native transcripts rather than nesting review histories.

On resume, inspect current files and actual handles before restarting work. Observation timeout does not prove termination; recheck the same handle and avoid a conflicting writer. After a failed tool action, use the actual error or current state to correct the next attempt; repeated failure calls for a changed diagnosis. Continue useful independent work when another branch is blocked.

Deliver after the complete requested behavior is integrated, the author has removed obvious unnecessary machinery and relevant checks pass. Repair known failures of required behavior or data integrity; unknown bugs do not require a new audit, hardening or cleanup round. Treat extreme simplicity as a design preference, not a demand to keep searching for a better implementation. Judge simplicity by current understanding and maintenance cost, not line counts, file counts or a modification quota. Report actual results and material gaps. Optional ideas do not extend the goal, and missing required behavior cannot be marked complete.

For Grok, select a named role using the actual tool schema and carry required constraints in its brief; do not assume parent --rules inheritance.

## Native Grok dispatch

Use the actual tool schema to select the named research, arch, dev, simplify or review role. Current Grok documents `subagent_type` on `spawn_subagent`; prefer that direct route when exposed. A free-text request to act as reviewer does not apply the named role's tool restrictions.

If the available tool lacks a named-role selector, native Workflow supports `agent(prompt, #{ agent_type: "review" })` (likewise research/arch/dev/simplify). Read the bundled create-workflow reference only when using that route. One focused assignment needs only an inline call; independent jobs may use parallel(), accounting for its whole-group barrier. Omit model/effort overrides and set agent_budget to the actual work; authored workflows cannot use fork_context.

Use actual task handles and native completion notifications. A Workflow run handle is distinct from its child agent_id. Inspect success, cancelled and output: complete(r), CLI exit 0 and validate_only do not prove a successful child result.

Continue the same responsibility through supported native messaging. Workflow resume_from with a completed child in the same session and agent_type creates a successor with transcript/tool state, not a still-live original process. If continuation is unavailable, hand off the necessary facts explicitly instead of inventing a handle.
