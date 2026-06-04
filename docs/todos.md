# TODOs

Known issues and open work items. See `features.md` for what already exists.

## Safeguard `reactive_output` against use outside the `ui.tsx` pattern

`shinyreact.reactive_output` is designed to deliver values to `useShinyOutputValue()` hooks inside a `ui.tsx` app configured with `set_react_page()`. If used in a standard Shiny app (with `ui.output_text()` or other server-rendered UI elements), it will silently send a JSON payload that no client-side binding consumes. Add a runtime check (or session-level marker on `set_react_page()`) so `reactive_output` errors clearly when used outside the `ui.tsx` context.

## Discourage non-`reactive_output` / non-plot renderers in `ui.tsx` apps

`useShinyOutputValue` accepts whatever payload any Shiny renderer ships. For primitives (`@render.text` returning a string) this happens to work, but renderers like `@render.table` send pre-rendered HTML across the wire — wasteful and defeats the `ui.tsx` model. The principle is: **send the minimal data; let the client handle presentation**. For tabular data, the right pattern is `@reactive_output` returning rows/columns, then TanStack Table (or similar) on the client. Consider:

- A warning or error when a non-`reactive_output` (and non-`render.plot`) renderer is bound to an output consumed by `useShinyOutputValue`.
- Documentation guidance on which renderers are appropriate in `ui.tsx` mode.
- Possibly a registry of "approved" renderers (`reactive_output`, `render.plot`, future `render.image`, etc.) with everything else flagged.

## Clarify the two output paradigms in documentation

`ui.tsx` apps now have two distinct output mechanisms:

- `@reactive_output` + `useShinyOutputValue(id)` — server sends pure data, React component renders it. Best for custom UI where the client owns presentation.
- `<ShinyOutput id class />` — traditional Shiny output binding owns the container's DOM. Best for existing widget ecosystems (htmlwidgets, data-frame, etc.) where the binding handles rendering.

Document guidance on when to use which. The principle remains: prefer `reactive_output` + client rendering when possible (avoids shipping pre-rendered HTML), but `ShinyOutput` is the legitimate path for leveraging existing output bindings without rewriting them as React components.

## 07-chat requires external API key

The chat example requires `OPENAI_API_KEY` and the `chatlas` package. It cannot be smoke-tested without credentials. Consider adding a mock/echo mode for demo purposes.

## XSS in chat example renderMarkdown (07-chat)

The `renderMarkdown()` function in `examples/app-py/07-chat/chat.js` escapes code blocks via `escapeHtml()` but passes all other text (inline code, bold, italic, plain text) as raw HTML into `dangerouslySetInnerHTML`. If the AI model returns markup like `<img src=x onerror=...>`, it will execute as script. Options: integrate a sanitization library (e.g. DOMPurify), build a React element tree instead of an HTML string, or escape-first then apply formatting. The current inline TODO at `chat.js:216` documents the risk.

## Full React page support

`page_react()` and `page_bare()` are now exported. `page_react()` creates a full-page React app with a `#root` div and the shinyreact HTMLDependency. Remaining work:
- End-to-end example app demonstrating the full React `ui.tsx` pattern.
- Ensure all hooks and the output binding gracefully handle late Shiny arrival.

## No build step for example JS

All example JS files use `React.createElement` directly (no JSX, no bundler). This works but is verbose. A lightweight build step (e.g., esbuild with JSX) could improve readability without adding heavy tooling.

## What is the general shape of a UI component?

Define what a well-formed `shinyreact` UI component looks like from the downstream package author's perspective. What props should it accept? How should it compose with other components? What conventions should the JS catalog entry follow (e.g., naming, prop types, children handling)? Establishing a clear "component contract" will help downstream packages like `shinyshadcn` build consistent, interoperable components.

## What render methods are useful?

Evaluate which Python-side render patterns are most valuable for downstream packages. Currently `@shinyreact.render_react` returns a `Spec`/`Node` tree (app.py pattern) and `@shinyreact.reactive_output` returns raw JSON for `useShinyOutputValue` (ui.tsx pattern). Are there other render shapes that would be useful — e.g., rendering a single element without a full Spec, streaming partial updates, returning pre-built HTML fragments, or rendering lists of components? Understanding the useful render surface area will guide API design.

