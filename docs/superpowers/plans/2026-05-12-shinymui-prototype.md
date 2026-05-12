# MUI Prototype + RFC Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 5-component MUI helper-package prototype at `downstream-prototypes/shinymui/`, plus a working example app, validating the conventions in `docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md` and folding findings back into the RFC's open-questions section.

**Architecture:** Vite IIFE bundle externalizes React/ReactDOM to `window.shinyreact.*` and calls `window.shinyreact.registerComponents()` at load. Python package exposes factory functions returning `shinyreact.Node` instances with `mui:`-namespaced type strings; a `_dep()` helper produces the `HTMLDependency` consumers pass to `shinyreact.ui_output(extra_deps=[...])`. Example app at `downstream-prototypes/shinymui/example/app.py` exercises every component and serves as the integration test.

**Tech Stack:** Vite 5, TypeScript 5, React 19, `@mui/material`, `@mui/x-data-grid`, Python 3.10+, `shinyreact` (this repo), `htmltools`, `hatchling` (build backend), `pytest`.

**Non-goals (this plan):**
- The `scaffold-shinyreact-helper` Claude skill (separate follow-on plan).
- Publishing the prototype to PyPI/npm.
- Per-category divergence handling (headless, copy-paste, specialized). MUI baseline only.
- Comprehensive test coverage. Factories get one assertion each; the example app is the integration test.

---

## File structure

```
downstream-prototypes/
  README.md                              # one paragraph: "prototypes validating RFC, not published"
  shinymui/
    README.md                            # links to RFC, marks as throwaway
    js/
      package.json                       # @mui/material, @mui/x-data-grid, vite, react peer
      tsconfig.json
      vite.config.ts                     # IIFE, externalize react/react-dom → window.shinyreact.*
      src/
        index.ts                         # entry: imports components, calls registerComponents
        components/
          Button.tsx
          TextField.tsx
          Slider.tsx
          Card.tsx
          DataGrid.tsx
      dist/
        shinymui.js                      # built bundle (committed)
    pkg-py/
      pyproject.toml                     # hatchling backend, src layout
      src/
        shinymui/
          __init__.py                    # exports: dep, button, text_field, slider, card, data_grid
          _dep.py                        # HTMLDependency factory (mtime-based version)
          _components.py                 # factory functions returning shinyreact.Node
          www/
            shinymui.js                  # copied from js/dist/ (committed)
      tests/
        test_factories.py                # one assertion per factory
    example/
      app.py                             # single-page example mounting all 5 components
docs/superpowers/specs/
  2026-05-12-downstream-helper-packages-rfc-design.md   # existing — edited in last task
```

The prototype intentionally does NOT add a Makefile target or pre-commit integration — those are decisions for the real `shinymui` package, not the prototype.

---

## Task 1: Scaffold `downstream-prototypes/` directory and shinymui placeholders

**Files:**
- Create: `downstream-prototypes/README.md`
- Create: `downstream-prototypes/shinymui/README.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p downstream-prototypes/shinymui
```

- [ ] **Step 2: Write `downstream-prototypes/README.md`**

```markdown
# Downstream Prototypes

Throwaway helper-package prototypes used to validate the conventions in
[`docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md`](../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md).

Nothing here is published. Each prototype is superseded by its real-package
issue once the conventions are validated.

## Current prototypes

- `shinymui/` — MUI baseline (category 1: styled component library)
```

- [ ] **Step 3: Write `downstream-prototypes/shinymui/README.md`**

```markdown
# shinymui (prototype)

**Status:** throwaway prototype. Not published. Validates conventions in the
[helper-packages RFC](../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md).

Exposes 5 MUI components to `shinyreact`:

- `Button` (basic factory + slot API + controlled-event input)
- `TextField` (controlled string input)
- `Slider` (controlled numeric input)
- `Card` (children / composition)
- `DataGrid` (specialized component, server-pushed data)

Once the conventions are validated, this prototype is replaced by a real
`shinymui` package (see the follow-up umbrella issue spawned by the RFC).

## Run the example

\`\`\`bash
cd downstream-prototypes/shinymui
(cd js && npm install && npm run build)  # builds js/dist/shinymui.js
cp js/dist/shinymui.js pkg-py/src/shinymui/www/shinymui.js
uv pip install -e pkg-py
uv run shiny run --reload example/app.py
\`\`\`
```

- [ ] **Step 4: Commit**

```bash
git add downstream-prototypes/
git commit -m "feat(shinymui): scaffold downstream-prototypes/ with shinymui placeholders"
```

---

## Task 2: Scaffold shinymui JS project

**Files:**
- Create: `downstream-prototypes/shinymui/js/package.json`
- Create: `downstream-prototypes/shinymui/js/tsconfig.json`
- Create: `downstream-prototypes/shinymui/js/vite.config.ts`
- Create: `downstream-prototypes/shinymui/js/.gitignore`

- [ ] **Step 1: Write `downstream-prototypes/shinymui/js/package.json`**

```json
{
  "name": "@shinymui/js",
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
    "@emotion/react": "^11.13.0",
    "@emotion/styled": "^11.13.0",
    "@mui/material": "^6.0.0",
    "@mui/x-data-grid": "^7.0.0"
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

- [ ] **Step 2: Write `downstream-prototypes/shinymui/js/tsconfig.json`**

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

- [ ] **Step 3: Write `downstream-prototypes/shinymui/js/vite.config.ts`**

The critical convention from RFC §4.1: React must be externalized to `window.shinyreact.React`. Rollup writes `globals` directly into the IIFE.

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
      name: "shinymui",
      formats: ["iife"],
      fileName: () => "shinymui.js",
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
        assetFileNames: "shinymui.[ext]",
      },
    },
  },
});
```

- [ ] **Step 4: Write `downstream-prototypes/shinymui/js/.gitignore`**

```
node_modules/
```

Note: `dist/` is committed per the same convention `shinyreact` uses (CLAUDE.md §"Built assets").

