---
name: verify-ui-components
description: >-
  Browser-verify and debug a shinyreact ui-frameworks example/gallery app
  (Python and R): serve it, drive it headless, capture BOTH client
  console/page errors and server-side tracebacks, and diagnose the common
  runtime crashes (capitalize/null, builtin-name shadow, dropped async helper,
  stale bundle, parity drift). Use after adding or changing components in
  shinyshadcn / shinymui, or before declaring a gallery "done" — static checks
  do not catch these.
---

# verify-ui-components

Render-verify and fix runtime failures in `ui-frameworks/` example and gallery
apps. Tracking issue: posit-dev/shinyreact#166.

## Why this exists (read first)

`npm run build`, `tsc`, `vitest`, `uv build`, `import`, `R CMD check`, and `ruff`
all confirm code **compiles, imports, and serializes** — none of them mount the
React tree or run a Shiny session. Every gallery bug we shipped passed all of
those and still **crashed or rendered blank in the browser**. The only reliable
check is to **serve the app and drive it**, capturing errors from **both sides**:

- **Client** — React threw while rendering (e.g. MUI `capitalize`), blanking the
  output. Shows up as a `pageerror` / `console.error`; invisible server-side.
- **Server** — a `render_react` / reactive raised during serialization or an
  event (e.g. `AttributeError`). Shows up as a Python/R **traceback in the
  server log** and a red error `<div>` in `.shinyreact-output`; the browser
  console may be silent.

You must watch both. A "builds fine, looks fine for 3 seconds" check is not
enough — interaction (clicking every tab, clicking buttons) is what trips these.

## Setup (one time)

Playwright isn't in the default env. Install it via uv:

```bash
uv pip install playwright && uv run python -m playwright install chromium
```

(The `shiny-for-agents` skill covers generic Shiny-app driving; this skill is the
shinyreact-specific recipe + the bug playbook below.)

## Recipe

### 1. Serve, logging to a file (so you can read server tracebacks)

```bash
# Python
uv run shiny run --port 8801 ui-frameworks/<fw>/examples/<name>/app.py > /tmp/app.log 2>&1 &

# R (app dir, not the .R file)
Rscript -e 'shiny::runApp("ui-frameworks/<fw>/examples/<name>", port=8801, launch.browser=FALSE)' > /tmp/app.log 2>&1 &
sleep 6   # R is slower to boot
```

### 2. Drive it and capture both sides

```python
from playwright.sync_api import sync_playwright
pe, ce = [], []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.on("pageerror", lambda e: pe.append(str(e)))
    pg.on("console", lambda m: ce.append(m.text) if m.type == "error" else None)
    pg.goto("http://localhost:8801", wait_until="networkidle"); pg.wait_for_timeout(2500)
    # Click EVERY tab/category — lazily-rendered panels only mount on activation.
    for tab in ["Inputs","Display","Actions","Overlays","Navigation","Layout","Feedback"]:
        t = pg.query_selector(f"[role=tab]:has-text('{tab}'), button:has-text('{tab}')")
        if t:
            t.click(); pg.wait_for_timeout(1200)
            n = len(pg.query_selector_all("[data-slot], [class*=Mui], button, input"))
            print(f"{tab:11s} els={n:4d} errs={len(pe)+len(ce)}")
    # Click action buttons too (server-push toasts, dialogs, etc.).
    btn = pg.query_selector("button:has-text('Show toast')")
    if btn: btn.click(); pg.wait_for_timeout(1500)
    b.close()
print("PAGE ERRORS:", pe or "none")
print("CONSOLE ERRORS:", ce or "none")
```

Then read the **server log** for a traceback:

```bash
grep -iE "traceback|error in|attributeerror|not iterable|unhandled|exception" /tmp/app.log | tail -20
```

`INFO: connection closed` **alone** at the end is normal (the browser
disconnected). A traceback *before* it is a real server crash.

### 3. Pass criteria

- Every tab/category renders elements (count > a handful), and interactive
  buttons work (a toast appears, a dialog opens).
- **Zero** page errors, zero `console.error`, **no server traceback**.
- Both languages (Python *and* R) — they share the JS bundle but exercise
  different server code and helper signatures.

## Diagnosis: symptom → cause → fix

| Symptom | Cause | Fix |
|---|---|---|
| Whole tab/page blank; client error **"MUI error #7 / capitalize expects a string"** (or similar) | An optional Python/R arg defaulted to `None`/`NULL` → JSON `null` → the bridge passed it to a library prop that builds a class via `capitalize()` (e.g. Typography `align`/`color`); `capitalize(null)` throws and unmounts the tree | Coerce `null`→`undefined` in the bridge: `align={align ?? undefined}`. Applies to any library prop that maps `null` to a string op. |
| Server traceback **`'Node' object is not iterable`** during serialization; red error div, blank output | A helper builds `children=<a single Node>` instead of a list — often a component helper named like a Python builtin (e.g. `list`) **shadows it**, so `children=list(children)` calls the *component* | Use `children=[*children]` (shadow-proof); or ensure `children` is a list. Watch helper names that collide with builtins. |
| Server **`AttributeError: module has no attribute X`** → session closes (looks like a hang/timeout) | A helper is missing from the package — commonly an **`async def`** dropped by codegen/refactor that only matched `def`. The bug hides until the button/reactive that calls it fires | Restore the helper + re-export it. Make any def-scanning regex `^(?:async )?def`. Verify: `import pkg; hasattr(pkg, name)`. |
| Edits don't take effect; stale bundle served | `_dep()` preferred a gitignored build-time `www/` copy over the fresh shared one | Delete the build copy (`src/<pkg>/www/`) and/or make `_dep()` prefer the shared `www/`. Re-check the served bundle's `lib/<pkg>-<version>/...` URL. |
| One language's gallery is missing components / out of parity | The Python and R galleries drifted | Diff the component sets: `grep -oE 'sc\.[a-z_]+' app.py` vs `grep -oE 'shadcn_[a-z_]+' app.R`; bring the lagging one up to parity. |

## Resolve loop

1. Reproduce with the recipe; identify client vs server from *which* side errored.
2. Match the symptom in the table; fix the bridge / helper / dep.
3. If the JS bridge changed, rebuild (`cd js && npm run build`) and **delete any
   stale `src/<pkg>/www/` copy** so the fresh bundle is served.
4. Re-run the recipe; require zero errors on **both** sides, **both** languages.
5. Add a regression guard if practical (a unit test that the helper exists; a
   wire-shape test; or the CI e2e job proposed in #166).
