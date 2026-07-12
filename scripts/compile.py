#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Compile proven patterns into each tool's native format, for whichever
project you run this from.

Patterns are personal to the user (${PATTERNITY_HOME:-~/.patternity}/patterns/),
not the repo — this script reads that global store but writes compiled
output into the current working directory's project files. Deterministic
templating, no AI. Idempotent: re-running only replaces the marked section
it owns, everything else in the target file is left alone. No frontmatter
YAML parser dependency — the schema is small and controlled
(patterns/_SCHEMA.md), so a hand-rolled parser is a few lines vs. a new dep.

Run from the project you want compiled patternity patterns applied to:
    uv run /path/to/patternity/scripts/compile.py
"""
import fnmatch
import os
import re
from pathlib import Path

BEGIN = "<!-- patternity:begin -->"
END = "<!-- patternity:end -->"


def patterns_dir() -> Path:
    home = os.environ.get("PATTERNITY_HOME", str(Path.home() / ".patternity"))
    return Path(home) / "patterns"


def current_project() -> str:
    return Path.cwd().name


def parse_pattern(path: Path) -> dict:
    text = path.read_text()
    _, fm, body = text.split("---", 2)
    data: dict = {}
    applies_to: dict = {}
    in_applies_to = False
    for line in fm.splitlines():
        if not line.strip():
            continue
        if line.startswith("applies_to:"):
            in_applies_to = True
            continue
        if in_applies_to and line.startswith("  "):
            k, _, v = line.strip().partition(":")
            applies_to[k.strip()] = v.strip().strip('"')
            continue
        in_applies_to = False
        k, _, v = line.partition(":")
        data[k.strip()] = v.strip().strip('"')
    data["applies_to"] = applies_to
    data["body"] = body.strip()
    data["name"] = path.stem
    return data


def in_scope(p: dict, project: str) -> bool:
    project_scope = p["applies_to"].get("project", "*")
    return project_scope == "*" or project in project_scope.split(",")


def load_proven(project: str) -> tuple[list[dict], list[dict]]:
    additive, overrides = [], []
    directory = patterns_dir()
    if not directory.exists():
        return additive, overrides
    for path in sorted(directory.glob("*.md")):
        if path.name.startswith("_") or path.name == "WALKING_DOC.md":
            continue
        p = parse_pattern(path)
        if p.get("state") != "proven" or not in_scope(p, project):
            continue
        (overrides if p.get("type") == "override" else additive).append(p)
    return additive, overrides


def bullet(p: dict) -> str:
    first_line = p["body"].splitlines()[0] if p["body"] else p["name"]
    return f"- {first_line} _({p['name']})_"


def replace_marked_section(path: Path, section_body: str, header: str) -> None:
    block = f"{BEGIN}\n{header}\n\n{section_body}\n{END}"
    if path.exists():
        text = path.read_text()
        if BEGIN in text and END in text:
            text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block, text, flags=re.S)
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
    else:
        text = block + "\n"
    path.write_text(text)


def write_markdown_targets(additive: list[dict]) -> list[Path]:
    body = "\n".join(bullet(p) for p in additive) if additive else "_(none proven yet)_"
    written = []
    for target in (Path("AGENTS.md"), Path("CLAUDE.md")):
        replace_marked_section(target, body, "## Learned patterns (patternity)")
        written.append(target)
    return written


def write_cursor_rule(additive: list[dict]) -> Path:
    globs = ",".join(sorted({p["applies_to"].get("glob", "**/*") for p in additive})) or "**/*"
    always = any(p["applies_to"].get("tool") in ("*", "cursor") for p in additive)
    body = "\n".join(bullet(p) for p in additive) if additive else "_(none proven yet)_"
    content = (
        "---\n"
        f"description: Patterns learned by patternity\n"
        f"alwaysApply: {'true' if always else 'false'}\n"
        f"globs: {globs}\n"
        "---\n\n"
        "## Learned patterns (patternity)\n\n"
        f"{body}\n"
    )
    path = Path(".cursor/rules/patternity-learned.mdc")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def write_copilot_instructions(additive: list[dict]) -> Path:
    globs = ",".join(sorted({p["applies_to"].get("glob", "**/*") for p in additive})) or "**/*"
    body = "\n".join(bullet(p) for p in additive) if additive else "_(none proven yet)_"
    content = (
        "---\n"
        f"applyTo: \"{globs}\"\n"
        "---\n\n"
        "## Learned patterns (patternity)\n\n"
        f"{body}\n"
    )
    path = Path(".github/instructions/patternity-learned.instructions.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def apply_overrides(overrides: list[dict]) -> tuple[list[str], list[str]]:
    search_paths = [
        Path("CLAUDE.md"), Path("AGENTS.md"), Path(".github/copilot-instructions.md"),
        *Path(".cursor/rules").glob("*.mdc"), *Path(".github/instructions").glob("*.instructions.md"),
    ]
    applied, unresolved = [], []
    for o in overrides:
        target = o.get("target")
        if not target or target == "null":
            unresolved.append(f"{o['name']}: no target text set")
            continue
        found = False
        for path in search_paths:
            if not path.exists():
                continue
            text = path.read_text()
            if target in text:
                path.write_text(text.replace(target + "\n", "").replace(target, ""))
                applied.append(f"{o['name']}: removed from {path}")
                found = True
                break
        if not found:
            unresolved.append(f"{o['name']}: target text not found verbatim — {target!r}")
    return applied, unresolved


def write_overrides_report(unresolved: list[str]) -> None:
    body = "\n".join(f"- {u}" for u in unresolved) if unresolved else "_(none pending)_"
    replace_marked_section(Path("AGENTS.md"), body, "## Overrides (needs manual check)")


def main() -> None:
    project = current_project()
    if not patterns_dir().exists():
        print(f"no pattern store at {patterns_dir()} — nothing to compile")
        return

    additive, overrides = load_proven(project)
    applied, unresolved = apply_overrides(overrides)
    written = write_markdown_targets(additive)
    written += [write_cursor_rule(additive), write_copilot_instructions(additive)]
    if unresolved:
        write_overrides_report(unresolved)

    print(f"[{project}] compiled {len(additive)} pattern(s), {len(applied)} override(s) applied, {len(unresolved)} unresolved")
    for w in written:
        print(f"  wrote {w}")


if __name__ == "__main__":
    main()
