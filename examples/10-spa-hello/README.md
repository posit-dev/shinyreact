# Example 10 — SPA-first prototype (legacy)

The original SPA-first proof-of-concept that motivated the package split. Same hello-world UI as [example 13](../13-spa-hello/), but built before the new `shinyjson` package existed: it imports `shinyjsonold`, defines `SpaApp` locally in `spa_app.py`, and uses an esbuild step to bundle JSX from `src/` into `www/`.

> **Note:** Kept around as the historical "before" picture. New SPA-first apps should use [example 13](../13-spa-hello/) (no build step) or [example 16](../16-shadcn/) (Vite + shadcn) instead.

## What it shows

- `SpaApp` reading a hand-written `index.html` and serving `www/` as static assets.
- React via `window.shinyjson.React`, hooks via `window.shinyjson.useShinyInput` / `useShinyOutput`.
- A name-input + click-counter UI with paired client-side and server-side displays for latency comparison (same shape as ex 13).
- An esbuild script in `package.json` that bundles `src/index.jsx` to a content-hashed `www/index-XXXX.js` and rewrites `www/index.html` from the `src/index.html` template.

## Layout

```
examples/10-spa-hello/
├── app.py            # Server: imports shinyjsonold + local SpaApp
├── spa_app.py        # Local SpaApp class (now lives in shinyjson package)
├── package.json      # esbuild build script
├── src/
│   ├── App.jsx
│   ├── index.html    # Template with __MAIN_JS__ placeholder
│   ├── index.jsx
│   └── react-shim.js
└── www/              # Built output (committed in this example)
```

## Run it

```bash
cd examples/10-spa-hello && npm install && npm run build && cd -
uv run shiny run examples/10-spa-hello/app.py
```

## Why ex 13 is the modern equivalent

- No `package.json`, no esbuild, no `src/` directory. Edits land in `www/app.js` and reload immediately.
- `SpaApp` lives in the `shinyjson` Python package, not duplicated per-example.
- `@shinyjson.render_json` replaces the old `@shinyjson.render` for arbitrary JSON values.
