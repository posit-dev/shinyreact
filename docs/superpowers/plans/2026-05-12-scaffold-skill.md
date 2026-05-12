# Scaffold-Helper Claude Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill at `.claude/skills/scaffold-shinyreact-helper/` that, when invoked, scaffolds a new shinyreact downstream helper-package prototype mirroring `downstream-prototypes/shinymui/`'s layout — taking an upstream React library reference, a short name, and a target directory as inputs and producing a directory that builds and serves end-to-end.

**Architecture:** A single `SKILL.md` file (with YAML frontmatter) instructs Claude through the scaffolding procedure. Rather than duplicating shinymui's file contents inline, SKILL.md tells Claude to copy each file from `downstream-prototypes/shinymui/` and apply a substitution table. The skill produces a working scaffold with **one** stub component (Button-shaped) — the package author adds further components manually. Validated by an end-to-end smoke test that invokes the skill against a real upstream library and verifies the resulting scaffold builds, lints, tests, and serves HTTP 200.

**Tech Stack:** Claude Code skills system (Skill tool + `.claude/skills/<name>/SKILL.md`), Markdown with YAML frontmatter.

**Non-goals (this plan):**
- Auto-discovering all components in the upstream library — the skill scaffolds **one** stub component
- Theming / styling integration
- PyPI/npm publishing setup, CI workflows
- Per-category divergence handling — targets the MUI/category-1 baseline only
- Self-validating the skill via subagent pressure tests (per superpowers:writing-skills — that's appropriate but out of scope for the prototype skill; the end-to-end smoke test in Task 6 is sufficient validation for now)

---

## File structure

```
.claude/
  skills/
    scaffold-shinyreact-helper/
      SKILL.md                         # YAML frontmatter + full procedure
```

That's it — one file. The skill references `downstream-prototypes/shinymui/` for templates, so no separate templates directory.

The end-to-end smoke test (Task 6) produces a temporary `downstream-prototypes/_skill-test-<name>/` directory that is verified, then deleted. It is **not** committed.

---

## Task 1: Scaffold skill directory and SKILL.md skeleton

**Files:**
- Create: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p .claude/skills/scaffold-shinyreact-helper
```

- [ ] **Step 2: Write the skeleton `SKILL.md` (frontmatter + overview only)**

```markdown
---
name: scaffold-shinyreact-helper
description: Scaffold a new shinyreact downstream helper-package prototype that mirrors the shinymui reference layout. Use when starting a new helper package for a React UI library (e.g., shinymantine, shinyradix, shinyaggrid). Asks for the upstream package, short name, and target directory; produces a working scaffold with one stub component that builds and loads end-to-end.
---

# Scaffold a shinyreact helper package

## Overview

This skill produces a new helper-package prototype at a target directory, mirroring the layout established by `downstream-prototypes/shinymui/`. The output is **one stub component** wired end-to-end — the package author adds further components by following the established pattern (factory in Python + registered React component + entry-app wiring).

**Conventions enforced** (from [the helper-packages RFC](../../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md) §4):

- IIFE Vite bundle with React externalized to `window.shinyreact.React`
- Catalog keys namespaced as `<prefix>:<Component>`
- Python factory functions returning `shinyreact.Node(type="<prefix>:<Component>", props=...)`
- `HTMLDependency` produced by a `dep()` helper, consumed via `shinyreact.ui_output(id, extra_deps=[dep()])`
- Per-package directory layout: `js/` + `pkg-py/` + `example/`

**Reference implementation:** `downstream-prototypes/shinymui/` is the working precedent. If anything in this skill is ambiguous, read the corresponding shinymui file directly.

## Non-goals

This skill targets the category-1 styled-component-library baseline. It does not auto-discover all components in the upstream library, configure theming, set up CI/publishing, or handle per-category divergences (headless, copy-paste, specialized). Those are added by the package author after scaffolding.

The rest of the procedure (inputs, substitution rules, scaffolding steps, verification) lands in subsequent tasks.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): scaffold-shinyreact-helper SKILL.md skeleton"
```

---

## Task 2: Add the "Inputs" and "Substitution rules" sections

**Files:**
- Modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Append the Inputs section**

Append to `SKILL.md` (immediately after the "## Non-goals" section):

```markdown
## Inputs

Before scaffolding, collect these from the user one at a time. Validate each before moving on.

