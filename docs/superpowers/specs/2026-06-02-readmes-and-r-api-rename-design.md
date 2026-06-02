# Design: Language-agnostic root README, per-language package READMEs, and R API rename

**Date:** 2026-06-02
**Status:** Approved (design)

## Problem

Three issues with the repo's README surface:

1. The root `README.md` reads as the **Python** README — Python-only code samples,
   "from Python", `pip install`. It should be the language-agnostic front door for
   the monorepo (Python *and* R).
2. `pkg-py/README.md` is **missing** — there is no PyPI landing page for the Python
   package.
3. `pkg-r/README.md` is a 14-line stub that only points at `../docs` and
   `../examples`. It should be a polished pkgdown/CRAN landing page.

Separately, while writing the R docs we are renaming two R exports for clarity and to
avoid collision with base Shiny's `uiOutput()` / `renderUI()`. This is done as one
coherent change so the docs and code never disagree.

## Scope decisions (settled)

- **Split (option C):** root = language-agnostic monorepo front door; `pkg-py` = Python
  published landing page; `pkg-r` = R published landing page.
- **Honest pre-release (option A):** no fabricated CRAN/PyPI presence. Install via dev
  sources. Only badges that are real today.
- **Rename is in scope** as one coherent change (code + docs together).
- Python API is **unchanged** (`ui_output` / `reactive_output` stay). The R/Python
  divergence is justified by R's `uiOutput`/`renderUI` namespace collision.

## Part 1 — R API rename

R-only renames:

| Old (R) | New (R) |
|---|---|
| `ui_output()` | `ui_output_react()` |
| `render_reactive()` | `render_react()` |

Rationale: base Shiny already ships `shiny::uiOutput()` and `shiny::renderUI()`. A bare
`ui_output()` reads as a near-synonym of `uiOutput()`, and `render_reactive()` doesn't
signal what it renders. The `_react` suffix on both makes the pairing obvious and
collision-free.

**Ripple (R-only — Python `ui_output` is left alone):**

- **Source:** `pkg-r/R/output.R` (def + roxygen, cross-ref → `[render_react()]`),
  `pkg-r/R/render.R` (def, `label = "render_react"`, the `{.code ui_output_react(...)}`
  cli hint, cross-ref → `[ui_output_react()]`).
- **Regenerated via roxygen (not hand-edited):** `NAMESPACE` and `man/*.Rd`. The stale
  `man/ui_output.Rd` and `man/render_reactive.Rd` are removed; `man/ui_output_react.Rd`
  and `man/render_react.Rd` are created.
- **`_pkgdown.yml`:** update `reference:` `contents:` entries.
- **Tests:** `pkg-r/tests/testthat/test-ui-output.R`, `test-render.R` (update calls;
  keep filenames).
- **R examples:** `examples/app-r/{01-hello-world,02-inputs,04-messages}/app.R`,
  `examples/ui-tsx-r/01-hello/app.R`, and the R example READMEs that name the functions
  (`examples/app-r/02-inputs/README.md`, `examples/ui-tsx-r/01-hello/README.md`).
- **Living docs (updated for accuracy):** `docs/features.md` (R-pattern section) and
  `docs/timeline.md:83` (the `shinyreact::ui_output()` R reference). The other
  `ui_output` mentions in `docs/todos.md`, `CLAUDE.md`, `docs/app-py-vs-ui-tsx.md`, and
  `docs/timeline.md:110` are **Python** `ui_output` and stay unchanged.
- **Not touched:** `docs/superpowers/specs/*` and `docs/superpowers/plans/*` — historical
  records, left as written.
- **Verify:** `make r-check` (format + tests + R CMD check) passes.

## Part 2 — Root `README.md` (language-agnostic)

Strip Python-specific code; frame for "Python *or* R."

- **Title + tagline** — broaden "from Python" → "from Python or R."
- **How it works** — the two patterns (`app.py`/`app.R` and `ui.tsx`), no Python code.
- **Two languages** — short side-by-side: install + hello-world entry points, links to
  `pkg-py/README.md`, `pkg-r/README.md`, and the two pkgdown sites.
- **Architecture** — JS bundle / Python package / R package (kept; already cross-language).
- **JS bridge hooks table** — stays here (shared, language-neutral JS infra).
- **Extending shinyreact (package authors)** — keep the JS half; show the Python *and* R
  render-subclass/counterpart briefly.
- **Repo layout + Development** — `make` targets (already language-spanning).
- **Removed:** the Python `Usage` code blocks (moved to `pkg-py/README.md`).

## Part 3 — `pkg-py/README.md` (new; PyPI landing page)

Today's root content, Python-focused:

- Tagline, How it works.
- **Install (pre-release):** dev source, e.g.
  `pip install "shinyreact @ git+https://github.com/posit-dev/shinyreact.git#subdirectory=pkg-py"`
  (honest — not yet on PyPI). Confirm exact installable path during implementation.
- Usage for both patterns (the code currently in root).
- `send_message`.
- "Extending shinyreact" Python subclass section.
- JS hooks table.
- One-line note that the wheel also ships the `shinyui` / `shinyuiclassonly` prototypes
  (pointer only).

## Part 4 — `pkg-r/README.md` (bslib-inspired; pkgdown/CRAN landing page)

bslib's *shape and voice*, adapted to a zero-component plumbing package (no logo/GIF —
none exist):

- **Title + one-line tagline.**
- **Badges (honest):** lifecycle-experimental + R-CMD-check (from `check-r.yaml`). No CRAN
  badge yet.
- **Overview** — conversational; what it is / what it's for.
- **Installation** — pre-release via `pak::pak("posit-dev/shinyreact")` (GitHub). Confirm
  whether a subdir spec is needed for the monorepo layout during implementation.
- **A worked example** — condensed `app.R` hello-world using `ui_output_react()` /
  `render_react()`.
- **The two patterns** — brief, R framing (`app.R` vs `ui.tsx`).
- **Get started** — links to the pkgdown reference site
  (`https://posit-dev.github.io/shinyreact/r`), `examples/app-r/`, and `docs/features.md`.
- **No Code of Conduct section** (see Part 5).

## Part 5 — Code of Conduct (separate from README)

Run `usethis::use_tidy_coc()` with the active project set to the **repo root** to add
**`.github/CODE_OF_CONDUCT.md`** (Contributor Covenant 2.1, contact
`codeofconduct@posit.co` — the standard monitored tidyverse/Posit alias). Command:

```sh
Rscript -e 'usethis::with_project(".", usethis::use_tidy_coc())'
```

At the repo root there is no `DESCRIPTION`, so `is_package()` is `FALSE` and usethis
makes no `.Rbuildignore` edit (none is needed — the file lives outside `pkg-r/`). usethis
also creates `.github/.gitignore` (`*.html`) as a minor side artifact. Do not embed a CoC
section in the README.

## Out of scope

- Renaming Python API.
- Rewriting historical specs/plans under `docs/superpowers/`.
- Adding a logo or demo GIF.
- Publishing to PyPI/CRAN.

## Verification

- `make r-check` passes (format, tests, R CMD check) after the rename + CoC file.
- `make py-check` still passes (Python untouched, but confirm no incidental breakage).
- All three READMEs render correctly and contain no broken internal links or
  non-functional install/badge URLs.
- Repo-wide grep confirms no remaining R-context references to `render_reactive` or the
  bare R `ui_output` (Python `ui_output` retained).
