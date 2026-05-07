# Example 5 — shadcn-styled cards (shinyreact)

A gallery of cards styled to look like [shadcn/ui](https://ui.shadcn.com/) — but using **hand-written CSS variables and class names**, not real shadcn (no Tailwind, no `cva`, no build step). This is a "looks like shadcn" approximation that runs as a single static JS file.

> **Note:** Uses `shinyreact`. For the `ui.tsx`-first equivalent that uses *actual* shadcn components (real `cva`, real Tailwind v4, real `Card`/`Button`/etc.), see [example 16](../16-shadcn/).

## What it shows

- `PageLayout`, `Grid`, `TextInputCard`, `ButtonEventCard`, `PlotCard` registered in `shadcn.js` using `React.createElement` plus class names that match the shadcn naming convention.
- `styles.css` defines the shadcn CSS variables (`--background`, `--primary`, etc.) by hand and applies utility-style classes.
- The plot card uses `window.shinyreact.ImageOutput` to surface a matplotlib figure rendered with `@render.plot`.

## Layout

```
examples/5-shadcn/
├── app.py        # Server: PageLayout with three cards + matplotlib plot
├── shadcn.js     # JS bundle: createElement-based components, no JSX
└── styles.css    # Hand-written CSS variables and utility classes
```

## Run it

```bash
uv run shiny run examples/5-shadcn/app.py
```

## When to prefer this vs. example 16

- **This example:** zero build step, zero dependencies, ships in one JS file. Fine for a small demo where "approximately shadcn" is good enough.
- **Example 16:** real shadcn components with `cva` variants, real Tailwind v4, lucide icons. Brings a Vite + npm setup but gives you the actual shadcn registry and TypeScript-friendly variants.
