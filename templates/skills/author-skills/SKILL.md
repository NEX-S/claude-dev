---
name: author-skills
description: Create, revise, or evaluate reusable agent skills with precise triggers, focused instructions, and observable task results. Do not use for ordinary application edits or a one-off prompt that needs no reusable skill.
---

# Author skills

Build the smallest reusable instruction package that improves the requested workflow. Start with the user's actual use cases, existing skill and callers if any, target environment, and desired outputs. Preserve the user's scope, location, authorization, and supported configuration. Ask only for missing inputs that materially change the skill's behavior.

## Define the boundary

Write down representative requests that should activate the skill and nearby requests that should not. Put the main capability and positive trigger early in `description`; include a concise exclusion where confusion is likely. A description is routing metadata, not an inventory of every step. Explicit invocation should still follow the user's current task and constraints.

Use a lowercase hyphenated directory name and a matching `name` of at most 64 characters. Start `SKILL.md` with YAML frontmatter containing `name` and `description`; use only additional metadata supported by the target platform.

## Write only useful instructions

- Put the purpose, required inputs, consequential workflow choices, constraints, and expected output in `SKILL.md`. Assume the agent already knows general programming and tool use.
- Keep short skills self-contained. Move substantial conditional procedures, schemas, or examples into a reference only when it reduces irrelevant context. Link directly with a relative path and state when to read it; resolve resources from the skill's directory, not the task's current directory. Avoid duplicated rules and chains of references.
- Add a script only for repeated deterministic work or a fragile operation whose correctness it materially improves. Use existing tools and dependencies first. Run any script you create or change.
- Set the specificity according to the operation's actual risk. Give decision criteria for open work and exact invariants for fragile steps. Preserve needed boundary validation, cleanup, and failure evidence without adding speculative recovery branches.
- Mention a tool or another skill only if the workflow needs it and the target environment provides it. Instructions do not grant permissions or imply unavailable capabilities. Define meaningful failure or stopping conditions for retries and external mutations.
- Keep assets only when they belong in the output. Do not add placeholder folders, generic tutorials, duplicated quick references, or extra metadata without a concrete consumer.

## Validate the result

Check the target platform's skill format, discovery location, frontmatter, relative links, and any executable resources. Use an available official validator where applicable, and state if it cannot run. Parsing proves structure; discovery tests prove loading. Neither proves that the agent makes the intended decisions.

For a new workflow or a substantive change, use realistic requests covering positive activation, adjacent non-applicability, explicit invocation, an abnormal or missing-input case, and a representative completed artifact. Observe actual task outcomes, scope, and failure handling instead of checking for prescribed words or an exact tool sequence. Test at the complexity and risk of the skill; do not require a benchmark suite for a wording correction.

When useful, have the coordinator assign an independent evaluator the skill, realistic request, and minimum raw artifacts without revealing the expected solution. Use an isolated workspace and record model/version, relevant inputs, checks, and outcomes. Do not infer broad improvement from one successful example; a comparative claim needs a controlled baseline and repeated trials.

Use demonstrated failures to make narrow corrections, then rerun affected cases. Remove any rule or resource whose purpose the evidence does not support. Return the skill path, trigger boundary, resources added or changed, observed validation results, and exact unverified areas.
