# Example 12 — Drag-between-columns (legacy SPA prototype)

The columns demo using the **first** SPA-first prototype: `shinyjsonold` + a local `spa_app.py` + an esbuild JSX build. Predates the package split; preserved as historical context.

> **Note:** Kept as the "before" picture. New SPA-first apps should use [example 14](../14-columns-new-spa/) (no build step) or [example 15](../15-columns-shadcn/) (shadcn + Vite).

## What it shows

- The same drag-between-columns interaction as [example 11](../11-columns-traditional/), but server logic collapses to a single `@reactive.event(input.move_item)` plus a `@shinyjson.render` returning the column dict.
- A local `SpaApp` (since the new `shinyjson.SpaApp` did not yet exist).
- An esbuild script bundling `src/App.jsx` to `www/index-XXXX.js` with a content hash.
- `App.jsx` written in JSX, requiring the build step.

## Layout

```
examples/12-columns-spa/
├── app.py            # Server: shinyjsonold.render + local SpaApp
├── spa_app.py        # Local SpaApp (now lives in shinyjson package)
├── package.json      # esbuild build script
├── src/
│   ├── App.jsx
│   ├── index.html
│   ├── index.jsx
│   └── react-shim.js
└── www/              # Built output (committed)
```

## Run it

```bash
cd examples/12-columns-spa && npm install && npm run build && cd -
uv run shiny run examples/12-columns-spa/app.py
```

## Compared to ex 14 and 15

- **Ex 14** drops the build step entirely (raw `React.createElement`) and uses the new `shinyjson.SpaApp` / `@render_json` from the package.
- **Ex 15** keeps a build step (Vite) but in exchange gets real shadcn/ui styling.
- The server file in all three is functionally identical — the difference is purely on the client.
