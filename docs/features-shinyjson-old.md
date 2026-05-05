# Features — `shinyjsonold` (JSON-spec)

The original `shinyjson` package, renamed to `shinyjsonold`. Server emits JSON specs that the client renders via `@json-render/react`. Lives at `pkg-py/src/shinyjsonold/`. Examples 1–9 use this package. See `features.md` for the new SPA-first `shinyjson`.

## Python public API (`pkg-py/src/shinyjsonold/`)

| Feature | Status | Notes |
|---------|--------|-------|
| `shinyjsonold.ui_output()` | Working | Creates output div with HTMLDependency; accepts `extra_deps` |
| `shinyjsonold.page_react()` | Working | Full-page React app with `#root` + the shinyjson HTMLDependency |
| `shinyjsonold.page_bare()` | Working | Bare HTML page wrapper |
| `@shinyjsonold.render` | Working | Renders `Spec` or passes raw JSON for `useShinyOutput` |
| `shinyjsonold.Spec` / `Element` | Working | Flat-map data model for component trees |
| `shinyjsonold.Node` | Working | Nested tree API; `.to_spec()` auto-flattens to `Spec` |
| `shinyjsonold.post_message()` | Working | Server-to-client custom messages |

## Examples

| Example | Port | Status | Description |
|---------|------|--------|-------------|
| 1-hello-world | 8761 | Working | Decomposed components (Card, TextInput, Divider, OutputDisplay) composed from Python via Spec |
| 2-inputs | 8762 | Working | 10 input types (text, number, checkbox, radio, select, slider, date, button, file, batch form) |
| 3-outputs | 8763 | Working | Data table, statistics, matplotlib plot via ImageOutput |
| 4-messages | 8764 | Working | Server-to-client messaging with post_message, auto-dismissing toasts |
| 5-shadcn | 8765 | Working | Text processing, button events, matplotlib plot; shadcn look via plain CSS |
| 6-dashboard | 8766 | Working | Sidebar nav with tab switching, metrics cards, CSS bar charts, data table, filters |
| 7-chat | 8767 | Needs API key | AI chat with streaming, themes, image upload; requires OPENAI_API_KEY |
| 8-modules | 8768 | Working | Three counter widgets using ShinyModuleProvider namespacing |
| 9-blended | 8770 | Working | Tabbed sidebar layout, matplotlib plot, data table, settings panel |
| 10-spa-hello | — | Prototype | Early SPA exploration; superseded by 13-spa-hello |
| 11-columns-traditional | — | Prototype | Traditional `render.ui`-driven columns demo (the "before" half of the SPA comparison) |
| 12-columns-spa | — | Prototype | Earlier SPA rebuild of the columns demo on `shinyjsonold`; superseded by 14-columns-new-spa |

## Design decisions

- **Treat element keys as internal/opaque.** When using `Node`, element keys in the flat `elements` map (e.g., `"auto_001"`) are auto-generated internal plumbing. Callers can still manually construct `Spec(elements={...})` with arbitrary keys, so this is guidance rather than a hard API guarantee. These keys have no relationship to DOM IDs or Shiny input/output IDs: Shiny IDs are passed as component props (`input_id`, `output_id`) and are the only IDs the server needs to know about.
- **HTMLDependency mtime versioning for examples.** Shiny caches static files by `{name}-{version}` in the URL. During development, editing a JS file doesn't bust the cache if the version string is fixed. Examples use `version=str(int(file.stat().st_mtime))` so the version changes whenever the file is saved. Development convenience only — published packages should use fixed versions.
- **Downstream extension.** Downstream packages (e.g. `shinyshadcn`) ship their own IIFE bundle that calls `window.shinyjson.registerComponents(catalog, registry)` at load time, plus a Python render subclass with `extra_deps = [...]` and an overridden `transform()`.
