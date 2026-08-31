# examples/11-npm-local — behavior

Old Faithful histogram at the npm tier with nothing else on the page: the
client imports `@posit/shinyreact`, and the server injects no shinyreact JS and
no config tag. Two interchangeable servers (`app.py`, `app.R`) over one `www/`
client.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## Client distribution

- `package.json` depends on `"@posit/shinyreact": "file:../../pkg-js"` — the
  repo-relative placeholder `examples/09-hmr` uses until the first npm publish
  - `pkg-js` must be built (`make js-build`) before `npm install`
  - nothing machine-specific reaches `package.json` or the lockfile
- React and ReactDOM are the app's own devDependencies, bundled into
  `www/ui.js`

## Page

- the page carries this app's dependency, named `npm-local`, and no
  `shinyreact` dependency `(test)`
  - so there is exactly one React and one copy of the hooks on the page
- the page has no `#shinyreact-config` tag `(test)`
  - `page_bare()` is the one page entry point that never emits it
  - therefore no protocol handshake runs; the client tolerates its absence
  - bookmark restore is unavailable in this shape; this app does not bookmark
  - contrast `examples/09-hmr`, the other npm-tier example: it uses
    `set_react_page(shinyreact_js="client")`, which omits the JS but still
    emits the tag
- title is `"Old Faithful"`, set explicitly (`page_bare(title=)`), not derived
  from the folder name
- `www/ui.js` and `www/ui.css` are served by the dependency, versioned by
  `ui.js`'s mtime; neither is committed
  - `www/.gitkeep` is, so the directory exists before the first build —
    `[py]` `App()` mounts the dependency's source dir and raises
    `RuntimeError: Directory ... does not exist` without it

## Server

- output `dist_data` → `{breaks: number[], counts: number[]}`
  - `[py]` hand-written equal-width binner in `app.py`, stdlib only; data read
    from `faithful.csv` next to it, column `waiting`
  - `[r]` `hist(waiting, breaks = seq(...), plot = FALSE)` over base R's
    `faithful$waiting`
  - `[r]` vectors are wrapped in `I()` so a one-bin result serializes as a JSON
    array, not a scalar
- output `dist_caption` → `"272 eruptions in N bins"`, singular `"bin"` when
  `N == 1`
- before the client's first `bins` message
  - `[py]` `input.bins()` raises a silent exception, so neither output produces
    a value
  - `[r]` `input$bins` is `NULL` and both outputs return `NULL` explicitly

## Client (`src/ui.jsx`)

- JSX, built by Vite in lib/IIFE mode to `www/ui.js`
  - nothing is externalized: React, ReactDOM and the hooks are all bundled
  - `import "@posit/shinyreact/styles"` and `./ui.css` are emitted as
    `www/ui.css` (`assetFileNames: "ui.[ext]"`)
- mounts into a `<div>` the client appends to `<body>`; the page ships no
  container
- bins slider: `useShinyInput("bins", 30)`, `<input type="range">`, `min` 1,
  `max` 50, `id="bins"`; current value echoed in the label
- histogram drawn as SVG: one `<rect fill="#447099">` per count, viewBox
  `0 0 620 320`, `role="img"` with `aria-label` `"Histogram of Old Faithful
  waiting times in N bins"`
- no `dist_data` value yet → a `.placeholder` div reading `"Loading…"`
- value present and `useShinyOutputStatus("dist_data") === "recalculating"` →
  the SVG stays mounted and gets `class="recalculating"` (`opacity: 0.6`)
- caption paragraph shows `dist_caption`, or a single space before the first
  value arrives
