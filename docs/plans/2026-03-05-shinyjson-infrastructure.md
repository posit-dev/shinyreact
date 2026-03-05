# shinyjson Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create the monorepo skeleton, JS IIFE bundle, and Python package for `shinyjson` — the infrastructure layer that downstream packages (e.g. `shinyshadcn`) build Shiny JSON-render components on top of.

**Architecture:** Phase 1 scaffolds the repo and builds a Vite IIFE bundle (`shinyjson.js`) that registers a Shiny output binding and exposes `window.shinyjson.registerComponents()`. Phase 2 creates the Python package with `shinyjson.ui()`, `@shinyjson.render`, and `shinyjson.Spec`, distributed with the JS assets via `HTMLDependency`.

**Tech Stack:** TypeScript 5, React 18, `@json-render/core`, `@json-render/react`, Vite 5 (JS); Python 3.11+, `shiny>=1.2.0`, `htmltools`, `uv`, `pytest`, `pyright`, `ruff` (Python)

---

## Phase 1: JS + Repo Infrastructure

---

### Task 1: Create Directory Skeleton

**Files:**
- Create: `js/src/`
- Create: `pkg-py/src/shinyjson/www/`
- Create: `pkg-py/tests/`
- Create: `pkg-r/R/`
- Create: `pkg-r/inst/lib/shiny/`

**Step 1: Create all directories and placeholder files**

```bash
mkdir -p js/src
mkdir -p pkg-py/src/shinyjson/www
mkdir -p pkg-py/tests
mkdir -p pkg-r/R
mkdir -p pkg-r/inst/lib/shiny

# Placeholder Python package init (required before uv sync)
touch pkg-py/src/shinyjson/__init__.py
touch pkg-py/tests/__init__.py

# Gitkeep for empty directories
touch pkg-py/src/shinyjson/www/.gitkeep
touch pkg-r/inst/lib/shiny/.gitkeep
```

**Step 2: Verify**

```bash
find . -not -path './.git/*' -not -path './docs/*' -not -path './node_modules/*' | sort
```

Expected: All directories and placeholder files listed.

**Step 3: Commit**

```bash
git add pkg-py/ pkg-r/ js/
git commit -m "chore: scaffold monorepo directory structure"
```

---

### Task 2: Root pyproject.toml + Python Environment

**Files:**
- Create: `pyproject.toml` (at repo root)

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "shinyjson"
version = "0.1.0"
description = "Shiny UI infrastructure for JSON-based component rendering"
requires-python = ">=3.11"
dependencies = [
    "shiny>=1.2.0",
    "htmltools>=0.6.0",
]

[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyjson"]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pyright>=1.1.0",
    "ruff>=0.6.0",
    "pytest-cov>=5.0.0",
]

[tool.pyright]
include = ["pkg-py/src/shinyjson"]
pythonVersion = "3.11"
typeCheckingMode = "basic"

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]
```

**Step 2: Install Python environment**

```bash
uv sync --all-extras --all-groups
```

Expected: uv resolves dependencies and installs into `.venv/`.

**Step 3: Verify install**

```bash
uv run python -c "import shinyjson; print('ok')"
```

Expected: prints `ok`.

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add Python package configuration"
```

---

### Task 3: JS package.json + tsconfig

**Files:**
- Create: `js/package.json`
- Create: `js/tsconfig.json`

**Step 1: Verify the npm packages exist**

```bash
npm view @json-render/core version
npm view @json-render/react version
```

Expected: Both print a version number. If either fails, check https://github.com/vercel-labs/json-render for the correct package names.

**Step 2: Create js/package.json**

```json
{
  "name": "@shinyjson/js",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "build": "vite build",
    "watch": "vite build --watch",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "@json-render/core": "latest",
    "@json-render/react": "latest",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

**Step 3: Create js/tsconfig.json**

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
    "strict": true
  },
  "include": ["src"]
}
```

**Step 4: Install JS dependencies**

```bash
cd js && npm install
```

