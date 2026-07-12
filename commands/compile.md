---
description: Recompile adopted patterns into this project's CLAUDE.md/AGENTS.md/.cursor/.github
---

From the project root:

```
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/compile.py"
```

Usually automatic once a pattern hits `adopted`; use this to force a re-sync
(e.g. after editing a pattern by hand).
