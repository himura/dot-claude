---
name: pre-pr-check
description: Verify a branch is ready to become a pull request. Runs project-specific quality checks (lint/test/typecheck/build) sourced from CLAUDE.md or auto-detected tooling, scans the diff for hygiene issues (merge markers, debug statements, secrets, oversized files, accidental .env), and reports branch state (rebase needs, uncommitted changes, weak commit messages). Reports findings only — never auto-fixes, formats, commits, or pushes. Use when the user signals readiness to ship a branch with phrases like "PR 出す前に確認", "push する前にチェック", "ready to open a PR", "pre-PR check", "final check before review".
---

# pre-pr-check

Run a structured pre-PR verification pass on the current branch and emit a
single consolidated report. **Reporting only** — no formatting, no auto-fix,
no commits, no pushes.

## Determine the base branch

Try in order, use the first that resolves:

1. `git symbolic-ref refs/remotes/origin/HEAD` (strip the `refs/remotes/origin/` prefix)
2. `origin/main`, `origin/master`, `origin/develop` — whichever exists
3. `main`, `master`, `develop` — whichever exists locally
4. If none resolve, abort with an error: the report cannot be produced
   without a base.

Use `git merge-base <base> HEAD` for the actual comparison point.

## Phase 1 — Project-specific checks

Source priority:

### 1a. CLAUDE.md (preferred)

In the repo root `CLAUDE.md`, look for a section heading matching
`## Pre-PR Checks` (case-insensitive, allow trailing words). If present:

- Each bullet item (`- <cmd>`) under that section is a shell command.
- Lines inside a fenced ` ```bash ` / ` ```sh ` block under that section
  are also commands (one per line, blank and `#`-comment lines skipped).
- Run them in document order from the repo root.
- **Stop here** — do not also run auto-detected commands.

### 1b. Auto-detect

If CLAUDE.md has no `## Pre-PR Checks` section, detect from repo files:

| Marker file | Commands (in order) |
|---|---|
| `package.json` with `scripts.lint` | `<pm> run lint` |
| `package.json` with `scripts.typecheck` (or `type-check`) | `<pm> run typecheck` |
| `package.json` with `scripts.test` | `<pm> test` |
| `package.json` with `scripts.build` | `<pm> run build` |
| `Cargo.toml` | `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test` |
| `stack.yaml` | `stack test --fast` |
| `*.cabal` (no stack.yaml) | `cabal test all` |
| `go.mod` | `go vet ./...`, `go test ./...` |
| `pyproject.toml` or `poetry.lock` or `requirements.txt` | `ruff check .`, `mypy .`, `pytest` (skip any not installed) |
| `Gemfile` | `bundle exec rspec` (if `spec/`), `bundle exec rubocop` (if installed) |
| `Makefile` with target `check` | `make check` |

`<pm>` for Node: `pnpm` if `pnpm-lock.yaml`, else `yarn` if `yarn.lock`,
else `bun` if `bun.lockb`, else `npm`.

Run each command sequentially, capture exit code and the last ~30 lines of
combined output. **Do not stop on failure** — continue to the next command.

### 1c. Nothing matched

Report `Phase 1: no project checks configured` as a warning. Do not mark the
phase as passing silently.

## Phase 2 — Diff hygiene

Get the diff: `git diff --no-color $(git merge-base <base> HEAD)...HEAD`.
Also get changed file list: `git diff --name-only $(git merge-base <base> HEAD)...HEAD`.

Scan for:

**Merge conflict markers** (error)
- Lines containing `<<<<<<< `, `=======` on its own line within a diff, `>>>>>>> `

**Debug statements** in *added* lines, skipping test files
(`*_test.*`, `*.test.*`, `*.spec.*`, paths under `test/`/`tests/`/`__tests__/`/`spec/`)
- JS/TS: `console.log(`, `console.debug(`, `debugger;`
- Rust: `dbg!(`, `eprintln!(`
- Python: `breakpoint()`, `pdb.set_trace()`, `import pdb`
- Ruby: `binding.pry`, `binding.irb`
- Haskell: `Debug.Trace`, `traceShow`, `trace `
- Go: `fmt.Println(` outside `main` package and non-test files

**Oversized files** (warning at >1 MiB, error at >10 MiB)
- Check with `git diff --stat` or `wc -c` on added/modified blobs

**Binary additions** (warning)
- `git diff --numstat` rows where added/removed are both `-`

**Suspicious filenames added** (error)
- `*.env` (except `.env.example`, `.env.sample`, `.env.template`)
- `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*.pfx`
- Paths matching `*credentials*`, `*secret*` (case-insensitive)

**Secret patterns in additions** (error)
- `-----BEGIN [A-Z ]*PRIVATE KEY-----`
- `AKIA[0-9A-Z]{16}` (AWS access key)
- `ghp_[A-Za-z0-9]{36}`, `gho_[A-Za-z0-9]{36}` (GitHub tokens)
- `xox[baprs]-[A-Za-z0-9-]+` (Slack)
- `AIza[0-9A-Za-z_-]{35}` (Google API key)
- `sk-[A-Za-z0-9]{32,}` (generic API key shape — warn, not error)

Report each match with file path and line number from the diff context.

## Phase 3 — Branch state

- `git status --porcelain` — any output ⇒ uncommitted changes (warning)
- `git rev-list --count HEAD..<base>` — > 0 ⇒ behind base, rebase recommended (warning)
- `git rev-list --count <base>..HEAD` — 0 ⇒ no commits to PR (error)
- Commit messages from `git log <base>..HEAD --format=%s`:
  - Empty subject ⇒ error
  - Matches `(?i)^(wip|fixup|squash|tmp|asdf|test commit)\b` ⇒ warning
  - Subject longer than 72 chars ⇒ warning
- If upstream is set, `git rev-list --count @{u}..HEAD` — report unpushed
  count as info (not a warning).

## Output

Single consolidated report. Group by phase. Each item prefixed with
`[✓]` / `[⚠]` / `[✗]`. End with a one-line summary:

```
Summary: N error(s), M warning(s). <verdict>
```

Verdict text:
- 0 errors, 0 warnings → `Ready to open the PR.`
- 0 errors, ≥1 warning → `Review warnings, then ready.`
- ≥1 error → `Address errors before opening the PR.`

If Phase 1 sourced from CLAUDE.md, note `(source: CLAUDE.md)` next to the phase
heading; if auto-detected, note `(source: auto-detected: <tooling>)`; if none,
`(source: none)`.

## CLAUDE.md convention

Projects opt out of auto-detection by adding a section to their `CLAUDE.md`:

````markdown
## Pre-PR Checks

- stack test --fast
- hlint src/
````

Or via a fenced block:

````markdown
## Pre-PR Checks

```sh
pnpm lint
pnpm typecheck
pnpm test
```
````

Commands are run from the repo root in order. Listed commands fully replace
auto-detection — list every check the project needs.
