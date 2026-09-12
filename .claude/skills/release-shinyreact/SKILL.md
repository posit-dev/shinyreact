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
| `@posit-dev/shinyreact` (npm) | `pkg-js/package.json` `version` | `js/v1.2.3` | `.github/workflows/release-js.yaml` — **stages only, a human approves** |
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

Unlike PyPI, **CI cannot publish npm** — it can only stage. The tag kicks off a
build that uploads a pending tarball; a human then approves it with 2FA. Two
steps, and the second one is not yours to do.

1. Bump `version` in `pkg-js/package.json` (`cd pkg-js && npm version 1.2.3
   --no-git-tag-version` also updates `package-lock.json`), and the matching
   constants `_SHINYREACT_JS_VERSION` in `pkg-py/src/shinyreact/_dep.py` and
   `.shinyreact_js_version` in `pkg-r/R/dep.R` (the shinyreact HTMLDependency
   version; `test_dep.py` / `test-dep.R` fail on drift). Open a PR, merge it.
2. `git tag js/v1.2.3 && git push origin js/v1.2.3`.
3. `release-js.yaml` verifies the tag matches `package.json`, lints, tests,
   builds (IIFE + npm ESM + types), and runs `npm stage publish`. Nothing is on
   npm yet. The job summary ends with the approval commands.
4. **Hand off to the human.** Report the run URL and stop — do not try to
   approve. Approval needs proof of presence (2FA), which an OIDC token cannot
   provide:

   ```bash
   npm stage list @posit-dev/shinyreact   # find the stage id
   npm stage view <stage-id>              # inspect what CI built
   npm stage download <stage-id>          # or pull the actual tarball
   npm stage approve <stage-id> --otp <code>   # publishes it
   npm stage reject <stage-id>                 # throws it away
   ```

   The Staged Packages tab on <https://www.npmjs.com/package/@posit-dev/shinyreact>
   does the same thing in a browser; 2FA is prompted either way. A stage is not
   on the registry and nobody can install it, so a bad build is rejected rather
   than unpublished — there is no 72-hour `npm unpublish` window to race.

There is **no `NPM_TOKEN`**, and adding one would be a regression — npm's own
guidance is "when trusted publishing is available for your workflow, always
prefer it over long-lived tokens", and direct publishing with a granular token
is being removed entirely in January 2027. Auth is npm trusted publishing
(OIDC): configured once on the package's Settings page against org
`posit-dev`, this repo, workflow filename `release-js.yaml`, and
`npm stage publish` as the *allowed action* — so the workflow cannot publish
directly even if someone edits it. Provenance is automatic under OIDC; the
workflow passes no `--provenance`.

Settings → Publishing access is also set to **"Require two-factor
authentication and disallow tokens"**. That closes the side door a token would
open without touching CI, since trusted publishing is OIDC rather than a
token. npm calls stage-only trusted publishing plus disallowed tokens the
maximum security posture; if you ever find yourself creating a token to work
around a release, that is the thing you are undoing.

Requires npm ≥ 11.15.0 and Node ≥ 22.14.0. `pkg-js/.nvmrc` pins Node 22, which
bundles npm 10.x, so the workflow upgrades npm explicitly — if a release fails
with an unknown `stage` command, that step is why.

A JS release is usually paired with a Python and R release, since the packages
ship the same bundle — but they are separate versions and separate tags. Do the
`make update-dist` PR first so all three ship the same code.

### The two things staging cannot do

- **A brand-new package cannot be staged**, and trusted publishing cannot be
  configured until the package exists. `0.1.0` was therefore published by hand
  from a maintainer's laptop — `npm login` and `npm publish --access public`,
  interactively with 2FA, **no token created**. It has no `js/v0.1.0` tag
  (pushing one would only have triggered a job that failed on a version already
  taken) and no provenance attestation, since that requires a CI publish. Every
  release from `0.1.1` on follows the flow above.
- **A new scope or a new package name** puts you back in that bootstrap case:
  publish once interactively, then configure the trusted publisher.

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
(`pip index versions shinyreact`, `npm view @posit-dev/shinyreact version`) and
say so — a green workflow with a skipped publish step is the usual failure.

For npm, a green workflow means *staged*, not published: `npm view` will keep
reporting the previous version until a human runs `npm stage approve`. Don't
report a JS release as done on the strength of a green run.
