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

