# Serve a React `index.html` document (the `ui.tsx` pattern)

Reads a complete HTML document — the kind a Vite build emits — and
injects the shinyreact page-level dependencies into it. The document
must contain Shiny's dependency placeholder inside `<head>`:

## Usage

``` r
page_react_html(
  path = "www/index.html",
  ...,
  extra_deps = NULL,
  shinyreact_js = "server"
)
```

## Arguments

- path:

  Path to the HTML document. Defaults to `"www/index.html"`, relative to
  the working directory.

- ...:

  Ignored.

- extra_deps:

  A list of additional
  [htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html)
  objects to render at the placeholder. A complete document has no tag
  tree to attach dependencies to, so this is the only way in — the
  counterpart of
  [`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md)'s
  `...`. They render *after* Shiny's and shinyreact's, so they can rely
  on `window.shinyreact` existing. Mirrors Python's
  `page_react_html(extra_deps=)`.

- shinyreact_js:

  Who supplies `shinyreact.js` / `shinyreact.css`: `"server"` (the
  default) or `"client"` for an npm-tier app whose bundle imports
  `@posit-dev/shinyreact` — see
  [`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md).

## Value

UI suitable for `shinyApp(ui = ...)`.

## Details

    <meta name="shiny-dependency-placeholder" content="">

Shiny's and shinyreact's script/link tags render in its place. It is an
ordinary `<meta>` tag rather than template syntax, so the document stays
valid HTML that a bundler's dev server can serve unchanged. Use as the
`ui` argument: `shinyApp(ui = page_react_html(), server = ...)`.

Assets the document references (your bundle's JS/CSS) should live in
`www/`, where Shiny serves them statically.

For apps that don't need to own the HTML document, prefer
[`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md)
— it requires no HTML file at all.

## The whole document is a template

R places the dependencies with
[`htmltools::htmlTemplate()`](https://rstudio.github.io/htmltools/reference/htmlTemplate.html),
which evaluates **every** `{{ ... }}` in the document as R code —
anywhere in it, `<head>` or `<body>`, with the global environment as
parent. So a body containing `{{ 6*7 }}` renders `42`, and
`{{ nonexistent() }}` is an error at page render.

A document written for a JS templating engine that also uses `{{ }}`
(Handlebars, Mustache, Vue's text interpolation) is therefore not safe
to pass here as is — those braces will be evaluated as R. Escape them,
or use
[`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md),
which needs no HTML file at all.

Python's `page_react_html()` differs: it replaces the placeholder and
leaves the rest of the document untouched. Documented as a deliberate
divergence rather than a bug — see `FEATURES.md` and issue \#223.

## Path resolution

A relative `path` resolves against the process working directory. Under
[`shiny::runApp()`](https://rdrr.io/pkg/shiny/man/runApp.html) /
[`shiny::shinyApp()`](https://rdrr.io/pkg/shiny/man/shinyApp.html) that
is the app directory, so the default `"www/index.html"` just works. R
has no per-caller `__file__`, so unlike Python — which resolves a
relative path against the calling module's directory — there is nothing
to resolve against outside the working directory. Pass an absolute path
if you need to be independent of it.

The placeholder must be spelled exactly as above — the check is a
fixed-string match, so a differently-quoted or reordered `<meta>` tag is
rejected.