Expected: `node_modules/` created, `package-lock.json` written.

**Step 5: Commit**

```bash
git add js/package.json js/tsconfig.json js/package-lock.json
git commit -m "chore: add JS package configuration and lockfile"
```

---

### Task 4: Vite Config + CSS Placeholder

**Files:**
- Create: `js/vite.config.ts`
- Create: `js/src/shinyjson.css`

**Step 1: Create js/vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: "src/index.ts",
      name: "shinyjson",
      formats: ["iife"],
      fileName: () => "shinyjson.js",
    },
    outDir: "dist",
    cssFileName: "shinyjson",
    rollupOptions: {
      // Bundle everything including React — no externals
    },
  },
});
```

**Step 2: Create js/src/shinyjson.css**

```css
/* shinyjson base styles — downstream packages provide component CSS */
```

**Step 3: Commit**

```bash
git add js/vite.config.ts js/src/shinyjson.css
git commit -m "chore: add Vite build configuration"
```

---

### Task 5: JS registry.ts

**Files:**
- Create: `js/src/registry.ts`

**Step 1: Create js/src/registry.ts**

```typescript
import type { ComponentRegistry } from "@json-render/react";

// Accumulated component registry — populated by downstream packages calling
// window.shinyjson.registerComponents() at page load.
let _registry: ComponentRegistry = {};

/**
 * Register components from a downstream package (e.g. shinyshadcn).
 * Called via window.shinyjson.registerComponents(catalog, registry).
 *
 * @param _catalog - Catalog definition (reserved for future validation)
 * @param registry - Map of component name → React component
 */
function registerComponents(
  _catalog: unknown,
  registry: ComponentRegistry,
): void {
  Object.assign(_registry, registry);
}

/**
 * Get the current accumulated registry for use by the renderer.
 */
function getRegistry(): ComponentRegistry {
  return _registry;
}

export { registerComponents, getRegistry };
```

**Step 2: Type-check**

```bash
cd js && npm run lint
```

Expected: No TypeScript errors.

---

### Task 6: JS renderer.tsx

**Files:**
- Create: `js/src/renderer.tsx`

**Step 1: Create js/src/renderer.tsx**

```tsx
import { Renderer } from "@json-render/react";
import type { Spec } from "@json-render/core";
import { getRegistry } from "./registry";

interface ShinyjsonRendererProps {
  spec: Spec;
}

/**
 * React component that renders a json-render Spec using all registered components.
 * The registry is read at render time, capturing all components registered via
 * window.shinyjson.registerComponents() before this render was triggered.
 */
function ShinyjsonRenderer({ spec }: ShinyjsonRendererProps) {
  return <Renderer spec={spec} registry={getRegistry()} />;
}

export { ShinyjsonRenderer };
```

**Step 2: Type-check**

```bash
cd js && npm run lint
```

Expected: No TypeScript errors.

---

### Task 7: JS shiny.d.ts + index.ts

**Files:**
- Create: `js/src/shiny.d.ts`
- Create: `js/src/index.ts`

**Step 1: Create js/src/shiny.d.ts**

Type declarations for Shiny's browser-global API. Shiny is loaded by the runtime before `shinyjson.js` — these types are never bundled.

```typescript
/**
 * Type declarations for Shiny's global JavaScript API.
 * Shiny is loaded by the browser before shinyjson.js runs.
 */
declare global {
  const Shiny: {
    OutputBinding: {
      new (): ShinyOutputBinding;
      prototype: ShinyOutputBinding;
    };
    outputBindings: {
      register(binding: ShinyOutputBinding, name: string): void;
    };
  };

  interface ShinyOutputBinding {
    find(scope: Element): ArrayLike<Element>;
    getId(el: Element): string;
    renderValue(el: Element, data: unknown): void;
    renderError(el: Element, err: { message: string; type?: string }): void;
    clearError(el: Element): void;
    showProgress(el: Element, show: boolean): void;
  }
}

