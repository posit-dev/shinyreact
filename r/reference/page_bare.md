# Bare HTML page with Shiny dependencies

Escape hatch for custom setups. Wraps
[`shiny::bootstrapPage()`](https://rdrr.io/pkg/shiny/man/bootstrapPage.html).

## Usage

``` r
page_bare(..., title = NULL, lang = "en")
```

## Arguments

- ...:

  Child tags or
  [htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html)
  objects. Named arguments pass through to
  [`shiny::bootstrapPage()`](https://rdrr.io/pkg/shiny/man/bootstrapPage.html)
  — including its own `theme`. Deliberately not surfaced as named
  parameters: in the `ui.tsx` pattern the client owns styling, so
  Bootstrap theming is a passthrough, not part of this API. Mirrors
  Python's `page_bare(**kwargs)`.

- title:

  Page title.

- lang:

  HTML `lang` attribute.

## Value

A `shiny.tag` page.

## Details

With no `theme`, the page carries **no Bootstrap**: only jQuery, Shiny's
own JS/CSS, and a `width=device-width` viewport meta tag. Shiny's own
default would attach Bootstrap 3 (plus its accessibility plugin, which
errors against a newer jQuery), and in the `ui.tsx` pattern the client
owns styling. Pass a `theme` — e.g. `theme = bslib::bs_theme()`, or
`bslib::bs_theme(version = 3)` for the classic stack — to get Bootstrap
back; then `...` is a plain passthrough to
[`shiny::bootstrapPage()`](https://rdrr.io/pkg/shiny/man/bootstrapPage.html).
