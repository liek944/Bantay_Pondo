# Bantay Pondo — Agent Rules

## Before any task

Read SPEC.md and PROGRESS.md in full. If they conflict with my chat
message, the files win — flag the conflict and stop.

## Hard rules

- Implement exactly one milestone per session. Stop at its boundary.
- Never write ingestion code against an assumed schema. Run a discovery
  script, print the real columns and dtypes, show me, then write code.
- If you do not know a library's API, a PostGIS function signature, or a
  dataset's field name: say so and stop. Do not guess. A wrong guess here
  costs more than the question.
- No library outside the stack list in SPEC.md without asking.
- Never drop rows silently. Failed parses go to a rejects table with a
  reason. Failed spatial joins go to a review queue. Log counts in and out.
- No raw hex colors in /src. Tokens only.

## Definition of done for a milestone

### Backend (Milestones 1–9)

1. `ruff check` and `mypy --strict` pass on /pipeline and /api
2. `pytest` passes, including new tests for this milestone
3. Row-count assertions hold on the fixture dataset
4. PROGRESS.md updated
5. Committed on branch `milestone/NN-name` with a descriptive message

### Frontend (Milestones 10–14 / Phases 0–4)

1. `tsc --noEmit`, `eslint`, and `prettier --check` pass with 0 errors
2. `vitest run` passes, including new tests for this milestone
3. Zero raw hex colors in `/src` (only semantic Tailwind tokens)
4. Contract & fixture assertions hold against SPEC.md schemas
5. PROGRESS.md updated
6. Committed on branch `milestone/NN-frontend-<name>` with a descriptive message

## Do not

- Refactor code outside this milestone's scope
- "Improve" the schema, the scoring formula, or the API contract
- Mark work complete that you have not run