export {};
```

**Step 2: Create js/src/index.ts**

```typescript
import React from "react";
import { createRoot, type Root } from "react-dom/client";
import type { Spec } from "@json-render/core";
import type { ComponentRegistry } from "@json-render/react";
import { registerComponents } from "./registry";
import { ShinyjsonRenderer } from "./renderer";
import "./shinyjson.css";

// Extend window with shinyjson's public global API
declare global {
  interface Window {
    shinyjson: {
      registerComponents: (catalog: unknown, registry: ComponentRegistry) => void;
    };
  }
}

// Expose global API — called by downstream packages at page load
window.shinyjson = { registerComponents };

// React root cache: one React root per output DOM element
const roots = new WeakMap<Element, Root>();

function getOrCreateRoot(el: HTMLElement): Root {
  if (!roots.has(el)) {
    roots.set(el, createRoot(el));
  }
  return roots.get(el)!;
}

// Shiny output binding for .shinyjson-output elements
class ShinyjsonOutputBinding extends Shiny.OutputBinding {
  find(scope: Element): NodeListOf<Element> {
    return scope.querySelectorAll(".shinyjson-output");
  }

  renderValue(el: Element, data: Spec | null): void {
    if (!data) return;
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(React.createElement(ShinyjsonRenderer, { spec: data }));
  }

  renderError(el: Element, err: { message: string }): void {
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(
      React.createElement(
        "div",
        { style: { color: "red", padding: "8px" } },
        err.message,
      ),
    );
  }
}

