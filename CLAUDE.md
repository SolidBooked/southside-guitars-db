# Southside Guitars DB — Database & Extract Pipeline

## Before Starting Work

CANARY-GLOBAL: Oh Captain!

## File Placement Rules

STRICT — These are hard constraints, not suggestions:

- **Source modules** → `src/southside_guitars_db/` (reusable code)
- **One-off scripts** → `scripts/` (never at root)
- **Data files (CSV, Excel, JSON)** → `data/` (never at root)
- **Generated outputs** → `data/outputs/` (never at root)
- **Tests** → `tests/`
- **Documentation** → `docs/`
- **Soft-deleted files** → `archive/` (never delete, always archive)

**NEVER create files at project root** except: `CLAUDE.md`, `STATE.md`, `.gitignore`, `.env`, `pyproject.toml`, `requirements.txt`, `README.md`

**NEVER create new directories at root** — nest under logical parents (`data/`, `docs/`, `src/`, etc.)

## Data Registry Protocol

ALL data files must be registered in `data/registry.json` before use.

**Before using any data file:**
1. Check `data/registry.json` for the file's entry
2. Verify `status: "active"` — never use files with `status: "archived"` or `status: "deprecated"`
3. Check `last_verified` date — if older than 30 days, verify with user before use

**When adding new data:**
1. Place file in `data/` (or appropriate subdirectory)
2. Add entry to `data/registry.json` with `status: "active"`
3. Update `last_updated` timestamp in registry

## Archive Policy

- **Soft delete only** — move files to `archive/`, never `git rm`
- Files in `archive/` are NOT referenced by agents unless explicitly asked
- `archive/README.md` documents what's archived and why
- Periodically review `archive/` — delete files older than 12 months

## Project Overview

- **Package name:** `southside_guitars_db` (installable via `pip install -e .`)
- **Import pattern:** `from southside_guitars_db.config import ...`
- **Package structure:** `src/southside_guitars_db/` for reusable modules, `scripts/` for one-off tasks

## Key Directories

- `src/southside_guitars_db/` — Reusable source modules (config, db, schema)
- `scripts/` — One-off scripts (q2_extract.py)
- `data/` — Data files and outputs
- `tests/` — Test suite
- `docs/` — Documentation (discoveries, technical spec, tools)
- `archive/` — Soft-deleted files (not used by agents)

## Cross-Session Communication

When working in parallel sessions:
1. Check `docs/discoveries.md` at session start
2. Add new findings to `docs/discoveries.md` during/after your session
3. Log detailed session work in `docs/sessions/YYYY-MM-DD-topic.md`

## Session End — Required Steps

At the end of every session, before closing:
1. Update `STATE.md` with findings, created items, and pending actions
2. Update `data/registry.json` if data was added, moved, or changed status
3. Commit all changed files: `STATE.md`, `docs/discoveries.md`, session log
4. **Push to GitHub: `git push`**

Commit message format:
```
Session YYYY-MM-DD: <topic> — <summary>

Co-Authored-By: Claude <model> <noreply@anthropic.com>
```