1. **Short package name** (e.g., `mantine`, `radix`, `aggrid`). Lowercase, no separators, no `shiny` prefix — the skill prepends `shiny` to form the package name (e.g., `mantine` → `shinymantine`).
2. **Upstream npm package(s)** that the helper will wrap (e.g., `@mantine/core`, `@radix-ui/react-dialog`, `ag-grid-react`). Accept either a single package or a comma-separated list. Used as a `dependencies` entry in the scaffold's `js/package.json`.
3. **Catalog prefix** (defaults to the short package name). The string before `:` in catalog keys (e.g., `mantine` → `mantine:Button`).
4. **Stub component name** (defaults to `Button`). The single component the skill wires up end-to-end as proof the scaffold loads. The package author replaces or extends after scaffolding.
5. **Target directory** (defaults to `downstream-prototypes/shiny<name>/`). Where the scaffold lives.

After collecting all inputs, **echo them back to the user** and ask for confirmation before writing any files. Example:

> About to scaffold:
> - Package: `shinymantine` (at `downstream-prototypes/shinymantine/`)
> - Upstream: `@mantine/core`
> - Prefix: `mantine:`
> - Stub component: `Button`
>
> Proceed? (yes / change)

If they say "change", re-collect the affected input.

## Substitution rules

Throughout the procedure, the following placeholders are substituted with values derived from the inputs:

| Placeholder | Derived from | Example value (for `mantine`) |
|-------------|--------------|-------------------------------|
| `{name}` | short package name | `mantine` |
| `{pkg}` | `shiny{name}` | `shinymantine` |
| `{Name}` | short package name, capitalized | `Mantine` |
| `{prefix}` | catalog prefix | `mantine` |
| `{Stub}` | stub component name, PascalCase | `Button` |
| `{stub}` | stub component name, snake_case lowercase | `button` |
| `{target_dir}` | target directory | `downstream-prototypes/shinymantine` |
| `{upstream_pkg}` | upstream npm package | `@mantine/core` |

These placeholders appear in templated files copied from `downstream-prototypes/shinymui/` and in the inline content below. The skill performs these substitutions textually when copying.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): add inputs + substitution rules to scaffold-shinyreact-helper"
```

---

## Task 3: Add the "Procedure: directory + JS project" section

**Files:**
- Modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Append the procedure header and Steps 1-2**

Append to `SKILL.md`:

````markdown
## Procedure

Run these steps in order. After each step, briefly confirm to the user what landed. Do not commit until Step 7.

### Step 1: Create the directory layout

```bash
mkdir -p {target_dir}/js/src/components
mkdir -p {target_dir}/pkg-py/src/{pkg}/www
mkdir -p {target_dir}/pkg-py/tests
mkdir -p {target_dir}/example
```

Create `{target_dir}/README.md` with the following content (substituting placeholders):

```markdown
# {pkg} (prototype)

**Status:** scaffold from `scaffold-shinyreact-helper`. Validates conventions in the [helper-packages RFC](../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md).

Exposes `{upstream_pkg}` components to `shinyreact`. Currently scaffolded with one stub component (`{Stub}`); add more by following the pattern in `downstream-prototypes/shinymui/`.

## Run the example

\`\`\`bash
cd {target_dir}
(cd js && npm install && npm run build)
cp js/dist/{pkg}.js pkg-py/src/{pkg}/www/{pkg}.js
uv pip install -e pkg-py
uv run shiny run --reload example/app.py
\`\`\`
```

(Note: the inner triple-backtick block is what the README needs — preserve it literally when writing the file.)

### Step 2: JS project

Copy each of these files from `downstream-prototypes/shinymui/js/` to `{target_dir}/js/` and apply substitutions. **Run substitutions as plain text replacement** (`shinymui` → `{pkg}`, `mui:` → `{prefix}:`, `@mui/material` → `{upstream_pkg}`, etc.).

| Source file | Destination | Substitutions |
|---|---|---|
| `downstream-prototypes/shinymui/js/package.json` | `{target_dir}/js/package.json` | `@shinymui/js` → `@{pkg}/js`; remove the `@mui/material`, `@mui/x-data-grid`, `@mui/icons-material`, `@emotion/react`, `@emotion/styled` entries from `dependencies`; add the user-supplied `{upstream_pkg}` (or each entry in the comma-separated list) at `^latest` or the version the user specified. Keep peerDependencies on react/react-dom and devDependencies unchanged. |
| `downstream-prototypes/shinymui/js/tsconfig.json` | `{target_dir}/js/tsconfig.json` | None — file is generic. |
| `downstream-prototypes/shinymui/js/vite.config.ts` | `{target_dir}/js/vite.config.ts` | `shinymui` → `{pkg}` (appears in `lib.name`, `fileName`, and `assetFileNames`). |
| `downstream-prototypes/shinymui/js/.gitignore` | `{target_dir}/js/.gitignore` | None. |
| `downstream-prototypes/shinymui/js/src/types.ts` | `{target_dir}/js/src/types.ts` | None — types are generic. |

