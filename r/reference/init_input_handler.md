# Init shinyreact input handler (internal)

Registered in `.onLoad()` (zzz.R) for the `shinyreact.init` input type;
shiny invokes it when the JS bundle's single per-session
`.shinyreact_init:shinyreact.init` ping arrives (sent after Shiny
initializes – `pkg-js/src/dep-discovery.ts`). Its job is per-session
bootstrap: installing automatic output dependency discovery
(dep-discovery.R). The hook is installed before the ping's own reactive
flush runs, so that same flush performs the first dependency harvest –
`server()` has already registered its outputs by then. A dedicated
handler keeps the value-transforming handlers above pure, and the
guaranteed ping means every session bootstraps exactly once, with or
without other inputs.

## Usage

``` r
init_input_handler(value, session = NULL, name = NULL)
```
