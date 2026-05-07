# Example 6 — Multi-input dashboard (shinyreact)

A more realistic app that wires several inputs (date range, search, category checkboxes) through a server-side filter into a panel of metric cards and charts. Demonstrates how the JSON-spec bridge holds up when there's actual reactive logic behind the UI rather than one-shot echoes.

> **Note:** Uses `shinyreact`. See `DESIGN.md` §4 for why dashboards with many interconnected reactive paths are the natural sweet spot for Shiny on the server, regardless of whether the UI is rendered server-driven or `client-ui`-first.

## What it shows

- `FilterPanel` exposes three inputs (date range, search term, category list).
- `MetricsCards` and `Charts` consume the same filtered dataset.
- Server-side: `@reactive.calc filtered_data` is the single source of truth; downstream renderers depend on it. A change to any input recomputes only what's affected.

## Layout

```
examples/6-dashboard/
├── app.py         # Server: filter pipeline + render functions
├── dashboard.js   # JS bundle: DashboardApp / FilterPanel / MetricsCards / Charts
├── data.py        # Sample data generation + filter / metric helpers
└── styles.css
```

## Run it

```bash
uv run shiny run examples/6-dashboard/app.py
```