After copying, run `npm install` in `{target_dir}/js/`:

```bash
cd {target_dir}/js && npm install
```

Wait for completion (1-3 minutes for a typical UI library).

### Step 3: JS entry + stub component

Create `{target_dir}/js/src/components/{Stub}.tsx` with this content:

```tsx
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

export function {Stub}({ element }: RegisteredComponentProps) {
  const { label, input_id } = element.props as {
    label: string;
    input_id: string;
  };

  const [count, setCount] = useShinyInput<number>(input_id, 0, {
    debounceMs: 0,
    priority: "event",
  });

  return (
    <button onClick={() => setCount((count ?? 0) + 1)}>
      {label} (clicks: {count ?? 0})
    </button>
  );
}
```

This is intentionally a **plain HTML `<button>`**, not a styled component from the upstream library. The package author swaps in the real upstream component as the first edit after scaffolding. The stub exists to verify the scaffold loads end-to-end with the simplest possible component code.

Create `{target_dir}/js/src/index.ts`:

```ts
import type { ComponentRegistry } from "./types";
import { {Stub} } from "./components/{Stub}";

const registry: ComponentRegistry = {
  "{prefix}:{Stub}": {Stub},
};

const catalog = { name: "{pkg}", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
```
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): add procedure §1-3 (directory + JS project + stub) to scaffold-shinyreact-helper"
```

---

## Task 4: Add the "Procedure: Python package" section

**Files:**
- Modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Append Steps 4-5**

Append to `SKILL.md`:

````markdown
### Step 4: Python package

Copy each of these files from `downstream-prototypes/shinymui/pkg-py/` to `{target_dir}/pkg-py/` and apply substitutions.

| Source file | Destination | Substitutions |
|---|---|---|
| `downstream-prototypes/shinymui/pkg-py/pyproject.toml` | `{target_dir}/pkg-py/pyproject.toml` | `shinymui` → `{pkg}` (appears in `name`, `packages`, and the `force-include` mapping). Keep `version = "0.0.0.dev0"` (hatchling requires PEP 440 — `0.0.0-prototype` is not valid). |
| `downstream-prototypes/shinymui/pkg-py/src/shinymui/_dep.py` | `{target_dir}/pkg-py/src/{pkg}/_dep.py` | `shinymui` → `{pkg}` (appears in the filename in `bundle`, the HTMLDependency `name`, and the `script.src`). |

Create `{target_dir}/pkg-py/src/{pkg}/__init__.py`:

```python
from ._components import {stub}
from ._dep import dep

__all__ = ["dep", "{stub}"]
```

Create `{target_dir}/pkg-py/src/{pkg}/_components.py`:

```python
"""Python factory functions for {Name} components.

Each factory returns a ``shinyreact.Node`` with a ``{prefix}:``-namespaced type
string. Currently scaffolded with one stub factory; add more by following the
pattern.
"""

import shinyreact


def {stub}(label: str, *, input_id: str) -> shinyreact.Node:
    """Render the stub {Stub} bound to a Shiny action-button input."""
    return shinyreact.Node(
        type="{prefix}:{Stub}",
        props={"label": label, "input_id": input_id},
    )


# Uncomment and adapt if the package needs to ship its own object type that
# render functions return and the JS side consumes via useShinyOutputValue.
# Per RFC §4.4, only subclass when there is package-specific transform logic.
#
# from typing import Any
#
# class render(shinyreact.reactive_output):
#     async def transform(self, value: Any) -> Any:
#         # e.g. return value.to_spec().to_dict()
#         return value
```

Touch the placeholder:

```bash
touch {target_dir}/pkg-py/src/{pkg}/www/.gitkeep
```

### Step 5: Stub factory test

Create `{target_dir}/pkg-py/tests/test_factories.py`:

```python
import {pkg}


def test_{stub}_factory():
    node = {pkg}.{stub}("Click me", input_id="b1")
    assert node.type == "{prefix}:{Stub}"
    assert node.props["label"] == "Click me"
    assert node.props["input_id"] == "b1"
```
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): add procedure §4-5 (Python package + factory test) to scaffold-shinyreact-helper"
```

---

## Task 5: Add the "Procedure: example app, build, verify" sections

**Files:**
- Modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Append Steps 6-9**

