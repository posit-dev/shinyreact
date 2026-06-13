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
mkdir -p ui-frameworks/<framework>/www                 # vite build outputs here (outDir: "../www")
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
  // "shinyreact" is externalized to the host global the same way react is, so
  // bridges `import { useShinyInput } from "shinyreact"` resolve to property
  // access on window.shinyreact (no local hooks shim — see Step 4).
  external: ["react", "react-dom/client", "shinyreact"],
  output: {
    globals: {
      react: "window.shinyreact.React",
      "react-dom/client": "window.shinyreact.ReactDOM",
      shinyreact: "window.shinyreact",
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

## Step 4 — src/shinyreact.d.ts (host hook types)

Do **not** create a `src/hooks.js` shim. The host hooks are consumed as an external module: bridges write `import { useShinyInput } from "shinyreact"`, and the externals block in Step 3 maps `"shinyreact"` to `window.shinyreact`, exactly as `react` is externalized. The bundler rewrites each named import to a property access on the global and tree-shakes the hooks a file does not use.

Copy `ui-frameworks/shadcn/js/src/shinyreact.d.ts` verbatim. It is an ambient `declare module "shinyreact"` that types the eight hooks for editor IntelliSense (interim — these declarations ultimately belong in the core shinyreact package). The available hooks:

```
useShinyInput, useShinyInputValue, useSetShinyInput,
useShinyOutputValue, useShinyOutputStatus, useShinyMessageHandler,
useShinyInitialized, useShinyBusy
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

**This is the most important file to get right, and the one most likely to make
components look broken without touching any component code.** Shiny serves pages with
**Bootstrap loaded unlayered**, and unlayered CSS beats Tailwind's *layered*
utilities regardless of specificity. So out of the box Bootstrap silently wins on
every element it targets: bare headings (card title → Bootstrap's 28px), form
controls (inputs → 16px not 14px), `.grid` (Bootstrap's 12 columns override
`grid-cols-2`), `<p>` margins, colors. The component sizes are *correct*; Bootstrap
inflates them. The styles.css below re-asserts the framework's defaults with an
unlayered, `.shinyreact-output`-scoped compat layer. Copy `ui-frameworks/shadcn/js/src/styles.css`
and adapt; it has four parts:

```css
@import "tailwindcss";

/* 1. Force-generate layout utilities used only in app.py/app.R. Tailwind scans
   js/src, NOT the apps, so app-only classes (grid, grid-cols-2, flex-wrap, …)
   must be listed here or they silently no-op. */
@source inline("grid grid-cols-1 grid-cols-2 flex-wrap uppercase tracking-wide");

/* 2. Design tokens. */
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
  --radius: 0.5rem;
}

/* 3. Bootstrap color compat — redeclare the utilities Bootstrap overrides, with
   !important + the .shinyreact-output scope so they beat unlayered Bootstrap. */
.shinyreact-output .bg-primary { background-color: hsl(240 5.9% 10%) !important; }
.shinyreact-output .text-primary-foreground { color: hsl(0 0% 98%) !important; }
.shinyreact-output .border { border-color: hsl(240 5.9% 90%) !important; }
/* …add bg-secondary, bg-card, rounded-*, shadow as needed… */

/* 4. Typography reset — neutralize Bootstrap inside the React tree. */
.shinyreact-output {
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 1rem;                /* shadcn base = 16px; controls opt into text-sm */
  line-height: 1.5;
  color: hsl(240 10% 3.9%);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
.shinyreact-output :is(h1, h2, h3, h4, h5, h6) {
  font-size: inherit; font-weight: inherit; line-height: inherit; margin: 0;
}
.shinyreact-output :is(input, button, select, textarea) {
  font-size: inherit; line-height: inherit; font-family: inherit;
}
/* Re-assert Tailwind text sizes (font-size only) so a component's text-* class
   beats unlayered Bootstrap. This is what keeps the base at 16px while controls
   render at their intended text-sm (14px) — don't force-flatten to one size. */
.shinyreact-output .text-xs { font-size: 0.75rem !important; }
.shinyreact-output .text-sm { font-size: 0.875rem !important; }
.shinyreact-output .text-base { font-size: 1rem !important; }
.shinyreact-output .text-lg { font-size: 1.125rem !important; }
.shinyreact-output .text-xl { font-size: 1.25rem !important; }
.shinyreact-output .text-2xl { font-size: 1.5rem !important; }
.shinyreact-output p { margin: 0; }
/* Bootstrap 5 ships its own 12-column .grid — re-assert the cols utilities. */
.shinyreact-output .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)) !important; }
.shinyreact-output .grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
```

**Why this matters beyond the gallery:** without the typography reset, *every*
component renders at Bootstrap's sizes in a real Shiny app, not just examples. This
is core to the framework being usable, not cosmetic.

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

Build an installable package, not a single file. Mirror `ui-frameworks/shadcn/pkg-py/` as the template:

```
pkg-py/
  pyproject.toml         hatchling backend, built with uv; depends on shinyreact + htmltools
  hatch_build.py         build hook copying ../www into src/shiny<framework>/www at build time
  src/shiny<framework>/
    __init__.py          re-exports the category modules with __all__ (regenerated by /scaffold-component)
    _dep.py              _dep() (see below); _www falls back to the shared ../www for source checkouts
    _types.py            shared Literal aliases, if any
    _<category>.py       helpers grouped by category (inputs, display, overlays, menus, layout, feedback)
