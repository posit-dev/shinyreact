# scaffold-framework

Scaffold a new UI framework under `ui-frameworks/` from scratch.

## When to use

When the user says "add MUI", "scaffold a new framework", or "create a
`<framework>` integration."

## Inputs needed

- **framework** — short lowercase name (e.g. `mui`, `mantine`, `radix`)
- **npm_package** — the npm package name (e.g. `@mui/material`, `@mantine/core`)
  - Leave empty for copy-paste frameworks like shadcn (no npm package)
- **first_components** — comma-separated list of components to add immediately
  (e.g. `Button, Card, TextField`)

## Two types of framework

**Copy-paste (shadcn model):** no npm package; component source is checked into
`js/src/components/`. You own and build the source.

**npm library (MUI, Mantine, Radix):** component source is an npm dependency;
Vite bundles it. No source to copy in — just write the wrappers.

## Steps

### 1. Create directory structure

```bash
mkdir -p ui-frameworks/<framework>/js/src/components   # copy-paste only
mkdir -p ui-frameworks/<framework>/js/src/wrappers
mkdir -p ui-frameworks/<framework>/js/src/lib          # if utils needed
mkdir -p ui-frameworks/<framework>/js/www
mkdir -p ui-frameworks/<framework>/pkg-py
mkdir -p ui-frameworks/<framework>/pkg-r
mkdir -p ui-frameworks/<framework>/examples/app-py
mkdir -p ui-frameworks/<framework>/examples/app-r
mkdir -p ui-frameworks/<framework>/tests/unit
mkdir -p ui-frameworks/<framework>/tests/e2e
```

### 2. package.json

```json
{
  "name": "shiny<framework>",
  "private": true,
  "type": "module",
  "scripts": { "build": "vite build", "dev": "vite build --watch" },
  "dependencies": {
    "<npm_package>": "latest"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "vite": "^5.4.0"
  }
}
```

For Tailwind-based frameworks add `tailwindcss` and `@tailwindcss/vite`.

### 3. vite.config.js

Copy the shadcn `vite.config.js` pattern — change only:
- `entry`: `src/index.jsx` (or `.tsx`)
- `name`: `Shiny<Framework>` (IIFE global name, unused but required)
- `fileName`: `() => "<framework>.js"`
- `outDir`: `"../www"`

**The externalize block must stay exactly as-is** — do not add more externals,
do not change the globals mapping. Note: `react-dom` is intentionally NOT
externalized — portal-based components (Radix overlays) need `createPortal`
which lives in `react-dom`, not `react-dom/client`.

```js
external: ["react", "react-dom/client"],
output: { globals: {
  react: "window.shinyreact.React",
  "react-dom/client": "window.shinyreact.ReactDOM",
}}
```

### 4. src/index.jsx

```jsx
// For Tailwind frameworks only:
// import "@/index.css";

import { ComponentA } from "@/wrappers/ComponentA";
// ... more imports

window.shinyreact.registerComponents(null, {
  "<framework>:ComponentA": ComponentA,
  // ...
});
```

### 5. Python _dep() helper

```python
from pathlib import Path
from htmltools import HTMLDependency

_www = Path(__file__).parent.parent / "www"

def _dep():
    js = _www / "<framework>.js"
    version = str(int(js.stat().st_mtime)) if js.exists() else "0"
    return HTMLDependency(
        name="shiny<framework>",
        version=version,
        source={"subdir": str(_www)},
        script={"src": "<framework>.js", "defer": ""},
        stylesheet={"href": "<framework>.css"},
    )
```

### 6. Add first components

Run `/scaffold-component` for each component in the first_components list.

### 7. Write example app

Follow the pattern in `ui-frameworks/shadcn/examples/app-py/app.py` and
`app-r/app.R`. Show all first_components in one card.

### 8. Write README.md

At `ui-frameworks/<framework>/README.md`:
- What the framework is and its npm package
- `npm install && npm run build` to build
- Example usage (Python + R, 10 lines each)
- How to add more components (link to scaffold-component skill)

### 9. Verify

```bash
cd ui-frameworks/<framework>/js
npm install
npm run build      # should produce www/<framework>.js
```

Run the example app and confirm components render.
