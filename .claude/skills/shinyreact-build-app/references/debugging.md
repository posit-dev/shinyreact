# Debugging a shinyreact app

The client is a normal React app, so React DevTools works. What is specific to
shinyreact is the wire, and these four hooks are the instruments — reach for
them before adding `console.log`:

| Hook | Tells you |
|---|---|
| `useShinyInitialized()` | whether the WebSocket handshake finished at all |
| `useShinyOutputStatus(id)` | `"pending"` / `"ready"` / `"recalculating"` / `"error"` for one output |
| `useShinyBusy()` | whether the server is processing *anything* right now |
| `useShinyInputValue(id)` | what a channel currently holds, read from any component |

Symptoms, in the order they actually come up:

| Symptom | Almost always |
|---|---|
| every hook returns `undefined` / nothing renders | two React copies — the Vite build is missing `external` + `globals` |
| the browser shows old behavior | stale `www/ui.js`; re-run the build |
| a page with no content at all | `www/ui.js` was not found — check it sits beside the app and the server logged no warning |
| an output stays `"pending"` forever | no server output with that exact id, or the server errored before its first value |
| the server never sees an input | it is debounced (100 ms), or the id has a `type` on one side and not the other |
| a click is dropped | the default 100 ms debounce coalesced it — use `debounceMs: 0, priority: "event"` |
| a widget renders 0×0 or not at all | `ShinyOutput` with the wrong tag/class for that binding, or `ImageOutput` with no CSS size |
| values reappear after reload | a bookmark restore is seeding initial values from the URL |

On the server, `reactive_output` is an ordinary Shiny output — print inside it,
and its errors surface in the Shiny console exactly as usual.

