# shinyjson Design

**Goal:** A minimal infrastructure package that lets other packages (e.g., `shinyshadcn`) build Shiny UI components powered by `vercel-labs/json-render`.

**Architecture:** A monorepo with a single JS build (`js/`) whose output is copied into both a Python package (`pkg-py/`) and an R package (`pkg-r/`). The JS layer exposes a global registration API; downstream packages call it from their own JS bundle to register React components. The Python and R layers provide a render decorator + UI function following Shiny conventions.

**Build order:** JS + repo infrastructure → Python package → R package.

---

## Repo Structure

```
shinyjson/
├── js/
│   ├── src/
│   │   ├── index.ts       # window.shinyjson global + Shiny output binding
│   │   ├── registry.ts    # registerComponents() + accumulated catalog/registry store
│   │   └── renderer.tsx   # React component wrapping @json-render/react <Renderer>
│   ├── package.json
│   └── vite.config.ts     # IIFE build → dist/shinyjson.{js,css}
├── pkg-py/
│   ├── src/shinyjson/
│   │   ├── __init__.py
│   │   ├── _render.py     # @shinyjson.render (Renderer subclass)
│   │   ├── _output.py     # shinyjson.ui() UI function
│   │   ├── _spec.py       # shinyjson.Spec dataclass
│   │   └── www/           # js/dist/ copied here by `make update-dist`
│   ├── tests/
│   └── pyproject.toml
├── pkg-r/
│   ├── R/
│   └── inst/lib/shiny/    # js/dist/ copied here by `make update-dist`
├── docs/
│   └── plans/
└── Makefile
```

---

## JS Layer

- **Build:** Vite + TypeScript + React, output as a single IIFE bundle (`shinyjson.js`, `shinyjson.css`)
- **Global API:**
  ```typescript
  window.shinyjson.registerComponents(catalog: CatalogDef, registry: RegistryDef): void
  ```
  Downstream packages call this once from their own JS bundle (loaded as a Shiny `HTMLDependency`). `shinyjson` accumulates all registrations before rendering.
- **Shiny output binding:** named `"shinyjson"` — receives a JSON spec message from the server, mounts a React root in the container `<div>`, renders via `@json-render/react`'s `<Renderer>` using the accumulated registry.

---

## Python Package API

```python
# UI — returns a <div> with the Shiny output binding + loads shinyjson.js/css
shinyjson.ui("my_id")

# Server — Renderer subclass; calls user fn, serializes Spec, sends to browser
@shinyjson.render
def my_id() -> shinyjson.Spec:
    return shinyjson.Spec(root="card-1", elements={...})
```

### `shinyjson.Spec`

```python
@dataclass
class Spec:
    root: str
    elements: dict[str, Element]

    def to_dict(self) -> dict: ...
```

### Extension point

`shinyjson.ui` accepts an `extra_deps` parameter for downstream packages to inject their own `HTMLDependency` (JS/CSS):

```python
shinyjson.ui(id, extra_deps=[_shadcn_html_dep()])
```

`shinyjson.render` can be subclassed; override `transform()` to convert downstream return types to `shinyjson.Spec`.

---

## Extension Mechanism (how `shinyshadcn` is built on top)

### JS (downstream package)

```javascript
// shinyshadcn/src/index.ts — loaded as HTMLDependency
window.shinyjson.registerComponents(catalog, registry);
```

### Python (downstream package)

```python
# UI
def ui(id: str) -> Tag:
    return shinyjson.ui(id, extra_deps=[_shadcn_html_dep()])

# Server
class render(shinyjson.render):
    async def transform(self, value: ShadcnComponent) -> shinyjson.Spec:
        return value.to_spec()
```

### What `shinyjson` explicitly does NOT provide

- No components — zero bundled UI elements
- No catalog — downstream packages own their catalogs entirely
- No styling — downstream packages own their CSS
