# Create a React page from conventional assets — no HTML file required

The zero-configuration page for the `ui.tsx` pattern: the server emits
no body HTML at all. Attaches the shinyreact bundle plus your app's
entry assets, discovered at `www/ui.js` and `www/ui.css` (relative to
the working directory — the app directory under
[`shiny::runApp()`](https://rdrr.io/pkg/shiny/man/runApp.html)). Your JS
owns the DOM: create and append your own mount container, e.g.
`ReactDOM.createRoot(document.body.appendChild(document.createElement("div")))`.

## Usage

``` r
page_react(
  ...,
  src_dir = "www",
  js_file = "ui.js",
  css_file = "ui.css",
  title = NULL,
  lang = "en",
  shinyreact_js = "server"
)
```

## Arguments

- ...:

  Extra children or
  [htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html)
  objects.

- src_dir:

  Directory containing the assets. Defaults to `"www"`, relative to the
  working directory.

- js_file:

  JS entry filename within `src_dir`. Defaults to `"ui.js"`.

- css_file:

  CSS filename within `src_dir`. Defaults to `"ui.css"`.

- title:

  Page title. Defaults to the app folder's name (`src_dir`'s parent when
  `src_dir` is a `www` directory), or `"shinyreact-app"` when that
  resolves to nothing usable.

- lang:

  HTML `lang` attribute.

- shinyreact_js:

  Who supplies `shinyreact.js` (and `shinyreact.css`) to the page.
  `"server"` (the default) serves them from the shinyreact package as an
  [htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html)
  — what a no-build app needs, and what makes `window.shinyreact` exist.
  `"client"` is for an app whose own bundle imports
  `@posit-dev/shinyreact` and therefore ships its own copy; serving them
  too would put two copies of React and the hooks on one page. The
  `#shinyreact-config` tag is emitted either way; the npm-tier client
  hard-errors without it. Mirrors Python's `page_react(shinyreact_js=)`.

## Value

UI suitable for `shinyApp(ui = ...)`.

## Details

`ui.js` is required (a missing file warns, pointing at the resolved
path); `ui.css` is attached only when it exists. Both are served as an
[htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html)
versioned by `ui.js`'s mtime, so the browser re-fetches after every edit
— unlike raw `<script src=...>` tags in a hand-written HTML file, which
the browser caches.
