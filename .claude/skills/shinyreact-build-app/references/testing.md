# Verifying a shinyreact app

Do not stop at "the code is written". At minimum:

1. **Factor pure logic out of the app file.** Binning, formatting, conversions
   go in a module beside the app so a test can import them directly, with no
   session at all. Logic left inside `app.py` / `app.R` next to the page call
   is still reachable — `testServer()` / `test_server()` below drive the app
   itself — but only through an input, which is a slower and blunter tool than
   calling a function.
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
| `shiny::testServer()` `[r]` / `shiny.testserver.test_server()` `[py]` | the reactive graph: inputs in, `reactive_output` values out | low, and no browser |
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
    test_faithful.py     [py]  pytest — the factored logic, called directly
    test_outputs.py      [py]  pytest — the app, via test_server()
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

## Testing the server: `testServer()` `[r]`, `test_server()` `[py]`

**This is the highest-value layer for a `ui.tsx` app.** The server contains
only reactive computation, so "input X produces output Y" *is* the server, and
both languages can assert it with no browser and no client: set inputs, read
outputs, and get the JSON value the client would have received.

### `[r]` `shiny::testServer()`

`reactive_output` is an ordinary Shiny render function, so `testServer()`
drives it directly.

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

### `[py]` `shiny.testserver.test_server()`

The Python counterpart (py-shiny#2470, so newer than shiny 1.7.0). It loads the
app file — Express or Core, `shiny.App` or `shinyreact.ReactApp` — and runs its
server against a mock connection:

```python
from pathlib import Path
from shiny.testserver import test_server

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_the_histogram_recomputes_when_bins_changes():
    with test_server(APP) as ts:
        ts.set_inputs(bins=9)
        assert ts.get_output("dist_data").value["counts"] == [16, 37, 30, 16, 14, 57, 67, 29, 6]
        assert ts.get_output("dist_caption") == "272 eruptions in 9 bins"
```

`get_output()` returns a value that compares equal to the underlying one, so
assert on it directly; use `.value` when you need to index into it, and
`.status` (`"ok"` / `"error"` / `"silent"`) or `.error` to assert the
non-value outcomes. Traditional renderers are readable too, so
`@render.data_frame` / `@render_plotly` outputs mounted through `ShinyOutput`
can be checked at the wire level.

Pass an **absolute `Path`**: a relative one resolves against the test file's
directory, and the app is a directory up from `tests/`.

Four things to know, all of them shinyreact-specific:

- **An untyped input id needs no `:shinyreact.default` suffix.** The hook
  appends it on the wire, but both Python handlers are no-ops, so
  `set_inputs(bins=9)` is equivalent.
- **A typed one does.** `set_inputs(**{"when:shiny.datetime": 1756382400})` is
  what makes the handler run and `input.when()` a `datetime`; without the
  suffix you are testing a different app than the one the client drives.
- **An event input needs two calls.** `useShinyInput` registers its default at
  mount and sends the event after, so an output behind
  `@reactive.event(..., ignore_init=True)` only fires on the *second*
  `set_inputs` for that id.
- **An unset input means `status == "silent"`, not a `None` value.**
  `input.x()` raises a silent exception while unset, so a `if x is None:`
  branch in your server is unreachable from a real client — assert the status
  instead. (A *later* `req()` failure is not visible in memory at all:
  py-shiny#2492.)

Module ids can be read as the session sees them (`ts.get_output("counter-n")`)
or through a scope, which strips the namespace on the way in and out:

```python
with ts.make_scope("counter") as counter:
    counter.set_inputs(n=7)
    assert counter.get_output("label") == "n=7"
```

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
