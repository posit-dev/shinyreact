# Default shinyreact input handler (internal)

Applied to every untyped `useShinyInput` value. Undoes the parts of
jsonlite/shiny simplification that make R disagree with Python about the
same JSON payload. Python needs no such handler — its deserializer never
simplifies (see `pkg-py/src/shinyreact/_input_handler.py`).

## Usage

``` r
default_input_handler(value, session = NULL, name = NULL)
```

## Details

The contract, stated in terms of the JSON the React hook sent:

- **Array of objects** (`[{a: 1}, {b: 2}]`) — kept as a list of records
  This is the case shiny's default handler gets wrong.

- **Array of scalars** (`[0, 100]`, `["a", "b"]`) — flattened to an
  atomic vector, exactly as shiny does by default.

- **Empty array** (`[]`) — [`list()`](https://rdrr.io/r/base/list.html),
  matching Python's `[]`. Shiny's default yields `NULL`, conflating
  "empty" with "absent".

- **Array of arrays** (`[[1, 2], [3, 4]]`) — nesting preserved. Shiny's
  default flattens it to `c(1, 2, 3, 4)`, which destroys the shape the
  component sent.

- Anything else — returned as-is.