Append to `SKILL.md`:

````markdown
### Step 6: Example app

Create `{target_dir}/example/app.py`:

```python
"""{pkg} prototype example app — scaffolded by scaffold-shinyreact-helper."""

import {pkg}
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[{pkg}.dep()])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        clicks = input.b1() or 0
        return shinyreact.Node(
            type="div",
            props={
                "style": {
                    "padding": "16px",
                    "fontFamily": "sans-serif",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "16px",
                }
            },
            children=[
                shinyreact.Node(type="h1", props={"children": "{pkg} prototype"}),
                {pkg}.{stub}("Click me", input_id="b1"),
                shinyreact.Node(
                    type="div",
                    props={"children": f"Stub button clicks: {clicks}"},
                ),
            ],
        )


app = App(app_ui, server)
```

### Step 7: Build, install, verify

Run these commands in order. If any fails, surface the error to the user and stop — do not paper over.

```bash
# Build the bundle
cd {target_dir}/js && npm run build
cd -

# Lint
cd {target_dir}/js && npm run lint
cd -

# Copy bundle to Python package
cp {target_dir}/js/dist/{pkg}.js {target_dir}/pkg-py/src/{pkg}/www/{pkg}.js

# Install the Python package as editable
uv pip install -e {target_dir}/pkg-py

# Run the factory test
cd {target_dir}/pkg-py && uv run python -m pytest tests/test_factories.py -v
cd -
```

Expected outputs:
- `npm run build` produces `{target_dir}/js/dist/{pkg}.js` (size varies by upstream; record it)
- `npm run lint` exits 0 (no TypeScript errors)
- `pytest` reports `1 passed`

### Step 8: Programmatic smoke test

Start the example app in the background, verify HTTP 200 + bundle loads, then stop.

```bash
uv run shiny run --port 8765 {target_dir}/example/app.py &
SHINY_PID=$!
sleep 4
curl -s -o /tmp/scaffold_smoke.html -w "%{http_code}\n" http://localhost:8765/
grep -c "{pkg}-" /tmp/scaffold_smoke.html
# Bundle reachable check:
BUNDLE_URL=$(grep -oE '/lib/{pkg}-[^"]+/{pkg}.js' /tmp/scaffold_smoke.html | head -1)
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8765$BUNDLE_URL"
# Cleanup
kill $SHINY_PID 2>/dev/null || true
pkill -f "shiny run --port 8765" 2>/dev/null || true
```

Expected:
- First curl: `200`
- grep count: ≥ 1
- Second curl: `200`

### Step 9: Final summary to user

Report back:

- Files created (count by directory)
- Bundle size from `ls -lh {target_dir}/js/dist/{pkg}.js`
- All verifications that passed
- Next steps for the package author: "edit `{target_dir}/js/src/components/{Stub}.tsx` to use the real `{upstream_pkg}` component; add more factories in `{target_dir}/pkg-py/src/{pkg}/_components.py` following the shinymui pattern"

