# Shiny modules in a shinyreact app

Modules exist so one id can appear many times on a page without collision. In a
normal Shiny app the UI function calls `ns()` and the server gets namespaced ids
for free. shinyreact has no UI function, so the client supplies the namespace
instead — with `ShinyModuleProvider`.

**Both sides resolve to the same wire id, and neither needs wiring beyond
naming the namespace once.**

## The whole idea

```jsx
const { ShinyModuleProvider, useShinyInput, useShinyOutputValue } = window.shinyreact;

function Card() {                       // knows nothing about namespaces
  const [bins, setBins] = useShinyInput("bins", 30);
  const data = useShinyOutputValue("dist_data");
  ...
}

<ShinyModuleProvider namespace="left"><Card /></ShinyModuleProvider>
<ShinyModuleProvider namespace="right"><Card /></ShinyModuleProvider>
```

`Card` is written as if it owned `bins` outright. The provider turns its ids
into `left-bins` and `right-bins` on the wire, which is exactly what the
matching module server reads.

Server side, nothing is special — write an ordinary Shiny module:

```python
# [py]
from shiny import module

@module.server
def card_server(input, output, session):
    @shinyreact.reactive_output
    def dist_data():
        return histogram(input.bins())

card_server("left")
card_server("right")
```

```r
# [r]
card_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    output$dist_data <- reactive_output({
      if (is.null(input$bins)) return(NULL)
      histogram(input$bins)
    })
  })
}
card_server("left")
card_server("right")
```

Inputs, outputs, and custom messages all resolve through Shiny's normal module
resolution, so `send_message(session, "ping", ...)` inside the module reaches
the `useShinyMessageHandler("ping", ...)` inside the matching provider.

## The namespacing rules

Every id-taking hook and component goes through one shared resolver, so the
behavior is identical for `useShinyInput`, `useShinyInputValue`,
`useSetShinyInput`, `useShinyOutputValue`, `useShinyOutputStatus`,
`useShinyOutputError`, `useShinyMessageHandler`, `ShinyOutput`, and `ImageOutput`.

Each of them takes an optional `namespace`:

| `namespace` | Result |
|---|---|
| omitted (`undefined`) | the enclosing `ShinyModuleProvider`'s namespace, or no prefix when there is no provider |
| `"ns"` | prefix with `ns-`, **ignoring** any enclosing provider |
| `null` | opt out — use the bare id, even inside a provider |
| `""` | same as `null` |

Three consequences worth knowing before you debug them:

- **`null` and `undefined` are not the same thing.** Passing `null` is how you
  say "this id is already fully qualified"; leaving it off is how you say "use
  whatever module I am in". The check is `!== undefined` precisely so a `null`
  cannot silently fall through to the context.
- **The prefix is a single hyphen**: `` `${namespace}-${id}` ``. So
  `namespace="left"` + `id="bins"` is `left-bins`, matching Shiny's own `ns()`.
- **Nesting overrides rather than concatenates.** An inner
  `ShinyModuleProvider` wins outright; it does not append to the outer one. For
  a genuinely nested module, pass the combined namespace whole:
  `namespace="outer-inner"`.

## When to reach for this

Only when the *server* has modules. If you just want two of something on the
page and the server can tell them apart by id, use two ids — modules are the
answer to "the same server code runs N times", not to "I have two cards".

A common middle case: one shared filter driving several cards. That is not a
module — it is one input id read by several components (`useShinyInputValue`)
and several outputs. Reach for a module when each instance needs its **own**
copy of the server logic.

## Pitfalls

- **A provider around only part of the subtree.** Every hook that belongs to the
  module instance has to be inside it. A control lifted out to a parent silently
  writes the un-namespaced id, and the module server never sees it.
- **Namespacing an already-namespaced id.** `ImageOutput` passes `null` for its
  internal clientdata ids for this reason; if you build something similar, do
  the same rather than letting the context double-prefix.
- **Assuming the client namespace is optional.** The server's `ns()` is not
  optional, so the client's must match it exactly — `left-bins`, not `left.bins`
  or `bins`.
- **`[r]`** a `session` whose `ns()` is not callable makes `send_message()`
  abort by design. The previous silent fallback delivered messages to an
  un-namespaced id that no in-module handler matched, which is much harder to
  find than an error.