- [ ] **Step 5: Install dependencies**

```bash
cd downstream-prototypes/shinymui/js && npm install
```

Expected: completes without errors. `node_modules/` populated.

- [ ] **Step 6: Commit**

```bash
git add downstream-prototypes/shinymui/js/package.json \
        downstream-prototypes/shinymui/js/tsconfig.json \
        downstream-prototypes/shinymui/js/vite.config.ts \
        downstream-prototypes/shinymui/js/.gitignore \
        downstream-prototypes/shinymui/js/package-lock.json
git commit -m "feat(shinymui): scaffold JS project with Vite IIFE config externalizing React"
```

---

## Task 3: Empty JS entry + verify build

This task establishes the registration call without any components yet, proving the IIFE bundles, externalizes React correctly, and the convention from RFC §4.1 / §4.2 works end-to-end.

**Files:**
- Create: `downstream-prototypes/shinymui/js/src/index.ts`
- Create: `downstream-prototypes/shinymui/js/dist/shinymui.js` (build output)

- [ ] **Step 1: Write a local types module**

To avoid brittle cross-project imports (the shinyreact types are not published to npm yet), copy the minimum needed type shape locally. Create `downstream-prototypes/shinymui/js/src/types.ts`:

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
```

- [ ] **Step 2: Write empty entry `downstream-prototypes/shinymui/js/src/index.ts`**

```ts
import type { ComponentRegistry } from "./types";

// Components will be added one per task; registry starts empty.
const registry: ComponentRegistry = {};

