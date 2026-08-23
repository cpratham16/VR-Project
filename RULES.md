# RULES.md

# Systematic Implementation Rules

This file is **mandatory prerequisite context** for the implementation plan.

## 1. Mandatory prerequisite

Before implementing **any iteration** from `IMPLEMENTATION_PLAN.md`:

1. Read this entire `RULES.md` file.
2. Read the current `CLAUDE.md` state.
3. Read the current `PROGRESS.md`.
4. Read the target iteration's Tasks and Acceptance criteria.
5. Inspect the existing implementation relevant to the iteration.
6. Do not begin implementation until these steps are complete.

`IMPLEMENTATION_PLAN.md` defines **what** must be built.  
`RULES.md` defines **how** every iteration must be executed.  
`CLAUDE.md` contains the live agent/project context.  
`PROGRESS.md` contains the permanent chronological implementation record.

## 2. Every iteration is an atomic execution unit

Each iteration must be executed independently in this exact order:

```text
READ RULES.md
    ↓
READ CLAUDE.md
    ↓
READ PROGRESS.md
    ↓
READ ITERATION TASKS + ACCEPTANCE CRITERIA
    ↓
INSPECT EXISTING IMPLEMENTATION
    ↓
IDENTIFY ASSUMPTIONS / DEPENDENCIES / RISKS
    ↓
PLAN MINIMAL CHANGE
    ↓
IMPLEMENT
    ↓
TEST / VERIFY
    ↓
VERIFY EVERY ACCEPTANCE CRITERION
    ↓
INSPECT FINAL DIFF
    ↓
UPDATE CLAUDE.md
    ↓
APPEND PROGRESS.md
    ↓
STOP ITERATION
```

Do not silently skip, reorder, or combine these stages.

## 3. Pre-implementation rules

Before coding:

- State important assumptions internally and surface them when they affect correctness.
- If the requirement has multiple plausible interpretations, do not silently choose one.
- If something is materially unclear, stop and ask for clarification.
- Identify dependencies on previous iterations.
- Inspect existing code before deciding how to implement the change.
- Prefer reuse of existing architecture and components.
- Prefer the simplest implementation that satisfies the requirements.
- Do not introduce speculative features.
- Do not perform unrelated refactors.
- Do not change behavior outside the iteration's scope unless required to unblock the iteration.

## 4. Implementation rules

While implementing:

- Make the smallest production-quality change that satisfies the iteration.
- Follow existing project architecture, conventions, naming, and patterns.
- Keep changes scoped to the current iteration.
- Add or update tests for behavior introduced or changed by the iteration.
- Preserve existing functionality unless the iteration explicitly requires changing it.
- Do not fabricate missing dependencies, APIs, test results, or implementation details.
- If a required change outside scope is discovered, document its necessity before making it.
- If a blocker prevents safe implementation, stop and record it rather than working around it silently.

## 5. Verification rules

An iteration is **not complete** merely because:

- the code compiles,
- the application starts,
- the implementation looks correct,
- or the requested files were changed.

Before completion:

1. Run all relevant automated tests.
2. Run applicable build, lint, type-check, integration, frontend/backend, or other verification commands.
3. Test important failure and edge cases introduced by the change.
4. Verify every acceptance criterion from `IMPLEMENTATION_PLAN.md`.
5. Check for regressions in existing functionality affected by the change.
6. Inspect the final diff for accidental or unrelated changes.
7. Remove unused imports, broken references, debugging statements, temporary files, and accidental artifacts introduced by the iteration.
8. Record the actual commands/checks and their results.

## 6. Acceptance criteria rule

The Acceptance criterion in `IMPLEMENTATION_PLAN.md` is the minimum functional target, but it is **not sufficient by itself**.

An iteration may be marked **Complete only when ALL of the following are true**:

- Every task for the iteration is implemented.
- Every stated acceptance criterion is satisfied.
- All applicable tests/checks pass.
- No known blocker remains for the iteration.
- The final diff contains no accidental/unrelated changes.
- Required documentation/tracking updates are complete.
- All applicable rules in this file were followed and are in place.

If even one required rule, acceptance criterion, verification check, or close-out requirement is not satisfied, the iteration must **not** be marked Complete.

Use:

- **Complete** — all requirements and rules are satisfied and verified.
- **Partial** — meaningful work is complete, but one or more requirements remain unfinished.
- **Blocked** — implementation cannot safely proceed because of a blocker.

Never mark an iteration Complete to hide a failing test, unresolved issue, skipped verification step, or missing requirement.

## 7. CLAUDE.md update rule

At the end of every iteration, overwrite the relevant `## Current Status` section in `CLAUDE.md`.

Use:

```text
## Current Status
- Active phase: [A/B/C/D/E]
- Last completed iteration: [ID — name]
- Status: [Complete / Partial / Blocked]
- What changed: [1-3 concise lines]
- New/modified modules: [list]
- Key decisions made: [bullets]
- Dependencies added/removed: [list or None]
- Verification performed: [tests/checks and result]
- Known issues / follow-ups: [bullets or None]
- Next iteration: [ID — name]
```

The status must reflect the **actual repository state**.

Do not stack historical snapshots in `CLAUDE.md`.

## 8. PROGRESS.md rule

`PROGRESS.md` replaces the previous `history.md`.

It is the permanent chronological implementation record.

After every iteration, append exactly one entry:

```text
### [YYYY-MM-DD] — Iteration [ID]: [Name]
**Status:** Complete / Partial / Blocked
**Summary:** 2-3 sentences describing what was actually built or changed
**Files touched:** [list]
**Tests/checks:** [commands/checks and results]
**Acceptance criteria:** [Pass / Partial / Fail, with evidence]
**Rules compliance:** [Pass / Partial / Fail]
**Decisions & rationale:** [bullets]
**Issues / blockers:** [bullets or None]
**Follow-ups carried to next iteration:** [bullets]
```

`PROGRESS.md` is append-only. Never rewrite, delete, or silently alter previous entries.

## 9. Final close-out is mandatory

The final action of every iteration must be:

1. Verify all acceptance criteria.
2. Verify all applicable rules are satisfied and in place.
3. Inspect the final diff.
4. Update `CLAUDE.md`.
5. Append the iteration record to `PROGRESS.md`.
6. Stop.

Do not start the next iteration during the same close-out.

## 10. Scope control

The test for every changed line is:

> Can this change be directly traced to the current iteration or to a documented dependency required to complete it?

If not, do not make the change.

Unrelated improvements may be mentioned in `PROGRESS.md` under follow-ups, but should not be implemented unless separately requested.

## 11. Blocker handling

If implementation or verification is blocked:

- Do not invent a successful result.
- Do not mark the iteration Complete.
- Record the exact blocker.
- Record what was completed.
- Record what remains.
- Set the iteration to `Partial` or `Blocked`.
- Carry the unresolved work into the appropriate follow-up.

## 12. Rule priority

When there is a conflict:

1. Explicit user requirement
2. `RULES.md`
3. `IMPLEMENTATION_PLAN.md`
4. Current project conventions
5. Agent preference

If the conflict cannot be safely resolved, stop and ask rather than guessing.
