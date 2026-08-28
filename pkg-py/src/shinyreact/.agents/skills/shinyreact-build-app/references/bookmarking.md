# Bookmarking

**Bookmarking** — opt in on the server and the client needs no code at all:

```python
# [py] -- ReactApp builds the UI per request, which is what makes restore work
app = ReactApp(server, bookmark_store="url")
```
```r
# [r] -- Shiny's own bookmarking; the UI must be a function of the request,
# so each visit gets its own restore context
shinyApp(ui = function(req) page_react(), server, enableBookmarking = "url")
```

Trigger it from an action-button input (`[py]` `await session.bookmark()`,
`[r]` `session$doBookmark()`), which rewrites the browser URL. On a later visit to that URL the page entry point
embeds the saved values in the page, and the client seeds `useShinyInput`
initial values from them **before the first paint** — so a bookmarked link
renders restored state directly, with no flash of the defaults and no
`useEffect` to write.

Two things follow from that: your `useShinyInput` defaults are only used when
there is nothing to restore, and **restored values appear in the page source**,
which is inherent to the mechanism — do not bookmark anything secret.