// Catalog is reserved for future validation in shinyreact (currently unused).
const catalog = { name: "shinymui", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
```

Note: `window.shinyreact` is not declared here — TypeScript will complain. Fix in the next step.

- [ ] **Step 3: Add a global declaration for `window.shinyreact`**

Append to `downstream-prototypes/shinymui/js/src/types.ts`:

```ts
declare global {
  interface Window {
    shinyreact: {
      registerComponents: (
        catalog: unknown,
        registry: ComponentRegistry,
      ) => void;
      useShinyInput: <T>(
        id: string,
        defaultValue: T,
        options?: { debounceMs?: number; priority?: "immediate" | "deferred" | "event" },
      ) => [T, (value: T) => void];
      useShinyOutputValue: <T>(id: string, defaultValue?: T) => T;
      // Other hooks exist (useSetShinyInput, useShinyMessageHandler, ...) but
      // are not used by the prototype; add them as needed.
      React: typeof import("react");
      ReactDOM: unknown;
    };
  }
}

export {};
```

- [ ] **Step 4: Build the bundle**

```bash
cd downstream-prototypes/shinymui/js && npm run build
```

Expected: writes `dist/shinymui.js`. Inspect it briefly with `head -50 dist/shinymui.js` and confirm:
- It is an IIFE (starts with `(function(){`).
- It references `window.shinyreact.React` somewhere (search: `grep "window.shinyreact" dist/shinymui.js`).
- It calls `registerComponents` with the catalog object.

- [ ] **Step 5: Run the lint check**

```bash
cd downstream-prototypes/shinymui/js && npm run lint
```

Expected: passes with no errors.

- [ ] **Step 6: Commit**

```bash
git add downstream-prototypes/shinymui/js/src/types.ts \
        downstream-prototypes/shinymui/js/src/index.ts \
        downstream-prototypes/shinymui/js/dist/
git commit -m "feat(shinymui): empty JS entry that registers an empty catalog"
```

---

## Task 4: Scaffold shinymui Python package

**Files:**
- Create: `downstream-prototypes/shinymui/pkg-py/pyproject.toml`
- Create: `downstream-prototypes/shinymui/pkg-py/src/shinymui/__init__.py`
- Create: `downstream-prototypes/shinymui/pkg-py/src/shinymui/_dep.py`
- Create: `downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py`
- Create: `downstream-prototypes/shinymui/pkg-py/src/shinymui/www/.gitkeep`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "shinymui"
version = "0.0.0-prototype"
description = "Prototype helper package exposing MUI to shinyreact"
requires-python = ">=3.10"
dependencies = [
    "shiny>=1.0.0",
    "htmltools>=0.5.0",
    "shinyreact",
]

[tool.hatch.build.targets.wheel]
packages = ["src/shinymui"]

[tool.hatch.build.targets.wheel.force-include]
"src/shinymui/www/shinymui.js" = "shinymui/www/shinymui.js"
```

- [ ] **Step 2: Write `src/shinymui/_dep.py`**

```python
from pathlib import Path

from htmltools import HTMLDependency

_www_dir = Path(__file__).parent / "www"


def dep() -> HTMLDependency:
    """HTMLDependency for the shinymui JS bundle.

    Versioned by mtime of the bundled JS file so browsers re-fetch when the
    bundle is rebuilt during development. A real package would pin to its
    release version.
    """
    bundle = _www_dir / "shinymui.js"
    version = str(int(bundle.stat().st_mtime)) if bundle.exists() else "0"
    return HTMLDependency(
        name="shinymui",
        version=version,
        source={"subdir": str(_www_dir)},
        script={"src": "shinymui.js", "defer": ""},
    )
```

- [ ] **Step 3: Write empty `src/shinymui/_components.py`**

```python
"""Python factory functions for MUI components.

Each factory returns a ``shinyreact.Node`` with a ``mui:``-namespaced type
string. Components are added one per task.
"""

# Factories added in subsequent tasks.
```

- [ ] **Step 4: Write `src/shinymui/__init__.py`**

```python
from ._dep import dep

__all__ = ["dep"]
```

- [ ] **Step 5: Create `src/shinymui/www/.gitkeep`** so the directory survives `git add`.

```bash
touch downstream-prototypes/shinymui/pkg-py/src/shinymui/www/.gitkeep
```

- [ ] **Step 6: Copy the built JS bundle into `www/`**

```bash
cp downstream-prototypes/shinymui/js/dist/shinymui.js \
   downstream-prototypes/shinymui/pkg-py/src/shinymui/www/shinymui.js
```

- [ ] **Step 7: Install the package and confirm `dep()` works**

```bash
uv pip install -e downstream-prototypes/shinymui/pkg-py
uv run python -c "import shinymui; d = shinymui.dep(); print(d.name, d.version)"
```

Expected: prints `shinymui <numeric-version>` where version is the mtime.

- [ ] **Step 8: Commit**

```bash
git add downstream-prototypes/shinymui/pkg-py/
git commit -m "feat(shinymui): Python package with _dep helper, empty factories module"
```

---

## Task 5: Smoke-test example app with empty registry

The point of this task: prove the JS bundle loads, `mui:` namespace is reachable, and Shiny + shinyreact + shinymui plumb together — *before* adding any components. Catching plumbing bugs against zero-component noise is cheaper than untangling them after 5 components exist.

**Files:**
- Create: `downstream-prototypes/shinymui/example/app.py`

- [ ] **Step 1: Write `example/app.py`**

```python
"""shinymui prototype example app.

Mounts each MUI component as it is added in subsequent tasks. Starts as
plumbing-only: renders a static heading to confirm the bundle loads.
"""

import shinymui
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[shinymui.dep()])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        return shinyreact.Node(
            type="div",
            props={"style": {"padding": "16px", "fontFamily": "sans-serif"}},
            children=[
                shinyreact.Node(
                    type="h1",
                    props={},
                    children=[shinyreact.Node(type="span", props={"children": "shinymui prototype"})],
                ),
                shinyreact.Node(
                    type="p",
                    props={"children": "Plumbing test. Components added in following tasks."},
                ),
            ],
        )


app = App(app_ui, server)
```

Note: this uses intrinsic HTML tags (`div`, `h1`, `p`) which are rendered directly by `shinyreact`'s renderer (no registration needed). The `mui:` registry is exercised once Task 6 lands.

- [ ] **Step 2: Run the example app**

```bash
uv run shiny run --reload downstream-prototypes/shinymui/example/app.py
```

Open `http://localhost:8000` in a browser.

Expected:
- Heading "shinymui prototype" and paragraph render.
- No JS errors in the browser console.
- Network panel shows `shinymui-<version>/shinymui.js` was loaded with a 200.
- Run `JSON.stringify(Object.keys(window.shinyreact))` in the console — should include `registerComponents`, `React`, etc. (the bundle does not add new keys to `window.shinyreact`; it consumes the API.)

Stop the dev server (`Ctrl+C`).

- [ ] **Step 3: Commit**

```bash
git add downstream-prototypes/shinymui/example/app.py
git commit -m "feat(shinymui): example app plumbing test (no components yet)"
```

---

## Task 6: Button component (basic factory + slot API + controlled-event input)

**Why first:** Button hits three RFC open questions at once — slot API (`startIcon`/`endIcon`), controlled-event input (`useShinyInput`), and basic factory. Resolving these in the first component sets the pattern for the next four.

**Files:**
- Create: `downstream-prototypes/shinymui/js/src/components/Button.tsx`
- Modify: `downstream-prototypes/shinymui/js/src/index.ts`
- Create: `downstream-prototypes/shinymui/pkg-py/tests/test_factories.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/__init__.py`
- Modify: `downstream-prototypes/shinymui/example/app.py`

- [ ] **Step 1: Write the failing Python factory test**

```python
# downstream-prototypes/shinymui/pkg-py/tests/test_factories.py
import shinymui


def test_button_factory_basic():
    node = shinymui.button("Click me", input_id="my_btn")
    assert node.type == "mui:Button"
    assert node.props["label"] == "Click me"
    assert node.props["input_id"] == "my_btn"
    assert node.props["variant"] == "contained"  # default


def test_button_factory_slot_icons():
    node = shinymui.button("Save", input_id="b", start_icon="Save", end_icon="Send")
    assert node.props["start_icon"] == "Save"
    assert node.props["end_icon"] == "Send"
```

- [ ] **Step 2: Run the test — expect FAIL**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

Expected: FAIL with `AttributeError: module 'shinymui' has no attribute 'button'`.

- [ ] **Step 3: Implement the Python factory**

Append to `downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py`:

```python
from typing import Literal

import shinyreact


def button(
    label: str,
    *,
    input_id: str,
    variant: Literal["text", "contained", "outlined"] = "contained",
    color: Literal["primary", "secondary", "success", "error"] = "primary",
    start_icon: str | None = None,
    end_icon: str | None = None,
) -> shinyreact.Node:
    """Render an MUI Button.

    ``input_id`` is required — clicks increment an action-button counter sent
    to ``input.<input_id>()``, following the shinyreact action-button pattern.

    ``start_icon`` and ``end_icon`` are MUI icon names (e.g. ``"Save"``,
    ``"Send"``); the JS component looks them up in ``@mui/icons-material``.
    """
    props: dict[str, object] = {
        "label": label,
        "input_id": input_id,
        "variant": variant,
        "color": color,
    }
    if start_icon is not None:
        props["start_icon"] = start_icon
    if end_icon is not None:
        props["end_icon"] = end_icon
    return shinyreact.Node(type="mui:Button", props=props)
```

Update `__init__.py`:

```python
from ._components import button
from ._dep import dep

__all__ = ["button", "dep"]
```

- [ ] **Step 4: Run the test — expect PASS**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Implement the JS component**

Create `downstream-prototypes/shinymui/js/src/components/Button.tsx`. Note that registered components receive `{ element, children }` per `RegisteredComponentProps` and must read their own props from `element.props`.

```tsx
import React from "react";
import { Button as MuiButton } from "@mui/material";
import * as MuiIcons from "@mui/icons-material";
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

type IconName = keyof typeof MuiIcons;

function renderIcon(name: unknown): React.ReactNode {
  if (typeof name !== "string") return undefined;
  const Icon = MuiIcons[name as IconName];
  if (!Icon) {
    console.warn(`[shinymui] unknown icon "${name}"`);
    return undefined;
  }
  return React.createElement(Icon as React.ComponentType);
}

export function Button({ element }: RegisteredComponentProps) {
  const {
    label,
    input_id,
    variant,
    color,
    start_icon,
    end_icon,
  } = element.props as {
    label: string;
    input_id: string;
    variant?: "text" | "contained" | "outlined";
    color?: "primary" | "secondary" | "success" | "error";
    start_icon?: string;
    end_icon?: string;
  };

  const [count, setCount] = useShinyInput<number>(input_id, 0, {
    debounceMs: 0,
    priority: "event",
  });

  return (
    <MuiButton
      variant={variant ?? "contained"}
      color={color ?? "primary"}
      startIcon={renderIcon(start_icon)}
      endIcon={renderIcon(end_icon)}
      onClick={() => setCount((count ?? 0) + 1)}
    >
      {label}
    </MuiButton>
  );
}
```

Note the convention discovered here for RFC §5: **slot props are passed as strings (icon names) and the JS component maps them**. This avoids needing the renderer to walk Element-valued props. Document this in Task 12.

- [ ] **Step 6: Register the component**

Update `downstream-prototypes/shinymui/js/src/index.ts`:

```ts
import type { ComponentRegistry } from "./types";
import { Button } from "./components/Button";

const registry: ComponentRegistry = {
  "mui:Button": Button,
};

const catalog = { name: "shinymui", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
```

- [ ] **Step 7: Add `@mui/icons-material` to `js/package.json`**

```bash
cd downstream-prototypes/shinymui/js && npm install @mui/icons-material
```

Verify the dependency appears in `package.json`.

- [ ] **Step 8: Build the bundle and copy to pkg-py**

```bash
cd downstream-prototypes/shinymui/js && npm run build
cp dist/shinymui.js ../pkg-py/src/shinymui/www/shinymui.js
```

Inspect bundle size: `ls -lh dist/shinymui.js`. Note the size for the RFC findings (`@mui/icons-material` is large — expect 1-2 MB minified). Document if it's surprising.

- [ ] **Step 9: Wire Button into the example app**

Replace `downstream-prototypes/shinymui/example/app.py` with:

```python
import shinymui
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[shinymui.dep()])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        clicks = input.btn1() or 0
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
                shinyreact.Node(type="h1", props={"children": "shinymui prototype"}),
                shinymui.button("Save with icon", input_id="btn1", start_icon="Save"),
                shinyreact.Node(
                    type="div",
                    props={"children": f"Button btn1 has been clicked {clicks} times."},
                ),
            ],
        )


app = App(app_ui, server)
```

The outer `main` is reactive on `input.btn1()`, so the click-count text re-renders on each click. This exercises both the JS `useShinyInput` event-input wiring and the server-side reactivity.

- [ ] **Step 10: Manual verification**

```bash
uv run shiny run --reload downstream-prototypes/shinymui/example/app.py
```

In a browser at `http://localhost:8000`:
- Confirm an MUI button labeled "Save with icon" appears with a Save icon on the left.
- Click it 3 times. The text "Button btn1 has been clicked 3 times." should appear and increment.
- No JS errors in the console.
- Stop the dev server.

- [ ] **Step 11: Commit**

```bash
git add downstream-prototypes/shinymui/js/src/components/Button.tsx \
        downstream-prototypes/shinymui/js/src/index.ts \
        downstream-prototypes/shinymui/js/package.json \
        downstream-prototypes/shinymui/js/package-lock.json \
        downstream-prototypes/shinymui/js/dist/ \
        downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py \
        downstream-prototypes/shinymui/pkg-py/src/shinymui/__init__.py \
        downstream-prototypes/shinymui/pkg-py/src/shinymui/www/shinymui.js \
        downstream-prototypes/shinymui/pkg-py/tests/test_factories.py \
        downstream-prototypes/shinymui/example/app.py
git commit -m "feat(shinymui): Button component (action-button input + icon slots)"
```

---

## Task 7: TextField component (controlled string input)

**Files:**
- Create: `downstream-prototypes/shinymui/js/src/components/TextField.tsx`
- Modify: `downstream-prototypes/shinymui/js/src/index.ts`
- Modify: `downstream-prototypes/shinymui/pkg-py/tests/test_factories.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/__init__.py`
- Modify: `downstream-prototypes/shinymui/example/app.py`

- [ ] **Step 1: Add failing factory test**

Append to `tests/test_factories.py`:

```python
def test_text_field_factory():
    node = shinymui.text_field(
        input_id="name",
        label="Your name",
        default_value="Anonymous",
        helper_text="Required",
    )
    assert node.type == "mui:TextField"
    assert node.props["input_id"] == "name"
    assert node.props["label"] == "Your name"
    assert node.props["default_value"] == "Anonymous"
    assert node.props["helper_text"] == "Required"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py::test_text_field_factory -v
```

Expected: FAIL with `AttributeError: module 'shinymui' has no attribute 'text_field'`.

- [ ] **Step 3: Implement Python factory**

Append to `_components.py`:

```python
def text_field(
    *,
    input_id: str,
    label: str = "",
    default_value: str = "",
    placeholder: str = "",
    helper_text: str = "",
    debounce_ms: int = 250,
) -> shinyreact.Node:
    """Render an MUI TextField bound to a Shiny input."""
    return shinyreact.Node(
        type="mui:TextField",
        props={
            "input_id": input_id,
            "label": label,
            "default_value": default_value,
            "placeholder": placeholder,
            "helper_text": helper_text,
            "debounce_ms": debounce_ms,
        },
    )
```

Update `__init__.py`:

```python
from ._components import button, text_field
from ._dep import dep

__all__ = ["button", "dep", "text_field"]
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

Expected: all factory tests pass.

- [ ] **Step 5: Implement JS component `js/src/components/TextField.tsx`**

```tsx
import React from "react";
import { TextField as MuiTextField } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

export function TextField({ element }: RegisteredComponentProps) {
  const {
    input_id,
    label,
    default_value,
    placeholder,
    helper_text,
    debounce_ms,
  } = element.props as {
    input_id: string;
    label?: string;
    default_value?: string;
    placeholder?: string;
    helper_text?: string;
    debounce_ms?: number;
  };

  const [value, setValue] = useShinyInput<string>(input_id, default_value ?? "", {
    debounceMs: debounce_ms ?? 250,
  });

  return (
    <MuiTextField
      label={label}
      placeholder={placeholder}
      helperText={helper_text}
      value={value ?? ""}
      onChange={(e) => setValue(e.target.value)}
      fullWidth
    />
  );
}
```

- [ ] **Step 6: Register the component**

Update `js/src/index.ts`:

```ts
import type { ComponentRegistry } from "./types";
import { Button } from "./components/Button";
import { TextField } from "./components/TextField";

const registry: ComponentRegistry = {
  "mui:Button": Button,
  "mui:TextField": TextField,
};

const catalog = { name: "shinymui", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
```

- [ ] **Step 7: Build and copy**

```bash
cd downstream-prototypes/shinymui/js && npm run build
cp dist/shinymui.js ../pkg-py/src/shinymui/www/shinymui.js
```

- [ ] **Step 8: Wire into example app**

Edit `example/app.py`'s `main` reactive output to add the TextField and an echo:

```python
@shinyreact.reactive_output
def main():
    name = input.name() or ""
    return shinyreact.Node(
        type="div",
        props={"style": {"padding": "16px", "fontFamily": "sans-serif", "display": "flex", "flexDirection": "column", "gap": "16px", "maxWidth": "600px"}},
        children=[
            shinyreact.Node(type="h1", props={"children": "shinymui prototype"}),
            shinymui.button("Save with icon", input_id="btn1", start_icon="Save"),
            shinyreact.Node(type="div", props={"children": f"Button btn1 clicks: {input.btn1() or 0}"}),
            shinymui.text_field(input_id="name", label="Your name", default_value="World"),
            shinyreact.Node(type="div", props={"children": f"Hello, {name}!"}),
        ],
    )
```

- [ ] **Step 9: Manual verification**

```bash
uv run shiny run --reload downstream-prototypes/shinymui/example/app.py
```

Verify:
- MUI TextField appears with label "Your name" and value "World".
- Typing in it updates "Hello, …!" after ~250ms debounce.
- No console errors.

Stop the dev server.

- [ ] **Step 10: Commit**

```bash
git add downstream-prototypes/shinymui/
git commit -m "feat(shinymui): TextField component (controlled string input)"
```

---

## Task 8: Slider component (controlled numeric input)

**Files:**
- Create: `downstream-prototypes/shinymui/js/src/components/Slider.tsx`
- Modify: `downstream-prototypes/shinymui/js/src/index.ts`
- Modify: `downstream-prototypes/shinymui/pkg-py/tests/test_factories.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/__init__.py`
- Modify: `downstream-prototypes/shinymui/example/app.py`

- [ ] **Step 1: Add failing factory test**

Append to `tests/test_factories.py`:

```python
def test_slider_factory():
    node = shinymui.slider(
        input_id="age",
        label="Age",
        default_value=25,
        min=0,
        max=100,
        step=1,
    )
    assert node.type == "mui:Slider"
    assert node.props["input_id"] == "age"
    assert node.props["default_value"] == 25
    assert node.props["min"] == 0
    assert node.props["max"] == 100
    assert node.props["step"] == 1
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py::test_slider_factory -v
```

- [ ] **Step 3: Implement Python factory**

Append to `_components.py`:

```python
def slider(
    *,
    input_id: str,
    label: str = "",
    default_value: float = 0,
    min: float = 0,
    max: float = 100,
    step: float = 1,
    debounce_ms: int = 100,
) -> shinyreact.Node:
    """Render an MUI Slider bound to a Shiny input."""
    return shinyreact.Node(
        type="mui:Slider",
        props={
            "input_id": input_id,
            "label": label,
            "default_value": default_value,
            "min": min,
            "max": max,
            "step": step,
            "debounce_ms": debounce_ms,
        },
    )
```

Update `__init__.py`:

```python
from ._components import button, slider, text_field
from ._dep import dep

__all__ = ["button", "dep", "slider", "text_field"]
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

- [ ] **Step 5: Implement JS component `js/src/components/Slider.tsx`**

```tsx
import React from "react";
import { Slider as MuiSlider, Typography, Box } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

export function Slider({ element }: RegisteredComponentProps) {
  const {
    input_id,
    label,
    default_value,
    min,
    max,
    step,
    debounce_ms,
  } = element.props as {
    input_id: string;
    label?: string;
    default_value?: number;
    min?: number;
    max?: number;
    step?: number;
    debounce_ms?: number;
  };

  const [value, setValue] = useShinyInput<number>(input_id, default_value ?? 0, {
    debounceMs: debounce_ms ?? 100,
  });

  return (
    <Box>
      {label && <Typography gutterBottom>{label}: {value}</Typography>}
      <MuiSlider
        value={value ?? 0}
        onChange={(_, v) => setValue(typeof v === "number" ? v : v[0])}
        min={min ?? 0}
        max={max ?? 100}
        step={step ?? 1}
        valueLabelDisplay="auto"
      />
    </Box>
  );
}
```

- [ ] **Step 6: Register**

Update `js/src/index.ts` registry to include `"mui:Slider": Slider` (and add the import).

- [ ] **Step 7: Build and copy**

```bash
cd downstream-prototypes/shinymui/js && npm run build
cp dist/shinymui.js ../pkg-py/src/shinymui/www/shinymui.js
```

- [ ] **Step 8: Wire into example app**

Add a slider section before the existing children:

```python
shinymui.slider(input_id="age", label="Age", default_value=25, min=0, max=100),
shinyreact.Node(type="div", props={"children": f"Age value: {input.age() or 0}"}),
```

- [ ] **Step 9: Manual verification**

Run the example, drag the slider, confirm the "Age value: N" text updates with ~100ms debounce. No console errors.

- [ ] **Step 10: Commit**

```bash
git add downstream-prototypes/shinymui/
git commit -m "feat(shinymui): Slider component (controlled numeric input)"
```

---

## Task 9: Card component (children / composition)

**Why this matters:** Card is the first component with `children`. It validates that the renderer's child-walking works for namespaced components (it does — components are looked up by `type` string regardless of namespace).

**Files:**
- Create: `downstream-prototypes/shinymui/js/src/components/Card.tsx`
- Modify: `downstream-prototypes/shinymui/js/src/index.ts`
- Modify: `downstream-prototypes/shinymui/pkg-py/tests/test_factories.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/__init__.py`
- Modify: `downstream-prototypes/shinymui/example/app.py`

- [ ] **Step 1: Add failing factory test**

Append to `tests/test_factories.py`:

```python
def test_card_factory_with_children():
    child = shinymui.button("X", input_id="x")
    node = shinymui.card("My title", child)
    assert node.type == "mui:Card"
    assert node.props["title"] == "My title"
    assert len(node.children) == 1
    assert node.children[0].type == "mui:Button"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py::test_card_factory_with_children -v
```

- [ ] **Step 3: Implement Python factory**

Append to `_components.py`:

```python
def card(
    title: str | None = None,
    *children: shinyreact.Node,
) -> shinyreact.Node:
    """Render an MUI Card. Children become the card body."""
    props: dict[str, object] = {}
    if title is not None:
        props["title"] = title
    return shinyreact.Node(type="mui:Card", props=props, children=list(children))
```

Update `__init__.py`:

```python
from ._components import button, card, slider, text_field
from ._dep import dep

__all__ = ["button", "card", "dep", "slider", "text_field"]
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

- [ ] **Step 5: Implement JS component `js/src/components/Card.tsx`**

```tsx
import React from "react";
import { Card as MuiCard, CardContent, CardHeader } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

export function Card({ element, children }: RegisteredComponentProps) {
  const { title } = element.props as { title?: string };
  return (
    <MuiCard variant="outlined">
      {title && <CardHeader title={title} />}
      <CardContent>{children}</CardContent>
    </MuiCard>
  );
}
```

- [ ] **Step 6: Register**

Update `js/src/index.ts` registry: `"mui:Card": Card`.

- [ ] **Step 7: Build and copy**

```bash
cd downstream-prototypes/shinymui/js && npm run build
cp dist/shinymui.js ../pkg-py/src/shinymui/www/shinymui.js
```

- [ ] **Step 8: Wire into example app**

Wrap the existing controls in a Card:

```python
shinymui.card(
    "Demo Card",
    shinymui.text_field(input_id="name", label="Your name", default_value="World"),
    shinymui.slider(input_id="age", label="Age", default_value=25, min=0, max=100),
    shinymui.button("Save", input_id="btn1", start_icon="Save"),
),
```

(Adjust the surrounding `main` reactive_output to render the Card and any echo text it needs.)

- [ ] **Step 9: Manual verification**

Run the example, confirm:
- MUI Card with "Demo Card" header.
- TextField, Slider, Button all render inside the Card.
- All three controls still send values to the server and the echo text updates.

- [ ] **Step 10: Commit**

```bash
git add downstream-prototypes/shinymui/
git commit -m "feat(shinymui): Card component (children composition)"
```

---

## Task 10: DataGrid component (specialized, server-pushed data)

**Why this is the stress test:** DataGrid has a large prop surface and consumes server-pushed data via `useShinyOutputValue` rather than a controlled input. This exercises the second output paradigm from CLAUDE.md ("`@reactive_output` + `useShinyOutputValue`") and the per-category-5 question (huge APIs).

**Files:**
- Create: `downstream-prototypes/shinymui/js/src/components/DataGrid.tsx`
- Modify: `downstream-prototypes/shinymui/js/src/index.ts`
- Modify: `downstream-prototypes/shinymui/pkg-py/tests/test_factories.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/_components.py`
- Modify: `downstream-prototypes/shinymui/pkg-py/src/shinymui/__init__.py`
- Modify: `downstream-prototypes/shinymui/example/app.py`

- [ ] **Step 1: Add failing factory test**

Append to `tests/test_factories.py`:

```python
def test_data_grid_factory():
    node = shinymui.data_grid(output_id="grid1", height=400)
    assert node.type == "mui:DataGrid"
    assert node.props["output_id"] == "grid1"
    assert node.props["height"] == 400
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py::test_data_grid_factory -v
```

- [ ] **Step 3: Implement Python factory**

Append to `_components.py`:

```python
def data_grid(
    *,
    output_id: str,
    height: int = 400,
) -> shinyreact.Node:
    """Render an MUI DataGrid consuming an output via useShinyOutputValue.

    The server-side renderer for ``output_id`` must return a dict shaped
    ``{"rows": [...], "columns": [{"field": str, "headerName": str, ...}]}``.
    All other DataGrid props are deferred — the prototype exposes only the
    minimum needed to validate the specialized-category pattern.
    """
    return shinyreact.Node(
        type="mui:DataGrid",
        props={"output_id": output_id, "height": height},
    )
```

Update `__init__.py`:

```python
from ._components import button, card, data_grid, slider, text_field
from ._dep import dep

__all__ = ["button", "card", "data_grid", "dep", "slider", "text_field"]
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

- [ ] **Step 5: Implement JS component `js/src/components/DataGrid.tsx`**

```tsx
import React from "react";
import { DataGrid as MuiDataGrid, type GridColDef } from "@mui/x-data-grid";
import { Box } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

const { useShinyOutputValue } = window.shinyreact;

interface GridPayload {
  rows: Array<Record<string, unknown> & { id: string | number }>;
  columns: GridColDef[];
}

export function DataGrid({ element }: RegisteredComponentProps) {
  const { output_id, height } = element.props as {
    output_id: string;
    height?: number;
  };

  const payload = useShinyOutputValue<GridPayload | null>(output_id, null);

  if (!payload) {
    return <Box sx={{ height: height ?? 400 }}>Loading…</Box>;
  }

  return (
    <Box sx={{ height: height ?? 400, width: "100%" }}>
      <MuiDataGrid rows={payload.rows} columns={payload.columns} />
    </Box>
  );
}
```

- [ ] **Step 6: Register**

Update `js/src/index.ts` registry: `"mui:DataGrid": DataGrid`.

- [ ] **Step 7: Build and copy**

```bash
cd downstream-prototypes/shinymui/js && npm run build
cp dist/shinymui.js ../pkg-py/src/shinymui/www/shinymui.js
```

Note the new bundle size — DataGrid adds substantial weight. Record the delta for RFC findings.

- [ ] **Step 8: Wire into example app**

Add the grid and a server-side `reactive_output` that produces filtered rows from the existing inputs. Inside `server()`:

```python
SAMPLE_ROWS = [
    {"id": 1, "name": "Alice", "age": 30, "score": 85},
    {"id": 2, "name": "Bob", "age": 25, "score": 92},
    {"id": 3, "name": "Carol", "age": 42, "score": 78},
    {"id": 4, "name": "Dave", "age": 35, "score": 88},
    {"id": 5, "name": "Eve", "age": 28, "score": 95},
]

@shinyreact.reactive_output
def grid1():
    threshold = input.age() or 0
    rows = [r for r in SAMPLE_ROWS if r["age"] >= threshold]
    return {
        "rows": rows,
        "columns": [
            {"field": "name", "headerName": "Name", "width": 150},
            {"field": "age", "headerName": "Age", "width": 100},
            {"field": "score", "headerName": "Score", "width": 100},
        ],
    }
```

Add `shinymui.data_grid(output_id="grid1", height=300)` to the Card body or below it.

- [ ] **Step 9: Manual verification**

Run the example, confirm:
- DataGrid renders with name/age/score columns and 5 rows initially.
- Dragging the age slider filters rows in real time (rows where age >= slider value).
- The slider's controlled input and the grid's pushed output both work in the same app.
- No console errors.

- [ ] **Step 10: Commit**

```bash
git add downstream-prototypes/shinymui/
git commit -m "feat(shinymui): DataGrid component (specialized, server-pushed data)"
```

---

## Task 11: Composite example app polish + manual smoke-test checklist

By now the example app has grown organically across tasks. This task tidies it into a clean reference and runs a final end-to-end smoke test.

**Files:**
- Modify: `downstream-prototypes/shinymui/example/app.py`

- [ ] **Step 1: Restructure the example into a coherent layout**

Replace `example/app.py` with:

```python
"""shinymui prototype example app.

Exercises all 5 components in one page. This is the integration test for the
prototype — if every interaction below works, the conventions hold.
"""

import shinymui
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[shinymui.dep()])


SAMPLE_ROWS = [
    {"id": 1, "name": "Alice", "age": 30, "score": 85},
    {"id": 2, "name": "Bob", "age": 25, "score": 92},
    {"id": 3, "name": "Carol", "age": 42, "score": 78},
    {"id": 4, "name": "Dave", "age": 35, "score": 88},
    {"id": 5, "name": "Eve", "age": 28, "score": 95},
]


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        name = input.name() or "World"
        age = input.age() or 0
        clicks = input.btn1() or 0
        return shinyreact.Node(
            type="div",
            props={
                "style": {
                    "padding": "16px",
                    "fontFamily": "sans-serif",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "16px",
                    "maxWidth": "800px",
                    "margin": "0 auto",
                }
            },
            children=[
                shinyreact.Node(type="h1", props={"children": "shinymui prototype"}),
                shinymui.card(
                    "Controls",
                    shinymui.text_field(
                        input_id="name", label="Name", default_value="World"
                    ),
                    shinymui.slider(
                        input_id="age",
                        label="Min age filter",
                        default_value=25,
                        min=0,
                        max=50,
                    ),
                    shinymui.button(
                        "Click me", input_id="btn1", start_icon="TouchApp"
                    ),
                    shinyreact.Node(
                        type="div",
                        props={
                            "children": f"Hello, {name}! Age filter: {age}. Clicks: {clicks}."
                        },
                    ),
                ),
                shinymui.card(
                    "Filtered data (DataGrid)",
                    shinymui.data_grid(output_id="grid1", height=300),
                ),
            ],
        )

    @shinyreact.reactive_output
    def grid1():
        threshold = input.age() or 0
        rows = [r for r in SAMPLE_ROWS if r["age"] >= threshold]
        return {
            "rows": rows,
            "columns": [
                {"field": "name", "headerName": "Name", "width": 150},
                {"field": "age", "headerName": "Age", "width": 100},
                {"field": "score", "headerName": "Score", "width": 100},
            ],
        }


app = App(app_ui, server)
```

- [ ] **Step 2: Run the full smoke-test checklist**

```bash
uv run shiny run --reload downstream-prototypes/shinymui/example/app.py
```

In the browser, verify ALL of the following before continuing:

- [ ] Page renders without JS errors.
- [ ] Two Cards visible: "Controls" and "Filtered data (DataGrid)".
- [ ] TextField: typing changes "Hello, …!" after debounce.
- [ ] Slider: dragging changes "Age filter: N" in real time, and the DataGrid filters rows accordingly.
- [ ] Button: clicking with `TouchApp` icon increments "Clicks: N".
- [ ] DataGrid: 5 rows shown initially; filters as slider moves.
- [ ] Browser network tab: `shinymui.js` loaded with a 200 status; version reflects file mtime.
- [ ] Browser console: no warnings about duplicate React or duplicate component registration.

If any check fails, fix and re-verify before committing.

- [ ] **Step 3: Run the full factory test suite once more**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 4: Commit**

```bash
git add downstream-prototypes/shinymui/example/app.py
git commit -m "feat(shinymui): polish composite example app exercising all 5 components"
```

---

## Task 12: Fold prototype findings back into RFC §5

The RFC explicitly says open questions get answered by the prototype. This task closes the loop.

**Files:**
- Modify: `docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md`

- [ ] **Step 1: Reread the RFC's open-questions section**

```bash
sed -n '/^## Open questions explored via prototype/,/^## MUI prototype/p' \
  docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md
```

- [ ] **Step 2: For each open question, append a "Prototype finding" paragraph**

Under each `### Theming`, `### Slot / compound-component APIs`, `### Controlled inputs vs server-pushed values`, and `### Per-category divergences` subsection, append a short paragraph titled "**Prototype finding:**" capturing what the MUI prototype actually did. Concrete content to write:

- **Theming finding** — The prototype did NOT integrate theming. Each MUI component renders with default theme. Document this as deferred until a real `shinymui` package; flag that MUI's `ThemeProvider` would need to wrap the entire React tree inside `ShinyreactRenderer`, which is a shinyreact-level concern (likely a per-page-react hook or a "provider chain" registration mechanism). Add a follow-up open question: "Where do `Provider`-style wrappers register in shinyreact?"

- **Slot / compound-component APIs finding** — Slot props for MUI Buttons (`startIcon`, `endIcon`) were passed as icon-name strings (`"Save"`) and resolved client-side via `@mui/icons-material`. This avoided the alternative of having the renderer walk Element-valued props. The convention generalizes: prefer string-keyed slot lookups when the library exposes a finite catalog (icons, variants); fall back to allowing `Element` references in props when the slot can be arbitrary user-defined React content. Note that the latter pattern was NOT exercised in the prototype — flag as still open.

- **Controlled inputs vs server-pushed values finding** — Three patterns surfaced cleanly: action-button events (`useShinyInput` with `priority: "event"` and `debounceMs: 0`), value-tracking inputs (TextField, Slider — `useShinyInput` with library-appropriate `debounceMs`), and server-pushed outputs (DataGrid — `useShinyOutputValue`). The factory `input_id` / `output_id` naming convention reads clearly at the call site. Recommend codifying these three patterns as the contract.

- **Per-category divergences finding** — All five components fit the same shape (factory → `mui:` namespace → registered component reads `element.props`). DataGrid stretched but did not break the shape — its `output_id` plus a server-side payload shape is the per-prop-typing workaround mentioned in §4.3. Bundle size grew substantially with `@mui/x-data-grid` (record actual delta). Real-world specialized packages may want tree-shakable imports.

Each finding paragraph should be 3-6 sentences, concrete (no "TBD"), and reference specific tasks/components where helpful.

- [ ] **Step 3: Add a "Bundle size baseline" subsection under the MUI prototype section (§6)**

Append:

```markdown
### Bundle size baseline

The built `dist/shinymui.js` totalled <N> MB minified, broken down as:

- `@mui/material` core: ~<N> MB
- `@mui/icons-material` (icon lookup table): ~<N> MB
- `@mui/x-data-grid`: ~<N> MB
- shinymui component code: <<N> KB

Implications for real packages: tree-shakable imports matter (the prototype
imports `* as MuiIcons` for simplicity — a real package would import only the
icons it ships, or expose the icon catalog separately so the consumer's
bundler can tree-shake). Specialized-category packages with large data
components should consider lazy-loading the heavy parts behind dynamic
imports.
```

Fill in the actual numbers from `ls -lh downstream-prototypes/shinymui/js/dist/shinymui.js` and any breakdown you can get from `vite build --report` (optional — if not easy, just total + commentary).

- [ ] **Step 4: Update the "Acceptance criteria" subsection**

The RFC's last bullet asks for the MUI prototype to demonstrate one component per archetype. Verify each archetype is checked off:

- Basic factory: ✅ Button
- Controlled input: ✅ TextField, Slider
- Layout / children: ✅ Card
- Specialized (server-pushed, large prop surface): ✅ DataGrid

If satisfied, this RFC milestone is complete. Add a final line under acceptance criteria:

```markdown
**Status (2026-05-12):** First three criteria satisfied by `downstream-prototypes/shinymui/`. The scaffolding-skill criterion remains open and is the subject of the follow-up plan.
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md
git commit -m "docs(rfc): fold MUI prototype findings into helper-packages RFC §5/§6"
```

---

## Final verification

- [ ] **Step 1: Run all factory tests**

```bash
cd downstream-prototypes/shinymui/pkg-py && uv run pytest tests/test_factories.py -v
```

Expected: 6 tests pass (button basic, button slot icons, text_field, slider, card with children, data_grid).

- [ ] **Step 2: JS lint**

```bash
cd downstream-prototypes/shinymui/js && npm run lint
```

Expected: passes.

- [ ] **Step 3: One final manual smoke test of the example app**

```bash
uv run shiny run downstream-prototypes/shinymui/example/app.py
```

Walk through every checkbox in Task 11 Step 2 one more time. If anything regressed, fix and re-verify.

- [ ] **Step 4: Verify the host repo's tests still pass**

```bash
make py-check
```

Expected: passes. The prototype lives outside `pkg-py/` so should not break the main package's tests, but verify.

- [ ] **Step 5: Final commit (if any fixes were needed in Step 3)**

Otherwise, this plan is complete. The next plan is the `scaffold-shinyreact-helper` Claude skill, which templates from `downstream-prototypes/shinymui/` as its reference shape.
