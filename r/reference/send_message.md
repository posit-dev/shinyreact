# Send a custom message to client React components

Messages are consumed by `useShinyMessageHandler(id, handler)` on the
React side. The `id` is namespaced to the current Shiny module (if any)
so module-scoped handlers match, just like input/output ids.

## Usage

``` r
send_message(session, id, data)
```

## Arguments

- session:

  The Shiny session.

- id:

  Message id; must match the `id` passed to `useShinyMessageHandler()`
  in the React component.

- data:

  Any JSON-serializable data.

## Value

Invisibly `NULL`.
