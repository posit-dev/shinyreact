# Example 01 — Old Faithful, `ui.tsx` style (no build step)

Shiny's canonical [`01_hello`](https://github.com/rstudio/shiny/blob/main/inst/examples-shiny/01_hello/app.R)
app — a bins slider over the Old Faithful waiting times — rebuilt as the
smallest possible `ui.tsx`-first app. No JSX, no bundler, no `package.json`.
Edit `app.js` and reload.

`app.py` (Express, via `set_react_page()`) and `app-core.py` (Core, via
`page_react_html()`) are two server-side entries for the same `www/` client;
`app.R` is the R twin.

## What it shows

The split that makes the pattern worth using. In traditional Shiny, `01_hello`
renders the histogram *on the server* — `renderPlot({ hist(...) })` ships a PNG
to the browser and the client is a passive `<img>`. Here the server never
produces a picture:

- **Server** — one `reactive_output` returning `{breaks, counts}` (plain JSON
  from R's `hist(..., plot = FALSE)` / a dependency-free Python binner), plus a
  caption string. That's the entire server. No plotting library, no image
  encoding, no `plotOutput` placeholder.
- **Client** — `www/app.js` reads that JSON with `useShinyOutputValue` and draws
  the bars as SVG `<rect>`s. Because the chart is real DOM the client owns, it
  can be styled, animated, or made interactive without another round trip.

The bins slider goes the other way: `useShinyInput("bins", 30)` pushes the value
to Shiny, which recomputes the counts.

It also demonstrates the output-status idiom from the repo's guidance — the
chart stays mounted while the server recomputes and only dims via
`useShinyOutputStatus("dist_data") === "recalculating"`. Dragging the slider
never tears the SVG down and re-mounts it.

## Layout

```
examples/01-hello/
├── app.py            # Express: set_react_page() + 2 reactive_output outputs
├── app-core.py       # Core: page_react_html() + App(..., static_assets=), same outputs
├── app.R             # R: page_react_html() + reactive_output, same outputs
├── faithful.py       # Old Faithful waiting times + a stdlib-only binner (Python)
├── faithful.csv      # base R's `faithful` dataset, exported for the Python servers
└── www/
    ├── index.html    # 2 lines: stylesheet, script (the app appends its own mount div to <body>)
    ├── app.js        # raw React.createElement (with `h` shorthand) + an SVG histogram
    └── main.css      # sidebar/panel layout
```

No `node_modules`, no Vite, no build script — and on the Python side no
numpy/matplotlib either.

`app.R` uses base R's built-in `faithful` dataset; `faithful.csv` is that same
data exported so the Python servers don't need a data dependency. R's outputs
return `NULL` until the client's first `bins` message arrives (Python raises a
silent exception instead), and wrap the histogram vectors in `I()` so a
single-bin result still serializes as a JSON array rather than a scalar.

`app-core.py` passes `static_assets={"/": .../www}` to `App()`. Shiny Express
(`app.py`) and R's `runApp()` (`app.R`) both mount the app directory's `www/`
automatically; Core's `App()` does not, so without it `index.html` loads and
then 404s on `app.js` and `main.css`.

## Bridge primitives used

- `from shinyreact import reactive_output, set_react_page` (Express server, `app.py`) / `page_react_html` (Core server, `app-core.py`); `library(shinyreact)` with `page_react_html()` + `reactive_output()` in `app.R`
- `window.shinyreact.useShinyInput(id, default)` for the bins slider
- `window.shinyreact.useShinyOutputValue(id, default)` for the histogram data and caption
- `window.shinyreact.useShinyOutputStatus(id)` to dim the chart while it recalculates
- `window.shinyreact.useShinyInitialized()` to suppress the placeholder UI during connection setup

`window.shinyreact.React` and `window.shinyreact.ReactDOM` are pulled in directly so the React app shares the React instance that owns the shinyreact hooks.

## Run it

```bash
# Express API
uv run shiny run examples/01-hello/app.py

# Core API (same client, same outputs)
uv run shiny run examples/01-hello/app-core.py

# R (same client, same outputs — the R package's page_react_html + reactive_output)
Rscript -e 'shiny::runApp("examples/01-hello/app.R")'
```

Open the URL printed by Shiny.

## When to use this pattern

Good fit for `ui.tsx`-first apps that are small enough to not need JSX or component libraries — proof of concept, internal tools, anything where the cost of running a build is more than the cost of writing `React.createElement` calls. As soon as you want shadcn or Tailwind utility classes, see [03-columns-shadcn](../03-columns-shadcn/) and [04-shadcn](../04-shadcn/) for the Vite-based setup.

If you'd rather keep rendering server-side, [04-shadcn](../04-shadcn/) shows
`@render.plot` + `ImageOutput` (matplotlib PNGs) side by side with the data-only
approach used here.