```

`_dep.py` resolves the bundled assets first, then the shared dir:

```python
_bundled = Path(__file__).parent / "www"                       # installed wheel
_shared = Path(__file__).parent.parent.parent.parent / "www"   # source checkout
_www = _bundled if (_bundled / "<framework>.js").exists() else _shared
```

The HTMLDependency stylesheet is `style.css`, not `<framework>.css`: Vite 5 lib mode with `cssCodeSplit: false` always emits the CSS asset as `style.css` (renaming needs `build.lib.cssFileName`, Vite 6+). Only the JS file is renamed, via `fileName`.

`hatch_build.py` copies the shared `../www` assets into the package at build time (the copy is gitignored) so the wheel and sdist ship them. Run `uv build` to produce them.

The category modules start empty; `/scaffold-component` appends helpers and regenerates `__init__.py`.

---

## Step 10 — R package

Build a full R package, not a single sourced file. Mirror `ui-frameworks/shadcn/pkg-r/`:

```
pkg-r/
  DESCRIPTION            Imports htmltools, rlang, shinyreact; Config/testthat/edition: 3; Roxygen markdown
  LICENSE  .Rbuildignore
  R/
    shiny<framework>-package.R   #' @importFrom shinyreact node  (+ send_message if used)
    dep.R                        <framework>_dep() (see below)
    <category>.R                 helpers by category (appended by /scaffold-component)
  inst/www/              committed copy of the built JS/CSS (re-sync after npm run build)
  man/  NAMESPACE         generated — run roxygen2::roxygenise()
  tests/testthat/
```

`<framework>_dep()` resolves the bundled assets via `system.file`, with an optional override for ad-hoc paths:

```r
<framework>_dep <- function(www_dir = NULL) {
  if (is.null(www_dir)) www_dir <- system.file("www", package = "shiny<framework>")
  www_dir <- normalizePath(www_dir, mustWork = TRUE)
  js <- file.path(www_dir, "<framework>.js")
  ver <- if (file.exists(js)) as.character(as.integer(file.mtime(js))) else "0"
  htmltools::htmlDependency(
    name = "shiny<framework>", version = ver, src = c(file = www_dir),
    script = list(src = "<framework>.js", defer = ""),
    stylesheet = "style.css"  # Vite 5 lib mode always emits style.css
  )
}
```

Because `R CMD INSTALL` has no build hook, the built bundle is committed under `inst/www/` (re-sync with `cp www/* pkg-r/inst/www/` after a rebuild) — the same convention the core package uses for `inst/lib/shiny/`. Each helper carries roxygen with `@param` (including `@param ...`), `@return`, and `@export`; run `roxygen2::roxygenise()` to regenerate `NAMESPACE` + `man/`.

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

Run the example app and **verify visually, not just with assertions** — drive it
headless with Playwright and *screenshot* it, then look at the image. Text
assertions ("element is visible") pass even when the layout is broken; the bugs
this integration actually hits are visual and only show in a render:
- Bootstrap inflating sizes (headings/inputs too big) — measure computed
  `fontSize` of a label/input and confirm it matches the framework's intent.
- A 12-column `.grid` where you expected 2 — check `gridTemplateColumns`.
- Portal/overlay failures — assert **zero console errors**, not just visibility.

A component "renders" is not the same as "looks right." Screenshot every example
tab once and eyeball it before declaring done.

---

## Pre-commit hook behavior (shadcn / Python-backed packages)

The pre-commit hooks run automatically on `git commit`. They modify files and exit
non-zero — the commit does NOT land. The correct response is to re-stage and retry:

1. `trailing-whitespace` — fixes `www/<framework>.js` automatically. Re-stage it.
2. `ruff-format` — auto-reformats Python files. Re-stage the reformatted file.
3. `ruff-check` — reports violations but does NOT fix them. Fix manually:
   - **E501 line too long (>88):** break docstring lines before column 88.
   - Other violations: address as reported.

Always run `git add` on every modified file the hooks touched, then retry the commit.
Never use `--no-verify` to skip hooks — they enforce the project's code style contract.
