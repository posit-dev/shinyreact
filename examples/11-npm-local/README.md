# 11-npm-local — the npm tier with nothing else on the page

The Old Faithful app again ([01-hello](../01-hello/) does it with no build
step), rebuilt to show the smallest possible npm-tier app: the client imports
`@posit-dev/shinyreact` and the server sends **no shinyreact JS and no
`#shinyreact-config` tag at all**.

## What is different here

[09-hmr](../09-hmr/) is the other npm-tier example, and it uses
`set_react_page(shinyreact_js="client")` — a page entry point that still emits
the config tag (it carries the protocol version, and bookmark restore rides on
it). This app needs neither, so its whole page is:

```python
ui = page_bare(page_react_dep(src_dir=_APP_DIR / "www", name="npm-local"))
```

```r
ui <- page_bare(page_react_dep("www", name = "npm-local"))
```

Shiny's own dependencies plus this app's bundle. That means the page has

- **no `shinyreact.js`** — no second copy of React and the hooks, and no
  duplicate `shinyReactMessage` handler;
- **no `#shinyreact-config` tag, so no protocol handshake** — nothing on the
  page is versioned separately from the app that shipped it.

Bookmark restore *does* travel through the config tag, so an app that bookmarks
wants `page_react()` instead. This app does not bookmark.

The hooks come from an import, not from `window.shinyreact`:

```jsx
import { useShinyInput, useShinyOutputValue } from "@posit-dev/shinyreact";
```

That package comes from npm like any other dependency, so nothing in this repo
has to be built before `npm install` — copy this directory anywhere and it
works. See [09-hmr](../09-hmr/) for how to point it at a local `pkg-js/`
instead while developing the library.

## Run it

```bash
shiny run app.py                 # Python — builds the bundle on first run
```

`app.R` does not build anything, so build once before running it:

```bash
npm install
npm run build                    # → www/ui.js, www/ui.css

Rscript -e 'shiny::runApp(".")'  # R
```

`npm run dev` rebuilds on change; reload the page to see it (no HMR here —
that is [09-hmr](../09-hmr/)).

## Tests

```bash
pytest                          # tests/test_page.py
Rscript -e 'shiny::runTests()'  # tests/testthat/test-page.R
```

Both assert the same thing in each language: the page carries this app's
dependency and no shinyreact one, and has no config tag.
