# Pattern store

Patterns are **personal to the user**, not the repo: they live at
`${PATTERNITY_HOME:-~/.patternity}/patterns/`, outside any project's git
history, so the same learned preferences follow you across repos. Two kinds
of file live there:

- `WALKING_DOC.md` — the index. One line per pattern, regenerated whenever a
  pattern is added or its state changes:
  `- [name](name.md) — state, N occurrences — one-line hook`
- `PROFILE.md` — a short narrative synthesis of proven patterns grouped by
  `cluster`, regenerated the same way. Not a new instruction source (that's
  still individual compiled patterns) — this is the human/agent-readable
  "who is this user" summary, shown as a panel in the visualization.
- `<kebab-case-name>.md` — one file per pattern.

## Pattern file frontmatter

```yaml
---
name: kebab-case-slug          # unique, becomes the filename stem
type: user | feedback | project | reference | override
state: observed | suspect | proven   # compile.py only reads proven
occurrences: 1
cluster: tooling | code-style | workflow | communication | testing | ...
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

## Clustering into a profile

`cluster` groups patterns by theme so they read as a profile, not a pile of
unrelated rules. There's no fixed enum — the skill picks a short existing
cluster name when a new pattern fits one, and only mints a new one when
nothing fits, so the set of clusters stays small and stable (a handful,
not one per pattern). Whenever clusters change, regenerate `PROFILE.md`:
group proven patterns under a `## <cluster>` heading each, with a
sentence or two of synthesis per cluster, not just a re-listing of the
pattern bullets — that's the difference between a profile and an index.

## Field notes

- `type: override` requires `target` — the literal string to suppress,
  copied verbatim from the source file. `compile.py` does exact-match
  removal; if the string isn't found, the override is flagged for manual
  review instead of silently skipped.
- Never hand-bump `occurrences`/`state` for something you haven't actually
  seen recur — that's the entire integrity guarantee of this system.
