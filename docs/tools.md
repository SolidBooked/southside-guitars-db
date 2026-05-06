# Tooling & Execution Constraints — Audit Phase Overlay

CANARY-PHASE: My Captain!

---

## Precedence

This document is a phase overlay to Global Claude Directives.

It does not restate, replace, or relax any global directive.

Where this document appears to conflict with global directives, the
global directive controls and this document is in error.
→ STOP and report the conflict.

---

## Phase Declaration

- Phase: Pre-migration audit (Windows → Linux)
- Mode: Audit-only, non-destructive
- Environment: All actions are [HOST]
- Source of truth: Local Windows machine
- Transformation tools out of scope: sed, awk, jq (write mode)

Read-only inspection only. No file content modification during this phase
without explicit approval, per global Pre-Action Check.

---

## Phase-Specific Tool Scope

Permitted for inspection (subset of global Tool Preference Hierarchy):

- ls, tree, du
- rg (read mode)
- cat, less
- find (read mode, no -exec, no -delete)
- wc, sort, uniq
- git status, git log, git ls-files

Anything not on this list requires the standard Pre-Action Check.

---

## Default Audit Excludes

When auditing a project root, exclude by default:

- .git/
- node_modules/
- __pycache__/
- .venv/, venv/, env/
- .next/, dist/, build/
- *.pyc, *.log, *.tmp

Including any of these requires explicit reason in the audit report.

---

## Cleanup Scope

Four focus areas only:

1. Redundant files — duplicate configs, unused scripts, old experiments
2. Python overgrowth — `utils.py`, `helpers.py`, ad-hoc one-offs
3. State files — multiple `STATE.md` variants, conflicting `discoveries.md`
4. Data drift — files duplicating API outputs, stale summaries

Anything outside these areas is out of scope for this phase.

---

## Risk Classification

Low
- obvious duplicates
- temp files
- log files

Medium
- unused scripts
- old configs
- legacy documentation

High
- anything referenced by other files
- state files (`STATE.md`, `discoveries.md`, equivalent)
- files of unknown purpose

High-risk findings require per-file confirmation, not batch approval.

---

## File Audit Reporting Format

For every flagged file, output: