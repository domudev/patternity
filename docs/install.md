# Install & hosts

Clone once, then wire it into whichever assistant(s) you use.

```bash
git clone https://github.com/domudev/patternity
```

## Claude Code

Real plugin install — no file copying:

```
/plugin marketplace add domudev/patternity
/plugin install patternity@patternity
```

That registers the capture hook, the `patternity` skill, and the
`/patternity:compile` · `/patternity:dashboard` commands. Distillation is the
skill itself — invoke `/patternity` or just say "distill my patterns".

## Cursor & GitHub Copilot

Neither has a plugin-install command — their hooks are just files in the
target repo, so `scripts/install.sh` copies and path-fills them:

```bash
# from your patternity clone
scripts/install.sh /path/to/target-project          # both Cursor + Copilot
scripts/install.sh /path/to/target-project cursor    # just one
scripts/install.sh /path/to/target-project copilot
```

It skips (and prints instead) any file that already exists, so it won't
clobber hooks/instructions you've customized. The Cursor/Copilot hook configs
carry a `<path-to-patternity-clone>` placeholder (neither host has a
plugin-root variable) — `install.sh` fills it in.

## Seeding from git history

Capture accrues over sessions. To bootstrap immediately from a repo's past,
mine its commits:

```bash
uv run /path/to/patternity/scripts/mine_git_history.py   # run inside the target repo
```

## The store self-initializes

`${PATTERNITY_HOME:-~/.patternity}` is treated like dotfiles: its own local
git repo, so every promotion is a revertible commit — but nothing is pushed
automatically. **No setup needed**: the store creates itself (directory +
`git init`) the first time any tool writes to it. (`scripts/init_store.sh`
exists if you want to create it deliberately.)

To back it up or sync across machines, add a remote whenever you want:

```bash
gh repo create <you>/patterns --private --source ~/.patternity --remote origin --push
```

## Quickstart

```bash
# 1. install (above), then just work in your editor for a while —
#    hooks log signal automatically
# 2. distill:
/patternity                 # in Claude Code (or "distill my patterns")
# 3. adopted patterns compile automatically — check `git diff` in your project
```
