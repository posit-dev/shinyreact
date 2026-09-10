# HTML dependency for a downstream package's own JS/CSS bundle

Convenience mirroring Python's `page_react_dep()`. It is versioned by
the JS file's mtime, so the `/lib/{name}-{version}/` URL changes on
every rebuild and the browser re-fetches. That is what you want while
developing and the wrong thing for a published package — an mtime is
whatever the install happened to write, so it is neither stable across
machines nor meaningful to a reader. There is no `version` argument on
purpose: a package shipping a fixed version should build its own
[htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html)
(the same advice as for a classic, non-module bundle), which is five
lines and leaves nothing about the dependency implicit.

## Usage

``` r
page_react_dep(
  src_dir,
  js_file = "ui.js",
  css_file = "ui.css",
  name = basename(src_dir)
)
```

## Arguments

- src_dir:

  Directory containing the JS/CSS. Required; Python infers this from the
  calling module's `__file__` when omitted, which R has no equivalent
  of.

- js_file:

  JS filename within `src_dir`. Defaults to `"ui.js"`, matching Python;
  attached only if the file exists.

- css_file:

  CSS filename within `src_dir`. Defaults to `"ui.css"`, matching
  Python; attached only if the file exists. `NULL` to skip.

- name:

  Dependency name; defaults to `basename(src_dir)`.

## Value

An
[htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html).

## Details

The script tag is emitted as `type="module"`. A classic `<script defer>`
tag throws on the bundle's first `import`. `type="module"` is implicitly
deferred, so no `defer` attribute is needed. If your bundle is a classic
(non-module) script, build an
[htmltools::htmlDependency](https://rstudio.github.io/htmltools/reference/htmlDependency.html)
directly instead of using this helper.

Both the script and the stylesheet are attached only when the file
exists inside `src_dir`, so a bundle that ships no CSS — or that has not
been built yet — does not emit a tag pointing at a 404. Pass
`css_file = NULL` to never attach a stylesheet. A missing `js_file`
warns, since it is the entry point and an empty dependency would
otherwise fail silently.