## Nested bullet structure of every feature or benefit

Create a comprehensive nested bullet list cataloging every feature and benefit `shinyreact` provides. This serves as a documentation source-of-truth that can later be expanded into user-facing docs, README sections, or marketing material without forgetting anything. Should cover: JS hooks and APIs, Python public API, the extension/downstream pattern, built-in examples, and architectural benefits (e.g., shared React instance, zero-component philosophy, IIFE bundling). Organizing as nested bullets makes it easy to promote sections into full doc pages later.

## Can dynamic UI be supported? Can any render output be supported, or should it always be components?

`@render_react` can now return a `Node`, which is a `Tagifiable` that nests htmltools `tags.*`, `HTML`, strings, and other `Node`s at arbitrary depth. Raw HTML, plain text, and htmltools wrappers are all supported in the wire tree. See `docs/superpowers/specs/2026-05-29-htmltools-spec-nesting-design.md` and `examples/app-py/14-nesting` for the design and a working example.

Still open: whether traditional Shiny input widgets (e.g., `ui.input_slider`) embedded inside a `@render_react` tree work end-to-end (input bindings, server-side `input.xxx()` reads). That path is untested.

## Nest UI functions into `shinyreact.ui.*` submodule

Currently `output_react`, `page_react`, and `page_bare` are flat top-level exports. Later, restructure into a `shinyreact.ui` submodule: `ui.output()`, `ui.page_react()`, `ui.page_bare()`.

## `HTMLDependency` support for `page_react()`

`page_react()` currently accepts `js_file`/`css_file` string paths. Consider accepting `extra_deps: list[HTMLDependency]` instead of or in addition to string paths, for consistency with the rest of the API.

## Evaluate `extra_deps` on `output_react()`

Should HTML dependencies be handled exclusively at the render subclass or page level? If so, `extra_deps` could be removed from `output_react()` to simplify the API.

## R bookmark restore value shape vs Python ([#27](https://github.com/posit-dev/shinyreact/issues/27))

R's bookmark restore serializer uses `jsonlite::toJSON(auto_unbox = TRUE)`, so a
length-1 R vector (e.g. a checkbox-group with one selected value) serializes as
a JSON scalar `"a"`, whereas Python `json.dumps` emits `["a"]`. This can seed the
wrong shape into the JS input registry for single-value multi-value inputs on
restore. Needs a cross-language bookmark-payload fixture and a shape-preserving
fix (hard due to R's lack of scalar vs. vector distinction). See issue
[#27](https://github.com/posit-dev/shinyreact/issues/27).

## R tag boolean/NA attribute serialization vs Python

R's `as_wire.shiny.tag` walker passes attribute values through after key
translation, so an HTML boolean attribute like `tags$input(checked = NA)`
serializes to `"checked": null`, whereas Python's `tags.input(checked=True)`
emits `"checked": ""`. Different falsy representations of an HTML boolean
attribute. Only affects DOM-`tag` node attrs (not `node()` props), is an
htmltools R-vs-Python idiom difference, and no parity fixture covers it.
Acceptable v1 limitation; revisit if a downstream component relies on boolean
attributes round-tripping identically across languages (would want a shared
fixture + agreed canonical encoding).

## Re-parent `Node` onto `UiReact(UiComponent, AllowsChildren)` (after #69)

`Node` is currently a standalone `Tagifiable` dataclass (see
`docs/superpowers/specs/2026-05-29-htmltools-spec-nesting-design.md`). Once #69
lands the `UiComponent` / `AllowsChildren` hierarchy, re-categorize `Node` as
`UiReact(UiComponent, AllowsChildren)`. This is cosmetic — it changes `Node`'s
base classes, not its `tagify()` / serialization behavior. Keep `Node`'s
`tagify()` and dependency surface aligned with what #69 expects of a
`UiComponent`.

## Tracked as GitHub issues

- [#28 — Shiny client runtime as an npm package](https://github.com/posit-dev/shinyreact/issues/28)
- [#35 — JSON Patch value-equality dedup](https://github.com/posit-dev/shinyreact/issues/35)
- [#36 — JSON Patch wire format](https://github.com/posit-dev/shinyreact/issues/36)
