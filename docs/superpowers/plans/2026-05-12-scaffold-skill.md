# Scaffold-Helper Claude Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained Claude Code skill at `.claude/skills/scaffold-shinyreact-helper/` that scaffolds a new shinyreact downstream helper-package prototype mirroring the conventions in [the helper-packages RFC](../specs/2026-05-12-downstream-helper-packages-rfc-design.md). The skill takes an upstream React library reference, a short name, and a target directory; produces a working scaffold with one stub component that builds, lints, tests, and serves HTTP 200.

**Architecture:** The skill is a `SKILL.md` file (procedure + substitution rules) plus a `templates/` directory containing every file the scaffold will produce, with `{{placeholders}}` for the variable parts. SKILL.md instructs Claude to render each template by reading it, substituting placeholders, and writing the result to the target. **No reference to `downstream-prototypes/shinymui/` at runtime** — the skill is fully self-contained. Validated by an end-to-end smoke test that scaffolds a transient `_skill-test-mantine/` package and verifies it works.

**Tech Stack:** Claude Code skills system (Skill tool + `.claude/skills/<name>/SKILL.md` + supporting files), Markdown with YAML frontmatter, mustache-style `{{placeholder}}` substitutions.

**Non-goals (this plan):**
- Auto-discovering all components in the upstream library — the skill scaffolds one stub component
- Theming / styling integration
- PyPI/npm publishing setup, CI workflows
- Per-category divergence handling — targets the category-1 baseline only
- Self-validating the skill via subagent pressure tests (per superpowers:writing-skills) — out of scope for the prototype skill

---

## File structure

```
.claude/skills/scaffold-shinyreact-helper/
  SKILL.md                                 # procedure + substitution rules + smoke test
  templates/
    README.md.tpl
    js/
      package.json.tpl
      tsconfig.json.tpl
      vite.config.ts.tpl
      .gitignore.tpl
      src/
        types.ts.tpl
        index.ts.tpl
        components/
          Stub.tsx.tpl
    pkg-py/
      pyproject.toml.tpl
      src/
        __init__.py.tpl
        _dep.py.tpl
        _components.py.tpl
      tests/
        test_factories.py.tpl
    example/
      app.py.tpl
```

The `.tpl` extension marks files that are templates (not executable as-is). They use `{{placeholder}}` markers for the substitution table.

End-to-end smoke test (Task 8) creates a transient `downstream-prototypes/_skill-test-mantine/` that is **not** committed and is deleted at the end of the task.

---

## Placeholder conventions

Throughout the templates and SKILL.md:

| Placeholder | Derived from | Example (for `mantine`) |
|-------------|--------------|--------------------------|
| `{{name}}` | short package name (lowercase) | `mantine` |
| `{{pkg}}` | `shiny{{name}}` | `shinymantine` |
| `{{Name}}` | short name, capitalized | `Mantine` |
| `{{prefix}}` | catalog prefix | `mantine` |
| `{{Stub}}` | stub component name, PascalCase | `Button` |
| `{{stub}}` | stub component name, snake_case lowercase | `button` |
| `{{target_dir}}` | target directory | `downstream-prototypes/shinymantine` |
| `{{upstream_pkg}}` | upstream npm package | `@mantine/core` |

`{{...}}` (double curly) was chosen because single `{` collides heavily with JSX/TS and Python f-strings.

---

## Task 1: Scaffold skill directory and SKILL.md skeleton

**Files:**
- Create: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p .claude/skills/scaffold-shinyreact-helper/templates/js/src/components
mkdir -p .claude/skills/scaffold-shinyreact-helper/templates/pkg-py/src
mkdir -p .claude/skills/scaffold-shinyreact-helper/templates/pkg-py/tests
mkdir -p .claude/skills/scaffold-shinyreact-helper/templates/example
```

- [ ] **Step 2: Write the `SKILL.md` skeleton (frontmatter + overview only — procedure sections added in later tasks)**

```markdown
---
name: scaffold-shinyreact-helper
description: Scaffold a new shinyreact downstream helper-package prototype with one stub component wired end-to-end. Use when starting a new helper package for a React UI library (e.g., shinymantine, shinyradix, shinyaggrid). Asks for the upstream package, short name, and target directory; renders templates with substitutions; verifies the scaffold builds, lints, tests, and serves HTTP 200.
---

