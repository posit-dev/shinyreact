# 13-bookmarking

Demonstrates bookmark restoration in shinyreact:

- `page_react()` (via `_dep_page()`) emits a `<script>` in `<head>` carrying the
  restored input values when Shiny parses a bookmark query string.
- The shinyreact bundle batch-seeds the input registry on init, so
  `useShinyInput` returns the restored value as its initial render value.

## Try it

```
shiny run examples/app-py/13-bookmarking/app.py
```

1. Change the text, number, and checkbox.
2. Click **Bookmark** — the URL changes to include the inputs as a query
   string.
3. Copy the URL into a new tab — the inputs initialise from the URL.

## Bookmark modes

This example uses `bookmark_store="url"`, which encodes inputs into the URL
itself. Switch the call to `bookmark_store="server"` to test the
server-stored variant; the same restoration mechanism applies.

> **Security:** bookmarked input values appear in the rendered HTML page
> source. Do not place credentials, tokens, or PII into inputs that
> participate in bookmarking.
