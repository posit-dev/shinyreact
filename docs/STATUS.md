# STATUS.md

Project status: known issues, TODOs, and feature inventory.

## TODOs

### Output registry `remove()` is destructive — needs reference counting

`outputs.remove()` deletes the entire `OutputRegistryEntry` and its hidden DOM element, then schedules async `unbindAll`/`bindAll`. When React unmounts one component and mounts another in the same commit (e.g., tab switching), the new `add()` races the old `remove()`'s unbind, causing Shiny to see duplicate output bindings. The input registry already handles this correctly — `removeUseStateSetValueFn` removes one subscriber without nuking the entry. The output registry should follow the same pattern: decrement a reference count on `remove()`, only delete the DOM element and unbind when the count reaches zero. This also wouldn't help `ImageOutput`, which bypasses the registry and creates its own DOM elements. See the existing TODO in `use-shiny.ts` at line ~208.

### 7-chat requires external API key

The chat example requires `OPENAI_API_KEY` and the `chatlas` package. It cannot be smoke-tested without credentials. Consider adding a mock/echo mode for demo purposes.

### Python-side input handlers for useShinyInput values

Currently, values sent from `useShinyInput` on the JS side arrive directly as `input.xxx()` with no server-side interception. Shiny's built-in inputs (e.g., `actionButton`) use Python input handlers to validate and transform incoming values — for example, the action button handler can reject or coerce values before they reach reactive code. shinyjson should support registering Python input handlers for `useShinyInput` IDs so that the server can intercept, validate, or deny values sent from the client. This would also enable patterns like the action button's `ignore_init` behavior to be handled at the input layer rather than requiring `@reactive.event(ignore_init=True)` at every call site.

### XSS in chat example renderMarkdown (7-chat)

The `renderMarkdown()` function in `examples/7-chat/chat.js` escapes code blocks via `escapeHtml()` but passes all other text (inline code, bold, italic, plain text) as raw HTML into `dangerouslySetInnerHTML`. If the AI model returns markup like `<img src=x onerror=...>`, it will execute as script. Options: integrate a sanitization library (e.g. DOMPurify), build a React element tree instead of an HTML string, or escape-first then apply formatting. The current inline TODO at `chat.js:216` documents the risk.

### Full React page support

`useShinyInitialized` now falls back to the `shiny:connected` DOM event when `window.Shiny` is not yet available at mount time. This unblocks a future "full React page" mode where the entire page is a React app and Shiny scripts load asynchronously. Remaining work includes a dedicated page layout function (e.g. `page_react()`), ensuring all hooks and the output binding gracefully handle late Shiny arrival end-to-end, and adding an example app that demonstrates the pattern.

### JSON Patch for partial/dynamic UI updates

Explore using RFC 6902 JSON Patch operations to send incremental spec updates from Python instead of replacing the full spec each time. `@json-render/react` has an internal (unexported) `applyPatch` function that applies patch ops (`add`, `replace`, `remove`, `move`, `copy`) to a spec's flat element map. A shinyjson implementation would need: (1) a Python-side `shinyjson.patch(session, id, ops)` function that sends patches via `post_message`, (2) JS-side patch application against the current spec, and (3) Python helpers or diffing to generate correct patch ops from spec changes.

**Why not client-side diffing instead?** json-render's `ElementRenderer` receives the entire `spec` object as a prop alongside each `element`, so `React.memo` never bails out even with stabilized element references — the `spec` reference is always new. React's DOM reconciliation already handles efficient updates for typical spec sizes. The JSON Patch approach is primarily valuable for (a) reducing wire payload for large specs and (b) enabling streaming/incremental spec building (e.g., AI-generated UIs).

### Python convenience helpers for Element construction

`Element.text_input(input_id, ...)` and similar factory methods would reduce boilerplate when building specs. Deferred until component patterns stabilize across downstream packages (Approach C from the hello world decomposition design).

### Pretty helper methods to hide Spec construction

The raw `Spec(root=..., elements={...})` / `Element(type=..., props={...}, children=[...])` calls are verbose and expose internal structure. Downstream packages (and examples) should offer higher-level helpers that build the spec behind the scenes, so app authors write something closer to a component tree rather than manually assembling flat dictionaries and element IDs.

