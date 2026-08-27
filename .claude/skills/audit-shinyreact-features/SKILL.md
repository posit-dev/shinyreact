---
name: audit-shinyreact-features
description: Audit FEATURES.md against the shinyreact source — confirm, contradict, or flag every leaf, and find behavior in the code that the tree never claims. Use when the user says "audit features", "/audit-shinyreact-features", "is FEATURES.md still true", or after a change that may have drifted from the tree.
---

# Audit `FEATURES.md`

`FEATURES.md` claims what shinyreact does. This audit checks whether it is
still true, in **both** directions, and reports coverage as numbers rather than
as assurance. It **reports**; it does not edit `FEATURES.md` or the code unless
the user asks for fixes afterwards.

Read the "The feature tree" section of `CLAUDE.md` first — it defines the leaf
format, the language markers, and the completeness bar you are auditing
against.

## Scope

Default: the whole file. If the user names a section ("audit the page entry
points") or a language ("audit the R leaves"), audit only that and say so in
the report header.

## Step 1 — build the inventories first

Do this **before** reading a single leaf. Auditing from the tree alone can only
ever confirm the tree; the inventories are what let you find what the tree
omits, and they keep the leaf pass honest about what it skipped.

For each package in scope, collect and **count**:

| Inventory | How |
|---|---|
| public symbols + signatures + defaults | `pkg-py/src/shinyreact/__init__.py`'s `__all__`, `pkg-r/NAMESPACE`, `pkg-js/src/global.ts` + `npm.ts` exports |
| error and warning sites | `grep -n "raise \|warnings.warn\|cli_abort\|stop(\|warning(\|throw new" <src>` |
| caller-steerable branches | `grep -n "if \|else\|elif \|try:\|except \|switch" <src>` — filter to branches a caller's input can select |
| fallback values | the `X if Y else Z` and `??` / `||` defaults, especially path and version fallbacks |
| unit test names | `grep -h "^def test\|^test_that\|  it(" <tests>` |
| e2e test names | `pkg-py/tests/playwright/test_*.py` |

Keep each inventory as a list. Every item must end the audit either matched to
a leaf or reported as unclaimed. That accounting is the deliverable — an audit
that cannot say how many of the 41 branch sites are described by leaves has not
finished.

## Step 2 — tree → code

Walk **every leaf** in scope, in file order. Skipping leaves because they look
obvious is how a stale tree survives an audit. Decide each from the source —
not from docstrings, not from `CLAUDE.md`, not from memory. Docstrings and
`CLAUDE.md` are themselves unverified claims, and have been wrong before.

| Verdict | Means |
|---|---|
| `CONFIRMED <file:line>` | the code does this; cite the line that proves it |
| `CONTRADICTED <file:line>` | the code does something else; say what it actually does |
| `NOT FOUND IN CODE` | no code implements this claim |
| `UNVERIFIABLE` | not atomically checkable as written; say what would make it checkable |

Rules for this pass:

- Markers narrow where to look: `[py]` → `pkg-py/src/shinyreact/`, `[r]` →
  `pkg-r/R/`, `[js]` → `pkg-js/src/`.
- An **unmarked** leaf claims every language its subtree applies to. Check each
  one and give a per-language verdict when they disagree — a leaf that is true
  in Python and false in R is `CONTRADICTED`, not `CONFIRMED`.
- `(verify)` leaves are normal targets, not exemptions. Resolving one to
  CONFIRMED means its marker can be dropped; say so.
- `(e2e)` leaves must be traced to an actual assertion in the named test, not
  just to a test whose name sounds right.
- Tests are supporting evidence, never the primary source. Note which leaves a
  test pins (`CONFIRMED ..., pinned by <test>`) and which no test pins — the
  latter are the ones that will drift silently.

## Step 3 — code → tree

Now walk the inventories from step 1 and list what has **no leaf**. This half
is where the findings usually are:

- public symbols, parameters, and defaults with no leaf
- error paths, warnings, and validation with no leaf
- caller-steerable branches with no leaf (existence checks, `None` fallbacks,
  absolute vs. relative, marker present/absent)
- silent fallback values with no leaf
- tests whose asserted behavior no leaf describes
- parity gaps: a behavior in one language whose sibling leaf is missing

Classify each as **undocumented behavior** (the tree needs a leaf) or **scope
creep** (the code does more than intended). If it is genuinely unclear, say so
and let the user decide — do not guess.

## Step 4 — report

Markdown, no `ReportFindings` tool. Lead with the numbers, then what needs
action, then compact confirmations.

```
# FEATURES.md audit — <scope>

Leaves: CONFIRMED 61 · CONTRADICTED 2 · NOT FOUND 1 · UNVERIFIABLE 3
Coverage: symbols 14/14 · errors 4/4 · branches 33/41 · fallbacks 5/7 · tests 88/94 · e2e 9/9
Unclaimed behavior: 7

## Needs action
- CONTRADICTED — "version falls back to `0.1.0`" → `_dep.py:24` falls back to `"0"`
- ...

## Unclaimed behavior
- undocumented — `page_react_dep(name=)` has no leaf — `_page.py:127`
- scope creep? — ...

## Leaves no test pins
- "the stylesheet is attached unconditionally" — no assertion anywhere

## Confirmed
### Wire protocol
- protocol version is `1.0` — `_protocol.py:17`, pinned by `test_protocol_version_matches_js_and_r`
- ...
```

End with one line of judgment: is the tree trustworthy right now, and which
section is least trustworthy.

## Rules

- **The code wins.** A disagreement is a tree bug until the user says the code
  is wrong.
- **Cite `file:line` for every CONFIRMED and CONTRADICTED.** An audit without
  citations is an opinion. Line numbers live in the *report*, never in
  `FEATURES.md` — there they rot.
- **Report absence.** A leaf you could not check, an inventory you could not
  complete, a package you ran out of budget on — all findings, none of them
  things to quietly drop. Never round a partial audit up to a clean one.
- **Do not fix while auditing.** Findings first; the user decides what changes.
- Fan out with subagents for a whole-file audit — one per section or per
  language — but give each the inventory it must account for, require verdicts
  with citations, and merge the results yourself. A subagent's summary is not a
  substitute for leaf-level verdicts, and "looks good" from a subagent is a
  failed audit, not a pass.