# Scaffold a shinyreact helper package

## Overview

This skill produces a new helper-package prototype at a target directory. The output is **one stub component** wired end-to-end — the package author adds further components by following the established pattern (factory in Python + registered React component + entry-app wiring).

**Conventions enforced** (from [the helper-packages RFC](../../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md) §4):

- IIFE Vite bundle with React externalized to `window.shinyreact.React`
- Catalog keys namespaced as `<prefix>:<Component>`
- Python factory functions returning `shinyreact.Node(type="<prefix>:<Component>", props=...)`
- `HTMLDependency` produced by a `dep()` helper, consumed via `shinyreact.ui_output(id, extra_deps=[dep()])`
- Per-package directory layout: `js/` + `pkg-py/` + `example/`

## Non-goals

This skill targets the category-1 styled-component-library baseline. It does not auto-discover all components in the upstream library, configure theming, set up CI/publishing, or handle per-category divergences (headless, copy-paste, specialized). Those are added by the package author after scaffolding.

## How it works

The skill is fully self-contained. All file contents live as templates under `.claude/skills/scaffold-shinyreact-helper/templates/`, each using `{{placeholder}}` markers. The procedure: collect inputs → render each template with substitutions → write to the target directory → build and verify.

The rest of the procedure (inputs, substitution rules, scaffolding steps, verification) lands in subsequent tasks.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md \
        .claude/skills/scaffold-shinyreact-helper/templates/
git commit -m "feat(skill): scaffold-shinyreact-helper SKILL.md skeleton + empty templates/ tree"
```

(The empty `templates/` directories will not be tracked by git unless they contain files — they will be populated in subsequent tasks. That's fine; this commit just establishes SKILL.md.)

---

## Task 2: Add Inputs + Substitution rules sections to SKILL.md

**Files:**
- Modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Append the Inputs section**

Append to `SKILL.md`:

```markdown
## Inputs

Before scaffolding, collect these from the user one at a time. Validate each before moving on.

1. **Short package name** (e.g., `mantine`, `radix`, `aggrid`). Lowercase, no separators, no `shiny` prefix — the skill prepends `shiny` to form the package name (e.g., `mantine` → `shinymantine`).
2. **Upstream npm package** that the helper will wrap (e.g., `@mantine/core`, `@radix-ui/react-dialog`, `ag-grid-react`). Used as a `dependencies` entry in the scaffold's `js/package.json`. (For now, a single package; multiple packages can be added by hand after scaffolding.)
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
```

- [ ] **Step 2: Append the Substitution rules section**

Append to `SKILL.md`:

```markdown
## Substitution rules

Templates under `templates/` use mustache-style `{{placeholder}}` markers. Substitute each occurrence with the corresponding value derived from the inputs:

| Placeholder | Derived from | Example (for `mantine`) |
|-------------|--------------|--------------------------|
| `{{name}}` | short package name (lowercase) | `mantine` |
| `{{pkg}}` | `shiny{{name}}` | `shinymantine` |
| `{{Name}}` | short name, capitalized | `Mantine` |
| `{{prefix}}` | catalog prefix | `mantine` |
| `{{Stub}}` | stub component name, PascalCase | `Button` |
| `{{stub}}` | stub component name, snake_case lowercase | `button` |
| `{{target_dir}}` | target directory | `downstream-prototypes/shinymantine` |
| `{{upstream_pkg}}` | upstream npm package | `@mantine/core` |

Substitution is plain textual replacement — no escaping, no conditional logic. If a template doesn't contain a placeholder, write it verbatim.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): inputs + substitution rules sections"
```

---

## Task 3: Write README + JS config templates

**Files:**
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/README.md.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/js/package.json.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/js/tsconfig.json.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/js/vite.config.ts.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/js/.gitignore.tpl`

