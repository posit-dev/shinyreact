# Hosting a traditional Shiny renderer

Two components do this, and neither needs a `*Output()` placeholder on the
server — that is the whole point. Keep the render function exactly as you would
write it in a normal Shiny app; the client says where it goes.

**`ShinyOutput`** — for a widget that owns its own DOM (data frames, plotly,
DT, leaflet). You are rendering the element that widget's *binding* looks for,
so how you spell it is per-widget and not guessable — copy it from the widget's
own `*Output()` function:

```jsx
// custom-element widgets: name the tag
<ShinyOutput id="my_table" tagName="shiny-data-frame" />

// classic bindings: a div carrying the binding's classes (tagName defaults to "div")
<ShinyOutput id="scatter" className="shiny-ipywidget-output" />
<ShinyOutput id="scatter" className="plotly html-widget html-widget-output" />
```

It renders that element with the `ref` directly on it — **no wrapper div**, so
your flex/grid CSS behaves — and runs Shiny's `bindAll` / `unbindAll` around
it. Any other prop is forwarded to the element, and children act as fallback
content until Shiny renders into it. The widget's binding JS and CSS are
discovered from the render function and delivered for you.

**`ImageOutput`** — for a server-drawn image (`[py]` `@render.plot`,
`[r]` `renderPlot()`). It measures itself and reports the size to the server, so
the plot is drawn at the element's dimensions rather than scaled after the fact,
and it shows a spinner placeholder before the first image arrives:

```jsx
<ImageOutput id="my_plot" className="h-80 w-full" />
```

**It must be given a size**, by `className`, by `width`/`height`, or by
surrounding CSS. With no size it measures 0×0 and the server never renders.
Resizes are watched and debounced (400 ms).

Reach for `reactive_output` + your own chart whenever the client *could* draw
it — you get a real React component instead of a server-rendered PNG. Use these
two when the server genuinely must draw (matplotlib/ggplot specifics) or when a
widget already exists and re-implementing it is not the job.

## Hosting a real Shiny *input* widget

Sometimes you need the genuine article — a real ionRangeSlider, a real
selectize — because the port has to look widget-for-widget identical to the
original app. `ShinyOutput` alone will not do it: it calls only
`Shiny.bindAll()`, and an input binding also needs its `initialize()` pass plus
the widget's own JS/CSS dependency (ion-rangeslider, selectize) on the page.

Shiny's dynamic-UI output does all three. Render the widget server-side and
host the holder in the client:

```python
@render.ui                        # [r] output$widgets <- renderUI({ ... })
def widgets():
    return ui.input_slider("bins", "Bins", min=1, max=50, value=9)
```

```jsx
<ShinyOutput id="widgets" className="shiny-html-output" />
```

Shiny's html-output binding calls `renderContent()`, which loads the
dependencies and then runs `initializeInputs()` *and* `bindAll()`. So
`input.bins()` / `input$bins` arrives exactly as in a classic app, and
`update_slider()` / `updateSliderInput()` keeps working against the id — once
the holder has rendered; see below.

This is a deliberate exception, not the default — React-owned state through
`useShinyInput` / `useSetShinyInput` is still how you build inputs. Use the
holder when pixel-identical widgets matter more than owning the state.

## Two things that break only once a widget is hosted

Both are Shiny's own behavior, not shinyreact's — a plain `output_ui()` /
`uiOutput()` app with no React anywhere hits them identically. The holder
recipe above just makes them easy to walk into.

**An update sent before the holder has rendered goes nowhere.** The widget
does not exist, server or client, until its `@render.ui` / `renderUI()` has
actually run. An update reaching Shiny before that targets an id Shiny does
not know about yet and is dropped: no error, no warning, the widget simply
starts at its own initial value.

```python
@reactive.effect                      # [r] observe({
def _():                              # [r]   updateSliderInput(session, "bins", value = 30)
    ui.update_slider("bins", value=30)  # [r] })
```

A hosted widget makes the race easy to hit, since the render now waits on a
React commit as well. Prefer putting the value in the widget's own call
(`ui.input_slider("bins", "Bins", 1, 50, value=30)`); reach for `update_*`
only for a value you do not know until after the widget already exists.

**A holder that starts hidden never renders at all.** Shiny suspends a
`@render.ui` / `renderUI()` output while nothing on screen is asking for it,
and a `ShinyOutput` inside a closed accordion, a non-default tab, or any
`display: none` container counts as not asked for — even though the element
itself has mounted. The render function never runs, the widget stays blank
indefinitely, and nothing in the console says why.

```python
# [py] Express
session.output(suspend_when_hidden=False)(widgets)

# [py] Core: @output(suspend_when_hidden=False) above @render.ui
# [r]  outputOptions(output, "widgets", suspendWhenHidden = FALSE)
```

Set it on every hosted widget that can start outside the visible panel.

