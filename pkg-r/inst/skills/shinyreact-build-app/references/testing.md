# Verifying a shinyreact app

Do not stop at "the code is written". At minimum:

1. **Factor pure logic out of the app file.** Binning, formatting, conversions
   go in a module beside the app so a test can import them; logic sitting
   inside `app.py` / `app.R` next to the page call cannot be reached at all.
2. **Write down what the app does, in plain English, before the tests** — a
   behavior file beside the app, one atomically checkable claim per line
   ("the caption reads `N eruptions in M bins`, singular `bin` at M=1"). An
   agent that writes the client and then writes the client's tests is agreeing
   with itself; both artifacts encode the same misunderstanding. A description
   a human can falsify at a glance is what breaks that loop.
3. **Test against that description**, at whichever of these layers is cheapest:

| Layer | Proves | Cost |
|---|---|---|
| pure functions in their own module | binning, formatting, conversions | trivial — always do this |
| `[r]` `shiny::testServer()` | the reactive graph: inputs in, `reactive_output` values out | low, and no browser |
| the client mounted in jsdom against a fake Shiny | rendering, input wiring, wire ids, status handling | low, and it exercises the file the app ships |
| Playwright | layout, real Shiny, real bindings | high; reserve for what the others cannot see |

## Where the tests live

Beside the app, and runnable **from the app directory** — someone sitting in
the app should not need your repo's tooling:

```
myapp/
  app.py / app.R
  faithful.py            the factored logic
  www/ui.js
  tests/
    test_faithful.py     [py]  pytest
    testthat.R           [r]   runner: library(testthat); test_dir("testthat")
    testthat/
      test-histogram.R   [r]
    ui.test.ts           [js]
```

```bash
pytest                                 # [py] from the app directory
Rscript -e 'shiny::runTests()'         # [r] also shinytest2::test_app()
```

`[r]` The two-file `tests/testthat.R` + `tests/testthat/` split is not a
convention you can skip: it is the layout `shiny::runTests()` and
`shinytest2::test_app()` look for. Put the tests directly in `tests/` and
neither finds them.

`[py]` A test that imports the app's own module needs the app directory on the
path, because pytest's rootdir is `tests/`:

```python
EXAMPLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE))

from faithful import histogram, waiting  # noqa: E402
```

## `[r]` Testing the server with `testServer()`

`reactive_output` is an ordinary Shiny render function, so `shiny::testServer()`
drives it with no browser and no client: set inputs, read outputs, and get the
JSON value the client would have received.

```r
test_that("the histogram recomputes when bins changes", {
  server <- function(input, output, session) {
    output$dist_data <- reactive_output({
      if (is.null(input$bins)) return(NULL)
      histogram(waiting, input$bins)
    })
  }

  shiny::testServer(server, {
    session$setInputs(bins = 9)
    expect_equal(output$dist_data$counts, c(16, 37, 30, 16, 14, 57, 67, 29, 6))

    session$setInputs(bins = 1)
    expect_equal(sum(output$dist_data$counts), 272)
  })
})
```

`output$id` is the value itself — no spec wrapper, no coercion — so assert on
it directly. This is the cheapest way to pin "input X produces output Y",
which is most of what a shinyreact server does.

Module servers work the same way: `testServer(card_server, args = list(id =
"left"), { ... })`.

**`[py]` has no `testServer()` equivalent.** Cover the Python server by
factoring its logic into a module and testing that with pytest, and let the
jsdom and Playwright layers cover the wiring. This is a real gap, not an
oversight in your app.

## The jsdom layer — mount the client the app ships

Evaluate the real `www/ui.js` against a fake `window.Shiny` (`setInputValue`
recording to an array, `bindAll`/`unbindAll` stubs) rather than importing the
component — a test that imports a component the app does not use is testing
nothing. It also lets you assert the **wire id**, including any `:type` suffix,
which is the contract the server actually sees.

Three traps cost real time:

- **`fireEvent.change`, not `el.dispatchEvent(new Event("change"))`.** React
  tracks the native value setter, so a raw event on a directly-assigned `value`
  is silently ignored. (`onInput` works either way.)
- **Debounce is real.** Nothing is on the wire immediately after mount — wait
  out the 100 ms default. And two actions in one tick coalesce *even at
  `debounceMs: 0`*, so to prove "no coalescing" put a real gap between them.
- **jsdom has no layout and runs no bindings**, so anything reading geometry,
  and anything a widget draws, is out of reach. For `ShinyOutput` the testable
  contract is the host element's shape — tag, id, classes.

A client built by Vite is a build artifact, so `www/ui.js` may be gitignored
and absent on a clean checkout. Build before testing, or test the source
component instead and accept that it is one step removed from what ships.
