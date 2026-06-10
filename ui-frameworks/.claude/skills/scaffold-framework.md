# scaffold-framework

Bootstrap a new UI framework integration under `ui-frameworks/` from scratch.

## When to use

When the user says "add MUI", "scaffold a new framework", or "create a `<framework>` integration."

---

## Step 0 — Identify the framework model

**Copy-paste (shadcn model):** component source is checked into `js/src/components/`. No npm dependency on the UI library itself — you own the source files.

**npm library (MUI, Mantine, etc.):** component source is an npm package. Write thin bridge files in `js/src/components/` that import from the package. No source copying.

This affects Step 1 (directories), Step 2 (package.json), and how component files are written. Everything else is identical.

---

## Step 1 — Create directory structure

```bash
mkdir -p ui-frameworks/<framework>/js/src/components
mkdir -p ui-frameworks/<framework>/js/src/lib          # for cn(), trigger-button, etc.
mkdir -p ui-frameworks/<framework>/js/www
mkdir -p ui-frameworks/<framework>/pkg-py/<framework>
mkdir -p ui-frameworks/<framework>/pkg-r
mkdir -p ui-frameworks/<framework>/examples/app-py
mkdir -p ui-frameworks/<framework>/examples/app-r
mkdir -p ui-frameworks/<framework>/tests/unit
mkdir -p ui-frameworks/<framework>/tests/e2e
```

---

## Step 2 — package.json

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

For Tailwind-based frameworks (shadcn model) also add:
```json
"tailwindcss": "^4.0.0",
"@tailwindcss/vite": "^4.0.0"
```

For copy-paste frameworks with no npm UI package, omit `<npm_package>` from `dependencies`.

---

## Step 3 — vite.config.js

Copy from `ui-frameworks/shadcn/js/vite.config.js`. Change only:
- `entry` → `src/index.jsx`
- `name` → `Shiny<Framework>` (IIFE global name, unused but required by Rollup)
- `fileName` → `() => "<framework>.js"`
- `outDir` → `"../www"`

**The externals block is fixed — do not change it:**

```js
rollupOptions: {
  // react-dom is intentionally NOT externalized.
  // window.shinyreact.ReactDOM is react-dom/client only — no createPortal.
  // Radix/portal components need createPortal from react-dom (~2 kB gzip).
  external: ["react", "react-dom/client"],
  output: {
    globals: {
      react: "window.shinyreact.React",
      "react-dom/client": "window.shinyreact.ReactDOM",
    },
  },
},
```

For Tailwind-based frameworks, also add the Tailwind plugin:
```js
import tailwindcss from "@tailwindcss/vite";
plugins: [react(), tailwindcss()],
```

---

## Step 4 — src/hooks.js

Create `js/src/hooks.js`. All component files import hooks from here — never destructure `window.shinyreact` inline.

```js
export const {
  useShinyInput,
  useShinyInputValue,
  useSetShinyInput,
  useShinyOutputValue,
  useShinyOutputStatus,
  useShinyMessageHandler,
  useShinyInitialized,
  useShinyBusy,
} = window.shinyreact;
```

---

## Step 5 — src/lib/utils.js (Tailwind frameworks only)

```js
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs) { return twMerge(clsx(inputs)); }
```

Add `clsx` and `tailwind-merge` to `dependencies` in package.json.

---

## Step 6 — src/lib/trigger-button.jsx (if framework has overlay components)

Shared styled trigger button for Dialog, Popover, Sheet, etc. Avoids duplicating the className string across every overlay component.

```jsx
export function TriggerButton({ children, ...props }) {
  return (
    <button
      type="button"
      className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 h-9 text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
      {...props}
    >
      {children}
    </button>
  );
}
```

Adjust the className to match the framework's design language.

---

## Step 7 — src/styles.css (Tailwind frameworks only)

```css
@import "tailwindcss";

@theme {
  --color-background: hsl(0 0% 100%);
  --color-foreground: hsl(240 10% 3.9%);
  --color-popover: hsl(0 0% 100%);
  --color-popover-foreground: hsl(240 10% 3.9%);
  --color-primary: hsl(240 5.9% 10%);
  --color-primary-foreground: hsl(0 0% 98%);
  --color-secondary: hsl(240 4.8% 95.9%);
  --color-secondary-foreground: hsl(240 5.9% 10%);
  --color-muted: hsl(240 4.8% 95.9%);
  --color-muted-foreground: hsl(240 3.8% 46.1%);
  --color-accent: hsl(240 4.8% 95.9%);
  --color-accent-foreground: hsl(240 5.9% 10%);
  --color-border: hsl(240 5.9% 90%);
  --color-input: hsl(240 5.9% 90%);
  --color-ring: hsl(240 5% 64.9%);
  --color-destructive: hsl(0 84.2% 60.2%);
}
```

Add tokens as needed when wrapping components that use Tailwind classes not covered above.

---

## Step 8 — src/index.jsx

```jsx
import "@/styles.css";  // Tailwind frameworks only

import { ComponentA } from "@/components/component-a";
// ... more imports

window.shinyreact.registerComponents(null, {
  "<framework>:ComponentA": ComponentA,
  // ...
});
```

---

## Step 9 — Python package

Create `ui-frameworks/<framework>/pkg-py/<framework>/__init__.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Literal

import shinyreact
from htmltools import HTMLDependency

_www = Path(__file__).parent.parent.parent / "www"


def _dep() -> HTMLDependency:
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

Note: `_www` is three `.parent` steps up because the package lives at
`pkg-py/<framework>/__init__.py` (two directories deep inside `pkg-py/`).

---

## Step 10 — R helpers

Create `ui-frameworks/<framework>/pkg-r/<framework>.R`:

```r
# <Framework> R helpers.
# source() this from app.R, then call <framework>_dep() and component helpers.

#' HTMLDependency for the <framework> JS + CSS bundle.
#' @param www_dir Absolute path to ui-frameworks/<framework>/www/
<framework>_dep <- function(www_dir) {
  www_dir <- normalizePath(www_dir, mustWork = TRUE)
  js <- file.path(www_dir, "<framework>.js")
  ver <- if (file.exists(js)) as.character(as.integer(file.mtime(js))) else "0"
  htmltools::htmlDependency(
    name       = "shiny<framework>",
    version    = ver,
    src        = c(file = www_dir),
    script     = list(src = "<framework>.js", defer = ""),
    stylesheet = "<framework>.css"
  )
}
```

---

## Step 11 — Add first components

Run `/scaffold-component` for each component in the initial list. See that skill for the full per-component workflow.

---

## Step 12 — Write example apps

Follow the pattern in `ui-frameworks/shadcn/examples/app-py/app.py` and `app-r/app.R`. Show all initial components in one card to prove end-to-end wiring works.

---

## Step 13 — Write README.md

At `ui-frameworks/<framework>/README.md`, cover:
- What the framework is and its npm package (if any)
- Build: `cd js && npm install && npm run build`
- Python usage snippet (10-15 lines)
- R usage snippet (10-15 lines)
- Component table
- How to add more components (link to `/scaffold-component`)
- Architecture notes (copy-paste vs npm, any framework-specific quirks)

---

## Step 14 — Verify

```bash
cd ui-frameworks/<framework>/js
npm install
npm run build      # should produce www/<framework>.js with no errors
```

Run the example app. Confirm all components render and Shiny inputs update correctly.