Do **not** commit the scaffold to git. Leave that decision to the package author — they may want to iterate on the stub component before committing.
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): add procedure §6-9 (example, build, verify) to scaffold-shinyreact-helper"
```

---

## Task 6: End-to-end smoke test the skill

**Files:**
- None permanently. Temporarily creates `downstream-prototypes/_skill-test-mantine/` which is deleted at the end.

This task validates the skill works end-to-end by following its own procedure manually against a real upstream library. We use `@mantine/core` as the test target — Mantine is another category-1 styled-component library, a natural second test case.

- [ ] **Step 1: Read SKILL.md completely as if invoked**

```bash
cat .claude/skills/scaffold-shinyreact-helper/SKILL.md
```

Treat the file as the source of truth. If anything is unclear or inconsistent, **stop and report a BLOCKED status** — the skill needs to be more precise.

- [ ] **Step 2: Run the procedure with these test inputs**

- short name: `mantine`
- upstream npm package: `@mantine/core`
- catalog prefix: `mantine`
- stub component name: `Button`
- target directory: `downstream-prototypes/_skill-test-mantine`

(The `_skill-test-` prefix marks this as transient, not a real prototype.)

Follow each procedure step in `SKILL.md` exactly. Substitute all placeholders. After each step, briefly note completion.

- [ ] **Step 3: Run all verifications from Step 7-8 of the skill**

- Bundle builds (record size)
- Lint passes
- Factory test passes (`1 passed`)
- HTTP 200 on `localhost:8765/`
- Bundle URL reachable with `200`

If any verification fails, **stop and report which step of `SKILL.md` was unclear or buggy**. The fix is to edit `SKILL.md`, not to paper over the failure in the test scaffold.

- [ ] **Step 4: Capture findings**

After verification passes, write a one-paragraph note covering:
- Whether any step of `SKILL.md` required interpretation beyond what was written
- Whether placeholders or substitutions were ambiguous
- Bundle size for `shinymantine` (compare to shinymui's 4.3 MB — should be similar or smaller since only one component is wired)
- Any gotchas the package author would hit

This note will inform any final edits to `SKILL.md` in Step 5.

- [ ] **Step 5: Patch `SKILL.md` for any issues found**

If Step 4 surfaced anything that should be tightened in the skill, edit `SKILL.md` to fix it. Common categories of fix:
- Substitution rule missing or ambiguous → add to the substitution table
- Step ordering issue → reorder
- Command that didn't work on first try → document the gotcha
- Verification expected output that turned out wrong → correct it

If no fixes needed, skip to Step 6.

- [ ] **Step 6: Clean up the test scaffold**

```bash
# Stop any leftover server
pkill -f "shiny run --port 8765" 2>/dev/null || true
# Remove the test directory entirely
rm -rf downstream-prototypes/_skill-test-mantine
# Verify it's gone
ls downstream-prototypes/ | grep -c "_skill-test" || echo "clean"
```

The skill itself stays in `.claude/skills/`. The test scaffold is throwaway.

- [ ] **Step 7: Commit any SKILL.md edits from Step 5 (if any)**

If `SKILL.md` was edited in Step 5:

```bash
git status                          # verify only SKILL.md is modified
git diff .claude/skills/scaffold-shinyreact-helper/SKILL.md   # review the edits
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): patch scaffold-shinyreact-helper based on end-to-end smoke test"
```

If `SKILL.md` was not edited, skip the commit — the skill works as written.

- [ ] **Step 8: Final RFC acceptance update**

Edit `docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md`. Find the existing "Status (2026-05-12):" line near the bottom (the one added by the shinymui-prototype plan's Task 12). Update it to:

```markdown
**Status (2026-05-12):** All four acceptance criteria satisfied. The MUI prototype lives at `downstream-prototypes/shinymui/` (5 components, all archetypes covered, validated via `downstream-prototypes/shinymui/example/app.py`). The scaffolding skill lives at `.claude/skills/scaffold-shinyreact-helper/SKILL.md` and has been validated end-to-end by scaffolding a transient `shinymantine` package that built, linted, tested, and served HTTP 200. The follow-up umbrella issue (§8) can now be filed.
```

Commit:

```bash
git add docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md
git commit -m "docs(rfc): mark all helper-packages RFC acceptance criteria satisfied"
```

---

## Final verification

- [ ] **Step 1: Confirm the skill file exists and looks complete**

```bash
ls -la .claude/skills/scaffold-shinyreact-helper/SKILL.md
wc -l .claude/skills/scaffold-shinyreact-helper/SKILL.md
```

Expect: file exists, roughly 200-400 lines (full procedure).

- [ ] **Step 2: Confirm no test artifacts remain**

```bash
ls downstream-prototypes/ | grep "_skill-test" && echo "LEFTOVER FOUND" || echo "clean"
```

Expect: `clean`.

- [ ] **Step 3: Confirm git is clean**

```bash
git status
```

Expect: `nothing to commit, working tree clean`.

- [ ] **Step 4: Confirm the RFC status line is updated**

```bash
grep -A1 "Status (2026-05-12)" docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md
```

Expect: the "All four acceptance criteria satisfied" version.

- [ ] **Step 5: Spot-check the skill is invocable**

The skill is now discoverable by Claude Code's Skill tool. From a future session, `/scaffold-shinyreact-helper` (or invoking via the Skill tool) should load `SKILL.md`. We do not test this in-session — it requires a fresh agent — but verify the frontmatter parses by reading the first 5 lines:

```bash
head -5 .claude/skills/scaffold-shinyreact-helper/SKILL.md
```

Expect:
```
---
name: scaffold-shinyreact-helper
description: Scaffold a new shinyreact downstream helper-package prototype that mirrors the shinymui reference layout. Use when starting a new helper package for a React UI library (e.g., shinymantine, shinyradix, shinyaggrid). Asks for the upstream package, short name, and target directory; produces a working scaffold with one stub component that builds and loads end-to-end.
---
```

If all five final-verification steps pass, the plan is complete. The repo now satisfies all four acceptance criteria of the helper-packages RFC.
