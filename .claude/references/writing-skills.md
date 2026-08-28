# Writing and maintaining the shipped skills

shinyreact ships two Agent Skills **inside the R and Python packages**, so an
app author who only ran `pip install shinyreact` or
`install.packages("shinyreact")` gets them. That changes what a skill is here:
it is not a note to the next contributor, it is **released documentation with a
version number**, and a stale one ships to users.

| Skill | Task | Shipped? |
|---|---|---|
| `shinyreact-build-app` | build a `ui.tsx`-pattern app from scratch | yes |
| `shinyreact-convert-app` | port an existing Shiny app to the pattern | yes |
| `audit-shinyreact-features` | walk `FEATURES.md` against the code | no — audits this repo |

## Where they live, and the copy flow

`.claude/skills/<name>/` is canonical. `make update-skills` copies the shipped
ones into both packages:

| | Installed path | How a user installs it |
|---|---|---|
| `[py]` | `shinyreact/.agents/skills/<name>/SKILL.md` | `uvx library-skills --claude` |
| `[r]` | `system.file("skills", "<name>", package = "shinyreact")` | `btw::btw_skill_install_package("shinyreact")` |

Both paths are contracts with an installer, not internal layout — the Python one
is what `library-skills` scans site-packages for, the R one is where `btw`
looks. Neither is discoverable by reading our code, so do not "tidy" them.

**After editing a skill, run `make update-skills`.** `pkg-py/tests/test_skills.py`
and `pkg-r/tests/testthat/test-skills.R` fail on drift, so a forgotten copy is a
failing suite rather than a silently stale release.

Two traps in the copy flow:

- **`ruff format pkg-py` rewrites Python code blocks inside Markdown.** The
  generated Python copy is excluded in `pyproject.toml`; without that, ruff
  reformats the shipped copy away from its source and the drift test fails on a
  change nobody made.
- **Hatchling includes `.agents/` with no packaging config**, but `**` does not
  match hidden directories in every backend — py-shiny needed an explicit glob
  for setuptools. If the build backend ever changes, check the wheel
  (`unzip -l dist/*.whl | grep agents`) rather than assuming.

## Naming

`<package>-<task>`: `shinyreact-build-app`, `shinyreact-convert-app`.

- **Namespace by package.** Every installed package's skills land in one flat
  `.claude/skills/`, so the name must be unique across the whole ecosystem. A
  bare `shinyreact` was too generic and told the agent nothing about *when* to
  reach for it.
- **Then by task**, because that is what the agent matches on.
- **Not by language.** There is deliberately no `-py` / `-r` split: R and Python
  are one API here, the skills are ~90% shared prose, and two per-language
  copies would drift exactly the way the parity bugs in #182–#186 did. Both
  packages therefore ship byte-identical files, so installing both into one
  project is a no-op rather than a clash. The cost is that a Python-only reader
  skims some R code fences.
- If a language split ever happens, **the shared body moves to a `references/`
  file both skills point at.** Copy-paste is the failure mode, not the fix.

## Frontmatter

Exactly two keys, and both tests pin this:

```markdown
---
name: shinyreact-build-app
description: <one line — what it does, then "Use when …" with the trigger words>
---
```

- **`name` must equal the directory name.**
- **`description` must be a single line.** Installers parse it with strict YAML;
  a description spilling onto a second line makes the skill silently *invisible*
  rather than producing an error. This is why py-shiny had to quote theirs.
- **Avoid `: ` in the description** (or quote the whole value). It is what turns
  a scalar into a mapping and breaks the parse.
- The description is the only thing the agent sees before deciding to load the
  skill, so spend the line on **triggers** — the API names, the phrasings a user
  would actually type — not on a summary of the body.

## Keeping them current as features land

This is the part with no automated backstop, so it has to be a reflex. When a PR
adds or changes behavior, four artifacts can go stale, and they are not
interchangeable:

| Artifact | Answers | Update when |
|---|---|---|
| `FEATURES.md` | "what does it do, exactly?" | **always** — a behavior change with no tree diff is an incomplete PR |
| `pkg-*/README.md` | "what is the API?" | a public symbol is added, removed, or changes signature |
| `CLAUDE.md` | "how do we work in this repo?" | a convention, command, or invariant changes |
| the skills | "how should someone *build an app*?" | the recommended way to do something changes |

The skills are the narrowest of the four. Most `FEATURES.md` leaves do **not**
belong in a skill — internal branches, error-message wording, escape hatches. A
skill earns a change when it would otherwise teach something that is now wrong
or no longer the best way. Concretely:

- **a new hook, component, or `window.shinyreact` export** → the hook table and
  the surrounding "pick the narrowest hook" guidance. Pinned by
  `pkg-js/src/__tests__/skill-api-coverage.test.ts`, which fails until the name
  is either taught or listed as a deliberate omission.
- **a new page entry point, or a change to what one discovers** → Step 2. This
  is the highest-value section and the easiest to leave stale, because the
  entry points are exactly what a zero-config API keeps absorbing.
- **a new idiom we would tell someone to copy** (the action-button shape, the
  loading-vs-recalculating pattern) → "The patterns worth copying verbatim".
- **a new footgun** → "Things that bite". Every entry there should be a mistake
  someone actually made; the section is worthless as a list of things that
  *could* go wrong.
- **a new example** → the "Worked examples" line, and the translation table in
  `shinyreact-convert-app` if it demonstrates a new Shiny → shinyreact mapping.
- **anything R does differently** → say both sides in the same sentence. A skill
  that documents only the Python spelling is how a reader concludes R cannot do
  it.

**When you add a language marker, look for its sibling** — same reflex as
`FEATURES.md`. And when the skill and the code disagree, the code wins and the
skill gets fixed in that PR, not the next one.

## Writing style

Skills are read by an agent under context pressure, so they are closer to a
checklist than to documentation:

- **Say the decision, not the options.** "Start at no-build" beats a comparison
  of three tiers the reader has to adjudicate.
- **Lead with what breaks.** "Two React copies is the single most common failure
  mode, and it presents as *hooks return nothing* rather than as an error" is
  worth more than the correct config it precedes.
- **Copy-pasteable snippets, minimal and real.** Prefer a fragment taken from a
  working example over invented code.
- **No repo trivia.** File layouts, build commands, and test-suite mechanics
  belong in `CLAUDE.md`; a user who installed the package has none of that.
- **Point at the repo for depth** (`examples/`,
  `.claude/references/verifying-ui-code.md`) rather than inlining it. Those
  pointers are repo-relative on purpose: they are for developers, and a reader
  who has the repo is the one who needs them.
- **Terminology is not optional.** The `ui.tsx` pattern; never "SPA". A skill
  that uses the wrong word teaches every app built with it to use the wrong
  word.

## Checklist for a skill change

1. Edit `.claude/skills/<name>/SKILL.md` — the canonical copy.
2. Run `make update-skills`.
3. Does the other language do this too? Say both, or say why not.
4. Does `FEATURES.md` claim it? If the behavior is new, the tree changes first.
5. Run `make py-check-tests`, `make r-check-tests`, and the JS suite — all three
   assert something about the skills.
