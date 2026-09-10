# Publish a reactive value to a shinyreact client (the `ui.tsx` pattern)

Server-side counterpart to `useShinyOutputValue()`. Assign to
`output[[id]]`; a React client reads the value by id. There is no UI
placeholder — the client owns all UI. Accepts any JSON-serializable
value (passed through unchanged).

## Usage

``` r
reactive_output(expr, env = parent.frame(), quoted = FALSE)
```

## Arguments

- expr:

  An expression returning a JSON-serializable value.

- env:

  The environment in which to evaluate `expr`.

- quoted:

  Is `expr` already quoted?

## Value

A Shiny render function.
