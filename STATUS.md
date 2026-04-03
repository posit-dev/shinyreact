# STATUS.md

Project status: known issues, TODOs, and feature inventory.

## TODOs

### Duplicate output IDs on tab navigation (6-dashboard)

Switching away from the Dashboard tab unmounts `useShinyOutput` components. Navigating back remounts them, creating duplicate output bindings for `metrics_data`, `chart_data`, and `table_data`. Shiny shows a "Duplicate output IDs were found" client error. Needs a fix in the output registry cleanup/re-registration logic, or the Dashboard page should stay mounted (hidden) rather than unmounted.

### 7-chat requires external API key

The chat example requires `OPENAI_API_KEY` and the `chatlas` package. It cannot be smoke-tested without credentials. Consider adding a mock/echo mode for demo purposes.

### Python-side input handlers for useShinyInput values

Currently, values sent from `useShinyInput` on the JS side arrive directly as `input.xxx()` with no server-side interception. Shiny's built-in inputs (e.g., `actionButton`) use Python input handlers to validate and transform incoming values — for example, the action button handler can reject or coerce values before they reach reactive code. shinyjson should support registering Python input handlers for `useShinyInput` IDs so that the server can intercept, validate, or deny values sent from the client. This would also enable patterns like the action button's `ignore_init` behavior to be handled at the input layer rather than requiring `@reactive.event(ignore_init=True)` at every call site.

### XSS in chat example renderMarkdown (7-chat)

The `renderMarkdown()` function in `examples/7-chat/chat.js` escapes code blocks via `escapeHtml()` but passes all other text (inline code, bold, italic, plain text) as raw HTML into `dangerouslySetInnerHTML`. If the AI model returns markup like `<img src=x onerror=...>`, it will execute as script. Options: integrate a sanitization library (e.g. DOMPurify), build a React element tree instead of an HTML string, or escape-first then apply formatting. The current inline TODO at `chat.js:216` documents the risk.

### Full React page support

`useShinyInitialized` now falls back to the `shiny:connected` DOM event when `window.Shiny` is not yet available at mount time. This unblocks a future "full React page" mode where the entire page is a React app and Shiny scripts load asynchronously. Remaining work includes a dedicated page layout function (e.g. `page_react()`), ensuring all hooks and the output binding gracefully handle late Shiny arrival end-to-end, and adding an example app that demonstrates the pattern.

### Python convenience helpers for Element construction

`Element.text_input(input_id, ...)` and similar factory methods would reduce boilerplate when building specs. Deferred until component patterns stabilize across downstream packages (Approach C from the hello world decomposition design).

### Pretty helper methods to hide Spec construction

The raw `Spec(root=..., elements={...})` / `Element(type=..., props={...}, children=[...])` calls are verbose and expose internal structure. Downstream packages (and examples) should offer higher-level helpers that build the spec behind the scenes, so app authors write something closer to a component tree rather than manually assembling flat dictionaries and element IDs.

### No build step for example JS

All example JS files use `React.createElement` directly (no JSX, no bundler). This works but is verbose. A lightweight build step (e.g., esbuild with JSX) could improve readability without adding heavy tooling.

## Features

### Core infrastructure (js/src/shiny-react/)

| Feature | Status | Notes |
|---------|--------|-------|
| `useShinyInput` hook | Working | Stable defaultValue via useRef; debounce support |
| `useShinyOutput` hook | Working | Subscribes to Shiny output binding |
| `useShinyMessageHandler` hook | Working | Stable handler ref; no unnecessary re-registration |
| `ImageOutput` component | Working | Renders `@render.plot()` outputs; prop is `id` (not `outputId`) |
| `ShinyModuleProvider` | Working | Namespace support for module patterns |
| `registerComponents` | Working | Downstream packages register components at load time |
| `useShinyInitialized` hook | Working | Tracks Shiny initialization state |

### Python package (pkg-py/)

| Feature | Status | Notes |
|---------|--------|-------|
| `shinyjson.ui()` | Working | Creates output div with HTMLDependency |
| `@shinyjson.render` | Working | Renders Spec or passes raw JSON for useShinyOutput |
| `shinyjson.Spec` / `Element` | Working | Data model for component trees |
| `shinyjson.post_message()` | Working | Server-to-client custom messages |

### Examples (examples/)

| Example | Port | Status | Description |
|---------|------|--------|-------------|
| 1-hello-world | 8761 | Working | Decomposed components (Card, TextInput, Divider, OutputDisplay) composed from Python via Spec |
| 2-inputs | 8762 | Working | 10 input types (text, number, checkbox, radio, select, slider, date, button, file, batch form) |
| 3-outputs | 8763 | Working | Data table, statistics, matplotlib plot via ImageOutput |
| 4-messages | 8764 | Working | Server-to-client messaging with post_message, auto-dismissing toasts |
| 5-shadcn | 8765 | Working | Text processing, button events, matplotlib plot; shadcn look via plain CSS |
| 6-dashboard | 8766 | Working | Sidebar nav with tab switching, metrics cards, CSS bar charts, data table, filters; duplicate output ID warning on tab switch |
| 7-chat | 8767 | Needs API key | AI chat with streaming, themes, image upload; requires OPENAI_API_KEY |
| 8-modules | 8768 | Working | Three counter widgets using ShinyModuleProvider namespacing |
| 9-blended | 8770 | Working | Tabbed sidebar layout, matplotlib plot, data table, settings panel |

### Design decisions

- **Element keys are always auto-generated.** The element key in `@json-render/react`'s flat `elements` map (e.g., `"auto_001"`) is internal plumbing — it has no relationship to DOM IDs or Shiny input/output IDs. Shiny IDs are passed as component props (`input_id`, `output_id`) and are the only IDs the server needs to know about. Exposing element keys to users would conflate two unrelated identity systems and add API surface for no benefit.

### Recent fixes

- **useShinyInput defaultValue stabilization**: Inline `{}` / `[]` defaults no longer cause infinite re-renders. The first value is captured in a `useRef` and used for the `useEffect` dependency array.
- **useShinyMessageHandler handler stabilization**: Inline arrow functions no longer cause unnecessary handler deregister/re-register cycles. Handler stored in a ref with stable wrapper.
- **ImageOutput prop**: Correct prop is `id`, not `outputId` (fixed in 5-shadcn).
- **File input (2-inputs)**: Uses `useShinyInput` to send file metadata (name, size, type) to the server instead of relying on Shiny's native file input binding.
- **Button pattern**: Buttons use `useShinyInput("id", 0)` + increment (Shiny action button pattern) with `ignore_init=True` on the server. See CLAUDE.md "Common patterns" for details.
- **Hello world decomposition**: Replaced monolithic `HelloWorldComponent` with five small registered components (`Card`, `Heading`, `TextInput`, `Divider`, `OutputDisplay`). Python now composes the full UI tree via `Spec` instead of delegating to a single JS component.
- **Button hook migration (hello-shinyjson)**: Migrated `Button` component from private Shiny internals (`window.Shiny.shinyapp.$inputValues`) to `useShinyInput` hook.
