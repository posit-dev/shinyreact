# Example 3 — Output types (shinyjsonold)

A gallery of output types over the JSON-spec bridge: numeric statistics, a data table, a matplotlib plot, and a verbatim-text display, all driven by a shared slider input filtering rows of `mtcars`.

> **Note:** Uses `shinyjsonold`. SPA-first apps generally don't need a per-output-type bridge — the client picks how to render whatever JSON the server ships. See [example 16](../16-shadcn/) for matplotlib + plotly versions of the plot pattern.

## What it shows

- `SliderCard` controls a cylinder count.
- `StatisticsCard` displays computed mean/min/max — `@shinyjson.render` returns a JSON object.
- `DataTableCard` displays the filtered rows — `@shinyjson.render` returns records.
- A matplotlib figure is rendered server-side via Shiny's standard `@render.plot` and surfaced through a shinyjsonold-registered `PlotCard` component.

## Layout

```
examples/3-outputs/
├── app.py        # Server: filter mtcars by cylinder count, render outputs
├── outputs.js    # JS bundle: SliderCard / StatisticsCard / DataTableCard / PlotCard
├── mtcars.csv
└── styles.css
```

## Run it

```bash
uv run shiny run examples/3-outputs/app.py
```