### No build step for example JS

All example JS files use `React.createElement` directly (no JSX, no bundler). This works but is verbose. A lightweight build step (e.g., esbuild with JSX) could improve readability without adding heavy tooling.

### What is the general shape of a UI component?

Define what a well-formed shinyjson UI component looks like from the downstream package author's perspective. What props should it accept? How should it compose with other components? What conventions should the JS catalog entry follow (e.g., naming, prop types, children handling)? Establishing a clear "component contract" will help downstream packages like shinyshadcn build consistent, interoperable components.

### What render methods are useful?

Evaluate which Python-side render patterns are most valuable for downstream packages. Currently `@shinyjson.render` returns `Spec` or raw JSON for `useShinyOutput`. Are there other render shapes that would be useful — e.g., rendering a single element without a full Spec, streaming partial updates, returning pre-built HTML fragments, or rendering lists of components? Understanding the useful render surface area will guide API design.

### Nested bullet structure of every feature or benefit

Create a comprehensive nested bullet list cataloging every feature and benefit shinyjson provides. This serves as a documentation source-of-truth that can later be expanded into user-facing docs, README sections, or marketing material without forgetting anything. Should cover: JS hooks and APIs, Python public API, the extension/downstream pattern, built-in examples, and architectural benefits (e.g., shared React instance, zero-component philosophy, IIFE bundling). Organizing as nested bullets makes it easy to promote sections into full doc pages later.

### Can dynamic UI be supported? Can any render output be supported, or should it always be components?

Investigate whether shinyjson can support dynamic UI patterns where the server controls what gets rendered (not just data updates to fixed components). For example: can a render function return arbitrary Shiny UI (like `ui.tags`, `ui.input_slider`, etc.) mixed with shinyjson components? Should render output always be a component tree, or could it include raw HTML, plain text, or other Shiny outputs? This has implications for how flexible the framework is versus how predictable the rendering contract remains.

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

- **HTMLDependency mtime versioning for examples.** Shiny caches static files by `{name}-{version}` in the URL. During development, editing a JS file doesn't bust the cache if the version string is fixed. Examples use `version=str(int(file.stat().st_mtime))` so the version changes whenever the file is saved. This is a development convenience only — published packages should use fixed versions.

- **Treat element keys as internal/opaque.** When using `Node`, element keys in the flat `elements` map (e.g., `"auto_001"`) are auto-generated internal plumbing. Callers can still manually construct `Spec(elements={...})` with arbitrary keys, so this is guidance rather than a hard API guarantee. These keys have no relationship to DOM IDs or Shiny input/output IDs: Shiny IDs are passed as component props (`input_id`, `output_id`) and are the only IDs the server needs to know about.

### Recent fixes

- **useShinyInput defaultValue stabilization**: Inline `{}` / `[]` defaults no longer cause infinite re-renders. The first value is captured in a `useRef` and used for the `useEffect` dependency array.
- **useShinyMessageHandler handler stabilization**: Inline arrow functions no longer cause unnecessary handler deregister/re-register cycles. Handler stored in a ref with stable wrapper.
- **ImageOutput prop**: Correct prop is `id`, not `outputId` (fixed in 5-shadcn).
- **File input (2-inputs)**: Uses `useShinyInput` to send file metadata (name, size, type) to the server instead of relying on Shiny's native file input binding.
- **Button pattern**: Buttons use `useShinyInput("id", 0)` + increment (Shiny action button pattern) with `ignore_init=True` on the server. See CLAUDE.md "Common patterns" for details.
- **Hello world decomposition**: Replaced monolithic `HelloWorldComponent` with five small registered components (`Card`, `Heading`, `TextInput`, `Divider`, `OutputDisplay`). Python now composes the full UI tree via `Spec` instead of delegating to a single JS component.
- **Button hook migration (hello-shinyjson)**: Migrated `Button` component from private Shiny internals (`window.Shiny.shinyapp.$inputValues`) to `useShinyInput` hook.
