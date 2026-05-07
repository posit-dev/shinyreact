# Example 2 — Input types (shinyreact)

A gallery of every Shiny input type used through the JSON-spec bridge: text, number, slider, checkbox, radio buttons, select, action button, and date picker. Each input is paired with an output that echoes its current value, so you can see the round-trip latency for each.

> **Note:** Uses `shinyreact` (the JSON-spec package). For the `ui.tsx`-first equivalent of this kind of demo, write a React app that mounts shadcn or any other component library — see [04-shadcn](../../ui-tsx/04-shadcn/).

## What it shows

Cards registered in `inputs.js` and instantiated from the server via `shinyreact.Node`:

- `TextInputCard`, `NumberInputCard`, `SliderCard`, `CheckboxCard`, `RadioCard`, `SelectCard`, `ActionButtonCard`, `DateInputCard`.

Each card wraps a `useShinyInput` hook on the client and pairs with a `@shinyreact.reactive_output` function on the server that just returns the value (or a derived string).

## Layout

```
examples/app-py/02-inputs/
├── app.py        # Server: renders a PageLayout → Node tree of input cards
├── inputs.js     # JS bundle: registers the eight input-card components
└── styles.css
```

## Run it

```bash
uv run shiny run examples/app-py/02-inputs/app.py
```