- [ ] **Step 1: Write `templates/README.md.tpl`**

Use a HEREDOC to write the file exactly (the inner triple-backtick block must be preserved literally):

```
# {{pkg}} (prototype)

**Status:** scaffold from `scaffold-shinyreact-helper`. Validates conventions in the [helper-packages RFC](../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md).

Exposes `{{upstream_pkg}}` components to `shinyreact`. Currently scaffolded with one stub component (`{{Stub}}`); add more by following the pattern in `downstream-prototypes/shinymui/`.

## Run the example

\`\`\`bash
cd {{target_dir}}
(cd js && npm install && npm run build)
cp js/dist/{{pkg}}.js pkg-py/src/{{pkg}}/www/{{pkg}}.js
uv pip install -e pkg-py
uv run shiny run --reload example/app.py
\`\`\`
```

Note: the `\`\`\`bash` and closing `\`\`\`` in the file source are LITERAL backslash-escaped backticks because this template content is itself inside a code block in this plan. The actual file should contain unescaped triple-backticks. When implementing, write triple-backticks (` ``` `), not backslash-escaped ones.

- [ ] **Step 2: Write `templates/js/package.json.tpl`**

```json
{
  "name": "@{{pkg}}/js",
  "private": true,
  "version": "0.0.0-prototype",
  "type": "module",
  "scripts": {
    "build": "vite build",
    "watch": "vite build --watch",
    "lint": "tsc --noEmit"
  },
  "peerDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "dependencies": {
    "{{upstream_pkg}}": "latest"
  },
  "devDependencies": {
    "@types/react": "^19.2.0",
    "@types/react-dom": "^19.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

Note: `"latest"` for the upstream package is a deliberate weak pin — the user is expected to tighten it for a real package. For a styled-component library that needs emotion, the user may need to add `@emotion/react` and `@emotion/styled` manually after scaffolding. The SKILL.md procedure will mention this.

- [ ] **Step 3: Write `templates/js/tsconfig.json.tpl`** — verbatim copy of shinymui's tsconfig.json (no placeholders):

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Write `templates/js/vite.config.ts.tpl`**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    lib: {
      entry: "src/index.ts",
      name: "{{pkg}}",
      formats: ["iife"],
      fileName: () => "{{pkg}}.js",
    },
    outDir: "dist",
    rollupOptions: {
      external: ["react", "react-dom", "react-dom/client"],
      output: {
        globals: {
          react: "window.shinyreact.React",
          "react-dom": "window.shinyreact.ReactDOM",
          "react-dom/client": "window.shinyreact.ReactDOM",
        },
        assetFileNames: "{{pkg}}.[ext]",
      },
    },
  },
});
```

- [ ] **Step 5: Write `templates/js/.gitignore.tpl`**

```
node_modules/
```

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/templates/
git commit -m "feat(skill): README + JS config templates"
```

---

## Task 4: Write JS source templates (types, index, stub component)

**Files:**
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/js/src/types.ts.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/js/src/index.ts.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/js/src/components/Stub.tsx.tpl`

- [ ] **Step 1: Write `templates/js/src/types.ts.tpl`** — copy from `downstream-prototypes/shinymui/js/src/types.ts` verbatim (no placeholders; this file is generic):

```ts
import type { ComponentType, ReactNode } from "react";

// Mirrors shinyreact's RegisteredComponentProps and ComponentRegistry from
// js/src/spec.ts. Kept local to avoid cross-project relative imports.

export interface Element {
  type: string;
  props: Record<string, unknown>;
  children?: string[];
}

export interface RegisteredComponentProps {
  element: Element;
  children: ReactNode;
}

export type ComponentRegistry = Record<
  string,
  ComponentType<RegisteredComponentProps>
>;

