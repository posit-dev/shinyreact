# examples/01-hello — behavior

Old Faithful waiting-time histogram: a bins slider on the client, binning on
the server, SVG drawing on the client. Three interchangeable servers
(`app.py`, `app-core.py`, `app.R`) over one `www/` client.

Format rules: `../README.md` § "Example behavior trees". `[py]` / `[r]` /
`[js]` mark a claim that holds only there; `(test)` marks a claim pinned by a
unit test; `(verify)` marks a claim not yet checked against the code.

## Data

- Old Faithful waiting times, 272 observations, minutes, min 43, max 96 `(test)`
  - `[py]` read from `faithful.csv` next to `app.py`, column `waiting`, at
    import time in `faithful.py`
  - `[r]` base R's built-in `faithful` dataset, column `waiting`
  - the `eruptions` column is never used
- the two sources are the same data — `[py]` `faithful.csv` is base R's
  `faithful` exported

## Server

- output `dist_data` → `{breaks: number[], counts: number[]}`
  - equal-width bins over `[min, max]`: `breaks` has `bins + 1` entries,
    `counts` has `bins` `(test)`
  - binning matches R's `hist()`: half-open `(lo, hi]` with the first bin
    inclusive of `lo` `(test)`
    - `[py]` hand-written in `faithful.py:histogram()`, stdlib only — no numpy
    - `[r]` `hist(waiting, breaks = seq(...), plot = FALSE)`
  - counts always sum to 272 `(test)`
  - `bins = 1` → `counts == [272]`, `breaks == [43, 96]` `(test)`
  - `bins = 9` → `counts == [16, 37, 30, 16, 14, 57, 67, 29, 6]`, identical in
    R and Python `(test)`
  - `[r]` vectors are wrapped in `I()` so a one-bin result serializes as a JSON
    array, not a scalar
- output `dist_caption` → `"272 eruptions in N bins"`
  - singular `"bin"` when `N == 1` `(test)`
  - the count is the dataset length, not the bin count
- before the client's first `bins` message
  - `[py]` `input.bins()` raises a silent exception, so neither output produces
    a value
  - `[r]` `input$bins` is `NULL` and both outputs return `NULL` explicitly —
    `req()` is deliberately not used, because its silent error still reaches
    the client console
- the server never renders an image: no plotting library, no `plotOutput`
  placeholder

## Page

- `[py]` `app.py` — Express, `set_react_page()` with no arguments
- `[py]` `app-core.py` — Core, `ReactApp(server)`; no `static_assets=` mount
- `[r]` `app.R` — `page_react()` with no arguments
- all three discover `www/ui.js` + `www/ui.css`; there is no `index.html`
- the page contains no mount container — the client appends its own `<div>` to
  `<body>`

## Client (`www/ui.js`)

- plain `React.createElement` via an `h` shorthand — no JSX, no bundler, no
  `package.json`
- pulls `React` / `ReactDOM` off `window.shinyreact` so the app shares the
  React instance that owns the hooks
- renders `null` until `useShinyInitialized()` is true `(test)`
- bins slider
  - `useShinyInput("bins", 30)` — `<input type="range">`, `min` 1, `max` 50,
    `id="bins"` `(test)`
  - the current value is echoed in an `<output class="bins-value">`
  - no explicit `debounceMs`, so the hook's 100 ms default applies
- histogram, drawn as SVG
  - one `<rect fill="#447099">` per count `(test)`
  - bar width is `max(x1 - x0 - 1, 1)` px in viewBox units, i.e. a 1px gap that
    never collapses the bar to zero width
  - viewBox is `0 0 620 380`; margins top 16, right 16, bottom 48, left 56
  - `role="img"` with `aria-label` `"Histogram of Old Faithful waiting times in
    N bins"` `(test)`
  - y axis: gridlines + labels at a 1/2/5 × 10ⁿ step chosen so ~4 ticks cover
    the max count; the axis top is the max count rounded up to that step
  - x axis: labels every 10 minutes, from the first multiple of 10 at or above
    `breaks[0]`
  - axis titles `"Waiting time to next eruption (minutes)"` and `"Frequency"`
- caption paragraph shows `dist_caption`, or a single space before the first
  value arrives (so the line does not collapse)
- loading vs. recalculating — the repo's status idiom
  - no `dist_data` value yet → a `.placeholder` div reading `"Loading…"` `(test)`
  - value present and `useShinyOutputStatus("dist_data") === "recalculating"` →
    the chart stays mounted and its wrapper gets `class="recalculating"`
    `(test)`
    - `www/ui.css` gives `.recalculating` `opacity: 0.6` with a 200 ms
      transition
  - dragging the slider therefore never unmounts and re-mounts the SVG

## Layout (`www/ui.css`)

- two-column flex layout, `max-width: 60rem`, centered; sidebar `flex: 1 1
  12rem`, panel `flex: 3 1 24rem` — wraps to one column on narrow screens
