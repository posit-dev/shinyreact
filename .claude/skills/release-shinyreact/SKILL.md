---
name: release-shinyreact
description: Cut a shinyreact release (PyPI, npm, or CRAN). Use when the user runs /release-shinyreact.
---

# Releasing shinyreact

Three packages, three independent versions, three tag prefixes. Releasing one
does **not** oblige releasing the others.

| Package | Version lives in | Tag | Automation |
|---|---|---|---|
| `shinyreact` (PyPI) | `pyproject.toml` (repo root) `version` | `py/v1.2.3` | `.github/workflows/release-py.yaml` |
| `@posit/shinyreact` (npm) | `pkg-js/package.json` `version` | `js/v1.2.3` | `.github/workflows/release-js.yaml` |
| `shinyreact` (R) | `pkg-r/DESCRIPTION` `Version` | `r/v1.2.3` | none — CRAN is a manual submission |

The `<lang>/v` prefix is what keeps the three apart; nothing else distinguishes
them. A bare `v1.2.3` tag triggers nothing.

## Before any release

The Python and R packages **vendor the built JS bundle** (`pkg-py/src/shinyreact/www/`,
`pkg-r/inst/lib/shiny/`). Releasing either one without rebuilding ships stale
JS, and nothing in the release workflow catches it — the committed copies are
checked by CI on PRs, not at tag time.

```bash
git switch main && git pull
make update-dist update-skills update-examples
git status --porcelain   # must be empty
```

A non-empty status here means main was merged with stale generated files: open
a normal PR with the regenerated output first, then release.

Then confirm main is green (`gh run list --branch main --limit 5`) and that the
checks for the package you're releasing actually ran — `check-r` and friends are
path-filtered and can be skipped rather than passing.

## Python → PyPI

1. Bump `version` in the **root** `pyproject.toml` (not `pkg-py/`; there is no
   pyproject there). Open a PR, merge it.
2. From the merged main: `git tag py/v1.2.3 && git push origin py/v1.2.3`.
3. `release-py.yaml` verifies the tag matches `uv version --short`, runs
   `uv build`, publishes with PyPI trusted publishing, and creates the GitHub
   release with generated notes and the sdist/wheel attached.

If the tag and `pyproject.toml` disagree the job fails before publishing —
delete the tag (`git push --delete origin py/v1.2.3`), fix, re-tag.

Trusted publishing must be configured once at
<https://pypi.org/manage/project/shinyreact/settings/publishing/> with workflow
`release-py.yaml` and environment `pypi`. There is no API token to rotate.

## JS → npm

1. Bump `version` in `pkg-js/package.json`. Open a PR, merge it.
2. `git tag js/v1.2.3 && git push origin js/v1.2.3`.
3. `release-js.yaml` verifies the tag matches `package.json`, lints, tests,
   builds (IIFE + npm ESM + types), and runs `npm publish --provenance`.
   Requires the `NPM_TOKEN` repository secret.

A JS release is usually paired with a Python and R release, since the packages
ship the same bundle — but they are separate versions and separate tags. Do the
`make update-dist` PR first so all three ship the same code.

## R → CRAN

No workflow. CRAN submission is interactive and cannot be automated by a tag.
The checklist is generated, not written by hand:

```r
# from pkg-r/ — usethis needs it as the active project
usethis::use_release_issue("1.2.3")
```

Then **work through the issue's bullets in order** and tick them off as you go.
usethis knows what a shinyreact release needs better than this file does — it
emits the right checklist for a first release vs. a patch, and it is the source
of truth for the CRAN steps (`urlchecker::url_check()`, `devtools::check(remote = TRUE, manual = TRUE)`,
revdep checks, `devtools::submit_cran()`, the post-acceptance version bump).

Two things the generated checklist does not know about:

- Run `make r-check` too (it fails on NOTEs), not just `devtools::check()`.
- Its "tag the release" bullet means `r/v1.2.3` here, not `v1.2.3`. Tag after
  CRAN accepts, then `gh release create r/v1.2.3 --generate-notes`.

If `use_release_issue()` is unavailable, `open-source:create-release-checklist`
produces the same tidyverse checklist.

## After any release

Nothing is automated post-release. Check the artifact actually landed
(`pip index versions shinyreact`, `npm view @posit/shinyreact version`) and
say so — a green workflow with a skipped publish step is the usual failure.
