# 10-bookmarking

Demonstrates bookmark restoration in shinyreact:

- `page_react()` emits the `#shinyreact-config` tag in `<head>` carrying the restored
  input values when Shiny parses a bookmark query string. The UI is a
  function of `request` so the page re-renders per request and sees the
  active RestoreContext.
- The shinyreact bundle batch-seeds the input registry on init, so
  `useShinyInput` returns the restored value as its initial render value.

## Try it

```
shiny run examples/10-bookmarking/app.py
```

1. Change the text, number, and checkbox.
2. Click **Bookmark** — the URL changes to include the inputs as a query
   string.
3. Copy the URL into a new tab — the inputs initialise from the URL.

## Register an `on_bookmarked()` callback

```python
session.bookmark.on_bookmarked(session.bookmark.update_query_string)
```

When an app has no `on_bookmarked()` callback, Shiny shows the bookmark URL in a
Bootstrap modal. `page_react()` loads no Bootstrap, so that modal cannot open
(the browser console says so). Register your own callback: this one writes the
URL to the address bar. In R:

```r
onBookmarked(function(url) updateQueryString(url))
```

## Bookmark modes

This example uses `bookmark_store="url"`, which encodes inputs into the URL
itself. Switch the call to `bookmark_store="server"` to test the
server-stored variant; the same restoration mechanism applies.

> **Security:** bookmarked input values appear in the rendered HTML page
> source. Do not place credentials, tokens, or PII into inputs that
> participate in bookmarking.
