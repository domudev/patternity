# Pattern store

Patterns are **personal to the user**, not the repo: they live at
`${PATTERNITY_HOME:-~/.patternity}/patterns/`, outside any project's git
history, so the same learned preferences follow you across repos. Two kinds
of file live there:

- `WALKING_DOC.md` — the index. One line per pattern, regenerated whenever a
  pattern is added or its state changes:
  `- [name](name.md) — state, N occurrences — one-line hook`
- `<kebab-case-name>.md` — one file per pattern.

## Pattern file frontmatter

```yaml
---
name: kebab-case-slug          # unique, becomes the filename stem
type: user | feedback | project | reference | override
state: observed | suspect | proven   # compile.py only reads proven
occurrences: 1
applies_to:
  tool: "*" | claude | cursor | copilot     # "*" = all tools
  glob: "**/*"                              # file scope, tool-dependent
  project: "*" | repo-name[,repo-name...]   # "*" = every project, or scope narrowly
target: null                   # override only: exact text to remove/suppress
---

Rule body in plain prose. State the rule, then:

**Why:** the reason/evidence (what recurred, what was said).
**How to apply:** when this should change agent behavior.
```

## State ladder (frequency-driven, not manual approval)

| occurrences | state    | compiled? |
|---|---|---|
| 1 | `observed` | no |
| 2 | `suspect`  | no |
| 3+ | `proven`  | yes, automatically |

Each time captured signal (`.patternity/signal.jsonl` in whichever project
you're in, or git history) matches an existing pattern, bump `occurrences`
and re-evaluate the state — this is the skill's job (`skills/patternity/SKILL.md`),
not `compile.py`, since deciding "is this the same pattern recurring" needs
judgment. An explicit standing statement ("always...", "never...", "from now
on...") skips straight to `proven` regardless of occurrence count — it isn't
an inference that needs corroborating, the user already said it once,
plainly.

There is no manual confirm step. Once a pattern is `proven`, `compile.py`
picks it up the next time it runs, and the skill runs it immediately after
promoting a pattern in the same turn — that's what keeps CLAUDE.md/AGENTS.md/
`.cursor/rules`/`.github/instructions` dynamically in sync instead of stale
until someone remembers to re-run a script. The safety net is git history on
the *compiled* files, not a pre-compile approval gate: every promotion is a
visible, revertible diff.

## Fine-grained scoping

`applies_to.project` lets a pattern stay narrow — e.g. a preference only
observed in one repo (`applies_to: {project: packlist}`) shouldn't leak into
every other project's CLAUDE.md just because the store is global. Default to
`"*"` only once a preference has actually shown up across more than one
project; scope to the observing project until then.

## Field notes

- `type: override` requires `target` — the literal string to suppress,
  copied verbatim from the source file. `compile.py` does exact-match
  removal; if the string isn't found, the override is flagged for manual
  review instead of silently skipped.
- Never hand-bump `occurrences`/`state` for something you haven't actually
  seen recur — that's the entire integrity guarantee of this system.