declare global {
  interface Window {
    shinyreact: {
      registerComponents: (
        catalog: unknown,
        registry: ComponentRegistry,
      ) => void;
      // priority values match Shiny's input event priorities used by
      // @posit/shiny-react. Stable strings in the wire protocol.
      useShinyInput: <T>(
        id: string,
        defaultValue: T,
        options?: { debounceMs?: number; priority?: "immediate" | "deferred" | "event" },
      ) => [T, (value: T) => void];
      useShinyOutputValue: <T>(id: string, defaultValue?: T) => T;
      // Other hooks exist (useSetShinyInput, useShinyMessageHandler, ...) but
      // are not used by the scaffold; add them as needed.
      React: typeof import("react");
      ReactDOM: unknown;
    };
  }
}

export {};
```

- [ ] **Step 2: Write `templates/js/src/index.ts.tpl`**

```ts
import type { ComponentRegistry } from "./types";
import { {{Stub}} } from "./components/{{Stub}}";

const registry: ComponentRegistry = {
  "{{prefix}}:{{Stub}}": {{Stub}},
};

const catalog = { name: "{{pkg}}", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
```

- [ ] **Step 3: Write `templates/js/src/components/Stub.tsx.tpl`**

```tsx
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

export function {{Stub}}({ element }: RegisteredComponentProps) {
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

Note: the stub uses a plain HTML `<button>`, not a styled component from `{{upstream_pkg}}`. The package author's first edit after scaffolding should be swapping this to use the real upstream component. The stub exists to verify the scaffold loads end-to-end with the simplest possible component code.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/templates/js/src/
git commit -m "feat(skill): JS source templates (types, index, stub component)"
```

---

## Task 5: Write Python templates

**Files:**
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/pyproject.toml.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/src/__init__.py.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/src/_dep.py.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/src/_components.py.tpl`
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/tests/test_factories.py.tpl`

- [ ] **Step 1: Write `templates/pkg-py/pyproject.toml.tpl`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{pkg}}"
version = "0.0.0.dev0"
description = "Prototype helper package exposing {{upstream_pkg}} to shinyreact"
requires-python = ">=3.10"
dependencies = [
    "shiny>=1.0.0",
    "htmltools>=0.5.0",
    "shinyreact",
]

[tool.hatch.build.targets.wheel]
packages = ["src/{{pkg}}"]

[tool.hatch.build.targets.wheel.force-include]
"src/{{pkg}}/www/{{pkg}}.js" = "{{pkg}}/www/{{pkg}}.js"
```

(Note: `0.0.0.dev0` is required by PEP 440 — `0.0.0-prototype` is rejected by hatchling. Found during shinymui prototype.)

- [ ] **Step 2: Write `templates/pkg-py/src/__init__.py.tpl`**

```python
from ._components import {{stub}}
from ._dep import dep

__all__ = ["dep", "{{stub}}"]
```

- [ ] **Step 3: Write `templates/pkg-py/src/_dep.py.tpl`**

```python
from pathlib import Path

from htmltools import HTMLDependency

_www_dir = Path(__file__).parent / "www"


def dep() -> HTMLDependency:
    """HTMLDependency for the {{pkg}} JS bundle.

    Versioned by mtime of the bundled JS file so browsers re-fetch when the
    bundle is rebuilt during development. A real package would pin to its
    release version.
    """
    bundle = _www_dir / "{{pkg}}.js"
    version = str(int(bundle.stat().st_mtime)) if bundle.exists() else "0"
    return HTMLDependency(
        name="{{pkg}}",
        version=version,
        source={"subdir": str(_www_dir)},
        script={"src": "{{pkg}}.js", "defer": ""},
    )
```

- [ ] **Step 4: Write `templates/pkg-py/src/_components.py.tpl`**

```python
"""Python factory functions for {{Name}} components.

Each factory returns a ``shinyreact.Node`` with a ``{{prefix}}:``-namespaced type
string. Currently scaffolded with one stub factory; add more by following the
pattern.
"""

import shinyreact


def {{stub}}(label: str, *, input_id: str) -> shinyreact.Node:
    """Render the stub {{Stub}} bound to a Shiny action-button input."""
    return shinyreact.Node(
        type="{{prefix}}:{{Stub}}",
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

- [ ] **Step 5: Write `templates/pkg-py/tests/test_factories.py.tpl`**

```python
import {{pkg}}


def test_{{stub}}_factory():
    node = {{pkg}}.{{stub}}("Click me", input_id="b1")
    assert node.type == "{{prefix}}:{{Stub}}"
    assert node.props["label"] == "Click me"
    assert node.props["input_id"] == "b1"
```

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/templates/pkg-py/
git commit -m "feat(skill): Python package templates (pyproject, init, _dep, _components, test)"
```

---

## Task 6: Write example app template

**Files:**
- Create: `.claude/skills/scaffold-shinyreact-helper/templates/example/app.py.tpl`

- [ ] **Step 1: Write `templates/example/app.py.tpl`**

```python
"""{{pkg}} prototype example app — scaffolded by scaffold-shinyreact-helper."""

import {{pkg}}
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[{{pkg}}.dep()])


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
                shinyreact.Node(type="h1", props={"children": "{{pkg}} prototype"}),
                {{pkg}}.{{stub}}("Click me", input_id="b1"),
                shinyreact.Node(
                    type="div",
                    props={"children": f"Stub button clicks: {clicks}"},
                ),
            ],
        )


app = App(app_ui, server)
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/templates/example/
git commit -m "feat(skill): example app template"
```

---

## Task 7: Write the Procedure section in SKILL.md

This is where SKILL.md tells Claude how to actually use the templates.

**Files:**
- Modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Append the Procedure header and Step 1 (directory + template rendering)**

Append to `SKILL.md`:

````markdown
## Procedure

Run these steps in order. After each step, briefly confirm to the user what landed. Do not commit the scaffold — leave that to the package author.

### Step 1: Create the directory layout

```bash
mkdir -p {{target_dir}}/js/src/components
mkdir -p {{target_dir}}/pkg-py/src/{{pkg}}/www
mkdir -p {{target_dir}}/pkg-py/tests
mkdir -p {{target_dir}}/example
```

### Step 2: Render templates

For each template under `.claude/skills/scaffold-shinyreact-helper/templates/`, read the file, perform every substitution from the table in the "Substitution rules" section above, and write to the corresponding location in `{{target_dir}}`. The mapping:

| Template | Destination |
|----------|-------------|
| `templates/README.md.tpl` | `{{target_dir}}/README.md` |
| `templates/js/package.json.tpl` | `{{target_dir}}/js/package.json` |
| `templates/js/tsconfig.json.tpl` | `{{target_dir}}/js/tsconfig.json` |
| `templates/js/vite.config.ts.tpl` | `{{target_dir}}/js/vite.config.ts` |
| `templates/js/.gitignore.tpl` | `{{target_dir}}/js/.gitignore` |
| `templates/js/src/types.ts.tpl` | `{{target_dir}}/js/src/types.ts` |
| `templates/js/src/index.ts.tpl` | `{{target_dir}}/js/src/index.ts` |
| `templates/js/src/components/Stub.tsx.tpl` | `{{target_dir}}/js/src/components/{{Stub}}.tsx` |
| `templates/pkg-py/pyproject.toml.tpl` | `{{target_dir}}/pkg-py/pyproject.toml` |
| `templates/pkg-py/src/__init__.py.tpl` | `{{target_dir}}/pkg-py/src/{{pkg}}/__init__.py` |
| `templates/pkg-py/src/_dep.py.tpl` | `{{target_dir}}/pkg-py/src/{{pkg}}/_dep.py` |
| `templates/pkg-py/src/_components.py.tpl` | `{{target_dir}}/pkg-py/src/{{pkg}}/_components.py` |
| `templates/pkg-py/tests/test_factories.py.tpl` | `{{target_dir}}/pkg-py/tests/test_factories.py` |
| `templates/example/app.py.tpl` | `{{target_dir}}/example/app.py` |

Also touch the placeholder for the empty `www/` directory:

```bash
touch {{target_dir}}/pkg-py/src/{{pkg}}/www/.gitkeep
```

### Step 3: Install JS dependencies

```bash
cd {{target_dir}}/js && npm install
```

Wait for completion (1-3 minutes for a typical UI library). If `npm install` warns about peer-dependency conflicts (e.g., `@mui/icons-material` requiring a different `@mui/material` major), surface the warning to the user — they may need to pin the upstream package version more tightly. Do not auto-fix.

For styled-component libraries that need emotion (MUI, Mantine), the user may need to add these themselves after scaffolding:

```bash
cd {{target_dir}}/js && npm install @emotion/react @emotion/styled
```

Mention this if and only if the upstream package is in the MUI/Mantine family.

### Step 4: Build the bundle

```bash
cd {{target_dir}}/js && npm run build
```

Expected: writes `{{target_dir}}/js/dist/{{pkg}}.js`. If the build fails because the upstream package isn't actually used in the stub (the stub uses a plain `<button>`), the build should still succeed because the import is only declared in `package.json`, not referenced in source. The user replaces the stub's plain button with the upstream component as their first manual edit.

### Step 5: Lint

```bash
cd {{target_dir}}/js && npm run lint
```

Expected: exits 0 with no output. If lint fails, surface the error verbatim.

### Step 6: Copy bundle to Python package www/

```bash
cp {{target_dir}}/js/dist/{{pkg}}.js {{target_dir}}/pkg-py/src/{{pkg}}/www/{{pkg}}.js
```

### Step 7: Install the Python package as editable

```bash
uv pip install -e {{target_dir}}/pkg-py
```

If this fails because `shinyreact` isn't resolvable (the prototype shinymui hit this), the workaround is to install into the parent repo's venv directly:

```bash
.venv/bin/pip install -e {{target_dir}}/pkg-py
```

### Step 8: Run the factory test

```bash
cd {{target_dir}}/pkg-py && uv run python -m pytest tests/test_factories.py -v
```

Or fall back to `.venv/bin/python -m pytest tests/test_factories.py -v` if `uv run` has venv-resolution issues.

Expected: `1 passed` (the stub factory test).
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): procedure §1-8 (render, install, build, lint, test)"
```

---

## Task 8: Add Smoke-test + Final-summary sections to SKILL.md

**Files:**
- Modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md`

- [ ] **Step 1: Append the smoke-test and final-summary sections**

Append to `SKILL.md`:

````markdown
### Step 9: Programmatic smoke test

Start the example app, verify HTTP 200 + bundle loads, then stop. Use a port unlikely to collide (8765 is the convention used by the shinymui prototype's smoke tests).

```bash
uv run shiny run --port 8765 {{target_dir}}/example/app.py &
SHINY_PID=$!
sleep 4

# Page returns 200
curl -s -o /tmp/scaffold_smoke.html -w "%{http_code}\n" http://localhost:8765/

# HTML references the bundle URL with the right name
grep -c "{{pkg}}-" /tmp/scaffold_smoke.html

# Bundle URL itself returns 200
BUNDLE_URL=$(grep -oE '/lib/{{pkg}}-[^"]+/{{pkg}}\.js' /tmp/scaffold_smoke.html | head -1)
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8765$BUNDLE_URL"

# Cleanup
kill $SHINY_PID 2>/dev/null || true
pkill -f "shiny run --port 8765" 2>/dev/null || true
```

Expected outputs:
- First curl: `200`
- grep count: at least `1`
- Second curl: `200`

If any of these fail, surface the failure to the user and stop. Common causes: port 8765 in use (try 8766), `shinyreact` not installed in the venv, bundle copy failed.

### Step 10: Final summary

Report back to the user:

- Number of files created (count by walking `{{target_dir}}`)
- Bundle size from `ls -lh {{target_dir}}/js/dist/{{pkg}}.js`
- All verifications that passed (build, lint, factory test, HTTP 200, bundle 200)
- **Next steps for the package author:**
  - Edit `{{target_dir}}/js/src/components/{{Stub}}.tsx` to use the real `{{upstream_pkg}}` component instead of the plain `<button>`
  - Add more factories in `{{target_dir}}/pkg-py/src/{{pkg}}/_components.py` following the pattern
  - Add tests in `{{target_dir}}/pkg-py/tests/test_factories.py` for each new factory
  - For styled-component libraries: install peer deps like `@emotion/react @emotion/styled`
  - Reference `downstream-prototypes/shinymui/` for examples of more complex patterns (children/composition, server-pushed data via `useShinyOutputValue`)
  - When ready to commit: `git add {{target_dir}}/` then commit with a descriptive message

Do **not** commit the scaffold — leave that decision to the package author.
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/scaffold-shinyreact-helper/SKILL.md
git commit -m "feat(skill): procedure §9-10 (smoke test + final summary)"
```

---

## Task 9: End-to-end smoke test the skill

**Files:**
- Modify: `docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md` (final acceptance status line at the end of Task 9)
- Possibly modify: `.claude/skills/scaffold-shinyreact-helper/SKILL.md` (only if the test surfaces issues)

This task validates the skill works end-to-end by running its own procedure against `@mantine/core` (a real category-1 styled library). The test scaffold is transient and is deleted at the end.

- [ ] **Step 1: Read SKILL.md completely as if invoked**

```bash
cat .claude/skills/scaffold-shinyreact-helper/SKILL.md
```

Treat the file as the source of truth. If anything is unclear or inconsistent, **stop and report a BLOCKED status** — the skill needs to be more precise before it can be exercised.

- [ ] **Step 2: Run the procedure with these inputs**

- short name: `mantine`
- upstream npm package: `@mantine/core`
- catalog prefix: `mantine`
- stub component name: `Button`
- target directory: `downstream-prototypes/_skill-test-mantine`

The `_skill-test-` prefix marks this as transient — not a real prototype.

Substitution values for this run:

| Placeholder | Value |
|-------------|-------|
| `{{name}}` | `mantine` |
| `{{pkg}}` | `shinymantine` |
| `{{Name}}` | `Mantine` |
| `{{prefix}}` | `mantine` |
| `{{Stub}}` | `Button` |
| `{{stub}}` | `button` |
| `{{target_dir}}` | `downstream-prototypes/_skill-test-mantine` |
| `{{upstream_pkg}}` | `@mantine/core` |

Follow each procedure step in `SKILL.md` exactly. Substitute all placeholders. After each step, briefly note completion to your own log.

- [ ] **Step 3: Run all verifications (Steps 4, 5, 8, 9 of the skill procedure)**

- Bundle builds (record size)
- Lint passes
- Factory test passes (`1 passed`)
- HTTP 200 on `localhost:8765/`
- Bundle URL reachable with `200`

If any verification fails, **stop and identify which step of `SKILL.md` was unclear, missing, or buggy**. The fix is to edit `SKILL.md`, not to paper over the failure in the test scaffold.

- [ ] **Step 4: Capture findings**

Write a short note (5-10 bullet points or a paragraph) covering:
- Whether any step of `SKILL.md` required interpretation beyond what was written
- Whether any placeholder or substitution was ambiguous
- Whether `npm install @mantine/core` succeeded with the `"latest"` pin (and whether emotion peer-deps were needed)
- Bundle size for `shinymantine` (note: should be small since the stub uses plain `<button>`, not Mantine; the `@mantine/core` dep declared in package.json but unreferenced should mostly be tree-shaken — record the actual size)
- Any gotchas the package author would hit

This note will inform any final edits to `SKILL.md` in Step 5.

- [ ] **Step 5: Patch `SKILL.md` for any issues found**

If Step 4 surfaced anything that should be tightened in the skill, edit `SKILL.md` to fix it. Common categories of fix:
- Substitution rule missing or ambiguous → add to the substitution table
- A template file had an issue → fix the corresponding `.tpl` file
- Step ordering issue → reorder
- Command that didn't work on first try → document the workaround
- Verification expected output that turned out wrong → correct it

Commit any fixes:

```bash
git status                                                                       # verify scope
git diff .claude/skills/scaffold-shinyreact-helper/                              # review
git add .claude/skills/scaffold-shinyreact-helper/
git commit -m "feat(skill): patch scaffold-shinyreact-helper based on end-to-end smoke test"
```

If no fixes needed, skip the commit — the skill works as written.

- [ ] **Step 6: Clean up the test scaffold**

```bash
# Stop any leftover server
pkill -f "shiny run --port 8765" 2>/dev/null || true

# Remove the test directory entirely
rm -rf downstream-prototypes/_skill-test-mantine

# Verify it's gone
ls downstream-prototypes/ | grep -c "_skill-test" && echo "LEFTOVER FOUND" || echo "clean"
```

Expect: `clean`.

The skill itself stays in `.claude/skills/`. The test scaffold is throwaway.

- [ ] **Step 7: Update the RFC acceptance status**

Edit `docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md`. Find the existing "Status (2026-05-12):" line near the bottom (the one added at the end of the shinymui-prototype plan). Replace it with:

```markdown
**Status (2026-05-12):** All four acceptance criteria satisfied. The MUI prototype lives at `downstream-prototypes/shinymui/` (5 components, all archetypes covered, validated via `downstream-prototypes/shinymui/example/app.py`). The scaffolding skill lives at `.claude/skills/scaffold-shinyreact-helper/` with `SKILL.md` plus `templates/` (14 template files); it was validated end-to-end by scaffolding a transient `shinymantine` package that built, linted, tested, and served HTTP 200. The follow-up umbrella issue (§8) can now be filed.
```

Commit:

```bash
git add docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md
git commit -m "docs(rfc): mark all helper-packages RFC acceptance criteria satisfied"
```

---

## Final verification

- [ ] **Step 1: Confirm the skill files exist**

```bash
find .claude/skills/scaffold-shinyreact-helper -type f | sort
```

Expect 15 entries: `SKILL.md` + 14 template files:

```
.claude/skills/scaffold-shinyreact-helper/SKILL.md
.claude/skills/scaffold-shinyreact-helper/templates/README.md.tpl
.claude/skills/scaffold-shinyreact-helper/templates/example/app.py.tpl
.claude/skills/scaffold-shinyreact-helper/templates/js/.gitignore.tpl
.claude/skills/scaffold-shinyreact-helper/templates/js/package.json.tpl
.claude/skills/scaffold-shinyreact-helper/templates/js/src/components/Stub.tsx.tpl
.claude/skills/scaffold-shinyreact-helper/templates/js/src/index.ts.tpl
.claude/skills/scaffold-shinyreact-helper/templates/js/src/types.ts.tpl
.claude/skills/scaffold-shinyreact-helper/templates/js/tsconfig.json.tpl
.claude/skills/scaffold-shinyreact-helper/templates/js/vite.config.ts.tpl
.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/pyproject.toml.tpl
.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/src/__init__.py.tpl
.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/src/_components.py.tpl
.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/src/_dep.py.tpl
.claude/skills/scaffold-shinyreact-helper/templates/pkg-py/tests/test_factories.py.tpl
```

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
grep "All four acceptance criteria satisfied" docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md
```

Expect: at least one match (the updated status line).

- [ ] **Step 5: Spot-check SKILL.md frontmatter parses**

```bash
head -5 .claude/skills/scaffold-shinyreact-helper/SKILL.md
```

Expect:
```
---
name: scaffold-shinyreact-helper
description: Scaffold a new shinyreact downstream helper-package prototype with one stub component wired end-to-end. Use when starting a new helper package for a React UI library (e.g., shinymantine, shinyradix, shinyaggrid). Asks for the upstream package, short name, and target directory; renders templates with substitutions; verifies the scaffold builds, lints, tests, and serves HTTP 200.
---
```

If all five final-verification steps pass, the plan is complete. The repo now satisfies all four acceptance criteria of the helper-packages RFC. The skill is fully self-contained — it does not depend on `downstream-prototypes/shinymui/` continuing to exist.