// Register with Shiny — Shiny is always loaded before this script
// because HTMLDependency ordering places Shiny's scripts first.
Shiny.outputBindings.register(new ShinyjsonOutputBinding(), "shinyjson.output");
```

**Step 3: Type-check**

```bash
cd js && npm run lint
```

Expected: No TypeScript errors.

---

### Task 8: Build JS + Update Dist

**Step 1: Build JS**

```bash
cd js && npm run build
```

Expected: `js/dist/shinyjson.js` and `js/dist/shinyjson.css` created. The bundle will be large (~150KB+) because React is bundled.

**Step 2: Verify build output**

```bash
ls -lh js/dist/
```

Expected: `shinyjson.js` and `shinyjson.css` present.

**Step 3: Copy dist assets to Python package www/**

```bash
cp -r js/dist/* pkg-py/src/shinyjson/www/
git rev-parse HEAD > pkg-py/src/shinyjson/www/GIT_VERSION
```

**Step 4: Verify www/ contents**

```bash
ls pkg-py/src/shinyjson/www/
```

Expected: `shinyjson.js`, `shinyjson.css`, `GIT_VERSION`, `.gitkeep`.

**Step 5: Commit**

```bash
git add js/src/ js/dist/ pkg-py/src/shinyjson/www/
git commit -m "feat: build JS IIFE bundle with Shiny output binding and global registry API"
```

Note: `js/dist/` is committed so the package can be published without requiring a JS build step by end users.

---

## Phase 2: Python Package

---

### Task 9: Python _spec.py (TDD)

**Files:**
- Create: `pkg-py/tests/test_spec.py`
- Create: `pkg-py/src/shinyjson/_spec.py`

**Step 1: Write the failing test**

Create `pkg-py/tests/test_spec.py`:

```python
from shinyjson._spec import Element, Spec


def test_element_to_dict_no_children():
    elem = Element(type="Card", props={"title": "Hello"}, children=[])
    assert elem.to_dict() == {
        "type": "Card",
        "props": {"title": "Hello"},
        "children": [],
    }


def test_element_to_dict_with_children():
    elem = Element(type="Page", props={}, children=["card-1", "card-2"])
    assert elem.to_dict() == {
        "type": "Page",
        "props": {},
        "children": ["card-1", "card-2"],
    }


def test_element_default_children():
    elem = Element(type="Metric", props={"value": 42})
    assert elem.to_dict()["children"] == []


def test_spec_to_dict_single_element():
    spec = Spec(
        root="card",
        elements={"card": Element(type="Card", props={"title": "Hi"})},
    )
    assert spec.to_dict() == {
        "root": "card",
        "elements": {
            "card": {"type": "Card", "props": {"title": "Hi"}, "children": []}
        },
    }


def test_spec_to_dict_nested():
    spec = Spec(
        root="page",
        elements={
            "page": Element(type="Page", props={}, children=["card"]),
            "card": Element(type="Card", props={"title": "Hi"}),
        },
    )
    result = spec.to_dict()
    assert result["root"] == "page"
    assert result["elements"]["page"]["children"] == ["card"]
    assert result["elements"]["card"]["type"] == "Card"
```

**Step 2: Run to verify it fails**

```bash
uv run pytest pkg-py/tests/test_spec.py -v
```

Expected: `ImportError: cannot import name 'Element' from 'shinyjson._spec'`

**Step 3: Write minimal implementation**

Create `pkg-py/src/shinyjson/_spec.py`:

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Element:
    type: str
    props: dict[str, Any]
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "props": self.props, "children": self.children}


@dataclass
class Spec:
    root: str
    elements: dict[str, Element]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "elements": {
                key: elem.to_dict() for key, elem in self.elements.items()
            },
        }
```

**Step 4: Run to verify it passes**

```bash
uv run pytest pkg-py/tests/test_spec.py -v
```

Expected: 5 tests PASSED.

**Step 5: Commit**

```bash
git add pkg-py/src/shinyjson/_spec.py pkg-py/tests/test_spec.py
git commit -m "feat: add Spec and Element dataclasses"
```

---

### Task 10: Python _output.py (TDD)

**Files:**
- Create: `pkg-py/tests/test_output.py`
- Create: `pkg-py/src/shinyjson/_output.py`

**Step 1: Write the failing test**

Create `pkg-py/tests/test_output.py`:

```python
from htmltools import HTMLDependency, Tag

from shinyjson._output import ui


def test_ui_returns_tag():
    result = ui("my-output")
    assert isinstance(result, Tag)


def test_ui_has_correct_id():
    result = ui("my-output")
    assert result.attrs.get("id") == "my-output"


def test_ui_has_shinyjson_class():
    result = ui("my-output")
    classes = result.attrs.get("class", "")
    assert "shinyjson-output" in classes


def test_ui_accepts_extra_deps():
    dep = HTMLDependency("test", "1.0.0", source="/tmp", script={"src": "t.js"})
    result = ui("my-output", extra_deps=[dep])
    assert isinstance(result, Tag)


def test_ui_no_extra_deps_by_default():
    result = ui("my-output")
    assert isinstance(result, Tag)
```

**Step 2: Run to verify it fails**

```bash
uv run pytest pkg-py/tests/test_output.py -v
```

Expected: `ImportError: cannot import name 'ui' from 'shinyjson._output'`

**Step 3: Write minimal implementation**

Create `pkg-py/src/shinyjson/_output.py`:

```python
from pathlib import Path
from typing import Sequence

from htmltools import HTMLDependency, Tag, div


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyjson",
        version="0.1.0",
        source=str(Path(__file__).parent / "www"),
        script={"src": "shinyjson.js"},
        stylesheet={"href": "shinyjson.css"},
    )


def ui(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
    """Create a Shiny output placeholder for a shinyjson renderer.

    Args:
        id: The output ID. Must match the server-side ``@shinyjson.render``
            function name.
        extra_deps: Additional HTML dependencies to include. Used by downstream
            packages to inject their own JS/CSS (e.g. ``shinyshadcn``).

    Returns:
        A ``<div>`` tag that the shinyjson Shiny output binding renders into.
    """
    return div(
        id=id,
        class_="shinyjson-output",
        _dep(),
        *(extra_deps or []),
    )
```

**Step 4: Run to verify it passes**

```bash
uv run pytest pkg-py/tests/test_output.py -v
```

Expected: 5 tests PASSED.

**Step 5: Commit**

```bash
git add pkg-py/src/shinyjson/_output.py pkg-py/tests/test_output.py
git commit -m "feat: add shinyjson.ui() output placeholder function"
```

---

### Task 11: Python _render.py

**Files:**
- Create: `pkg-py/src/shinyjson/_render.py`

No TDD for this task — testing a Shiny `Renderer` subclass requires a live Shiny session. The implementation is straightforward and verified by type-checking.

**Step 1: Write implementation**

Create `pkg-py/src/shinyjson/_render.py`:

```python
from typing import Any

from htmltools import Tag
from shiny.render.renderer import Renderer

from ._output import ui
from ._spec import Spec


class render(Renderer[Spec]):
    """Render a :class:`~shinyjson.Spec` as a reactive Shiny JSON output.

    Use this decorator on a server function that returns a
    :class:`~shinyjson.Spec` instance. The spec is serialized and sent to the
    browser, where the ``shinyjson`` Shiny output binding renders it using all
    registered downstream components.

    Example::

        @shinyjson.render
        def my_output() -> shinyjson.Spec:
            return shinyjson.Spec(
                root="card",
                elements={"card": shinyjson.Element(type="Card", props={"title": "Hi"})},
            )

    Downstream packages subclass this to accept their own return types::

        class render(shinyjson.render):
            async def transform(self, value: MyComponent) -> Any:
                return value.to_spec().to_dict()
    """

    async def transform(self, value: Spec) -> Any:
        return value.to_dict()

    def auto_output_ui(self) -> Tag:
        # Express mode: auto-generate the output container
        return ui(self.output_id)
```

**Step 2: Type-check**

```bash
uv run pyright pkg-py/src/shinyjson/_render.py
```

Expected: No errors. If `Renderer`'s `transform` signature causes type issues, add `# type: ignore[override]` on the `transform` method — Shiny's internal types are not always fully exported.

**Step 3: Commit**

```bash
git add pkg-py/src/shinyjson/_render.py
git commit -m "feat: add shinyjson.render decorator"
```

---

### Task 12: Python __init__.py

**Files:**
- Modify: `pkg-py/src/shinyjson/__init__.py`

**Step 1: Replace the placeholder with the public API**

```python
from ._output import ui
from ._render import render
from ._spec import Element, Spec

__all__ = ["Element", "Spec", "render", "ui"]
```

**Step 2: Verify all exports are importable**

```bash
uv run python -c "
import shinyjson
print(shinyjson.Spec)
print(shinyjson.Element)
print(shinyjson.render)
print(shinyjson.ui)
print('All exports OK')
"
```

Expected: Prints class/function names and `All exports OK`.

**Step 3: Commit**

```bash
git add pkg-py/src/shinyjson/__init__.py
git commit -m "feat: export public shinyjson API"
```

---

### Task 13: Full Python Checks

Run all checks from the Makefile to ensure the package is clean.

**Step 1: Run all tests**

```bash
uv run pytest pkg-py/tests/ -v
```

Expected: All tests PASS (8 total: 5 spec + 5 output, minus any skipped).

**Step 2: Run type checks**

```bash
uv run pyright pkg-py/src/shinyjson
```

Expected: No errors. Document any known Shiny type stub gaps in a `# type: ignore` comment rather than working around them with `Any` everywhere.

**Step 3: Run linter and formatter**

```bash
uv run ruff check pkg-py/src/shinyjson
uv run ruff format --check pkg-py/src/shinyjson
```

If there are format issues:

```bash
uv run ruff format pkg-py/src/shinyjson
uv run ruff check --fix pkg-py/src/shinyjson
```

**Step 4: Commit any fixes**

```bash
git add pkg-py/src/shinyjson/
git commit -m "chore: fix lint and format issues"
```

**Step 5: Verify full commit history**

```bash
git log --oneline
```

Expected: ~10 commits showing the incremental progression from skeleton to full package.
