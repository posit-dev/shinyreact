# As-is shinyreact input handler (internal)

Opt-in via `type = "shinyreact.asis"`. Returns the parsed value
completely untouched (no flattening), for nested structures the default
would coerce.

## Usage

``` r
asis_input_handler(value, session = NULL, name = NULL)
```
