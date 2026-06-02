# ui-tsx-r/01-hello

R port of `examples/ui-tsx/01-hello`. Demonstrates the **`ui.tsx` pattern**:
the React UI lives entirely in `www/` (a static `index.html` + `app.js`) and is
bootstrapped via `page_react_html("www/index.html")`. The Shiny server only
contains reactive computation — `render_react` outputs for `txtout_title` and
`txtout_count`, wired to `useShinyOutputValue` calls in the client.
