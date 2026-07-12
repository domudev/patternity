#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Record manual accept/reject decisions on patterns in the personal store.

The visualization can't write the store itself (it's a static file:// page),
so its accept/reject buttons just build the command that runs this. Accept
pins a pattern to compiled regardless of occurrence count; reject tombstones
it (never compiled, and the skill won't re-propose it); clear removes the
decision and lets the automatic state ladder take over again.

Usage (token form, as the viz emits it):
    uv run scripts/decide.py accept:uv-pref reject:tabs-not-spaces clear:foo

Edits the `decision` frontmatter field in ${PATTERNITY_HOME:-~/.patternity}/
patterns/<name>.md. Re-run compile.py afterwards to reflect it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import patterns_dir  # noqa: E402

VERBS = {"accept": "accepted", "reject": "rejected", "clear": None}


def set_decision(path: Path, value: str | None) -> None:
    """Drop any existing top-level `decision:` line from the frontmatter, then
    add the new one (unless clearing). Order-independent — the parser reads
    flat keys — so we just append after the frontmatter's other fields."""
    text = path.read_text()
    _, fm, body = text.split("---", 2)
    lines = [ln for ln in fm.splitlines() if not ln.strip().startswith("decision:")]
    if value is not None:
        # insert after the last top-level field, before any nested block —
        # simplest safe spot is right after `type:` which every pattern has.
        out, inserted = [], False
        for ln in lines:
            out.append(ln)
            if ln.startswith("type:") and not inserted:
                out.append(f"decision: {value}")
                inserted = True
        if not inserted:
            out.append(f"decision: {value}")
        lines = out
    path.write_text("---" + "\n".join(lines) + "\n---" + body)


def main(argv: list[str]) -> int:
    directory = patterns_dir()
    if not directory.exists():
        print(f"no pattern store at {directory}")
        return 1
    if not argv:
        print(__doc__)
        return 1

    changed = 0
    for token in argv:
        verb, _, name = token.partition(":")
        if verb not in VERBS or not name:
            print(f"skipping malformed token: {token!r} (want accept:NAME / reject:NAME / clear:NAME)")
            continue
        path = directory / f"{name}.md"
        if not path.exists():
            print(f"no such pattern: {name}")
            continue
        set_decision(path, VERBS[verb])
        print(f"{name}: {verb}")
        changed += 1

    if changed:
        print(f"\n{changed} decision(s) recorded — re-run compile.py to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
