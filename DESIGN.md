# ui.tsx-first Architecture: Rethinking Shiny's UI Layer for an AI driven World

## 1. Executive Summary

Shiny's original design achieved something remarkable: it let data scientists build professional web applications without learning HTML, JavaScript, or CSS. The framework accomplished this by generating UI from R/Python functions on the server and managing all client-server communication transparently.

AI changes the equation. When Claude can generate a complete React app — with layout, styling, interactivity, and accessibility — the server-side UI abstraction layer becomes indirection rather than simplification. The UI should simply live on the client from the start.

This is what `shinyreact` ships: the **`ui.tsx` pattern** (`set_react_page()` / `page_react_html()`) — the server contains only reactive computation; the client is a static React app that communicates via `useShinyInput` / `useShinyOutputValue` / `useShinyMessageHandler`. UI logic lives on the client.

This document was originally written to propose that architecture as a new direction, alongside an **app.py pattern** (`page_react` + `render_react` — server describes UI as a JSON wire tree rendered by the JS bundle). The app.py pattern was removed in #168; the original two-pattern version of this document is preserved at the [`archive/v0`](https://github.com/posit-dev/shinyreact/tree/archive/v0) tag, and history pointers for the removed APIs live in a comment on #167.

The document begins with the design tenets that guide the ui.tsx-first direction, then builds the supporting case.

## 2. Design Tenets

The sections that follow build the case for this shift — revisiting Shiny's first principles, examining how AI reframes them, and confronting the existential questions. But before the argument, here are the conclusions. These tenets are what should be guiding principles for AI driven development.

These tenets are ordered by priority — when tenets conflict, earlier tenets take precedence over later ones.

### Tenet 1: The app file is server logic the author can read and write

An app file contains reactive computations, data access, and business logic — nothing else. Whether the author writes it by hand or an AI drafts it, the server code must remain readable and understandable to the app author. This is Shiny's original promise, and it remains non-negotiable.

### Tenet 2: Shiny apps are polished products for non-technical audiences

Shiny apps are communication tools — they let subject matter experts who may not be technical with the underlying data safely interact with models and computations. The output is a polished product, not a notebook. This distinguishes Shiny from notebooks designed for the author's own exploration.

### Tenet 3: AI driven UI authoring is the default

Claude (or equivalent) is the default producer of the HTML, CSS, and React components that make up the application's interface. The author should not have to concern themselves with implementing layout, styling, component hierarchies, or frontend state management. Authors may still inspect or edit client code when needed, but the default path is AI driven UI authoring. The framework's job is to make that generation reliable — providing a clear communication bridge, well-documented hooks, and predictable conventions — not to abstract the UI away with R/Python wrapper functions.

### Tenet 4: UI lives on the client

All UI definitions — component trees, styling, layout, and client-side interactivity — exist as static assets (`index.html` + JS/CSS bundles). Nothing about the visual structure travels over the wire at runtime. The server sends data; the client decides how to render it. All client dependencies are resolved at build time via `package.json` — dynamic dependency injection (HTMLDependency) is not supported in ui.tsx-first apps. The server never influences what JS or CSS loads on the client.

### Tenet 5: Prefer client-side computation when the server isn't needed

If the data is already on the client — filter it on the client. If the interaction is purely visual — handle it on the client. The server should only be involved when it has something the client doesn't: access to data, models, credentials, or expensive resources. Every round-trip to the server adds latency and consumes session resources. Minimizing server involvement makes apps faster and more scalable. In short: this tenet applies to UI logic and interactions; Tenet 6 applies to data and computation.

### Tenet 6: The server is a reactive computation engine, connected by websocket

Shiny's core value is lazy, dependency-tracked, minimal recomputation — analogous to [Preact signals](https://preactjs.com/guide/v10/signals/), but running on the server where the data and models live. When inputs change, only the affected downstream computations re-execute. This enables exploration of models, datasets, and computations that are too expensive or too dynamic to precompute. It requires a persistent websocket connection — the server maintains a live reactive graph per session. This limits horizontal scaling (warm sessions must stay in memory) in a way that stateless API backends do not. We choose this tradeoff deliberately for the class of applications Shiny serves. Exploring a hybrid model (websocket for reactive state, REST for stateless operations) is a future priority.

### Tenet 7: The communication bridge is small and explicit

Message passing between client and server should be targeted — addressed by element id, message type, and handler — not broadcast to the document. The bridge API surface should be minimal: a small set of React hooks (functions that let components interact with Shiny) on the client (`useShinyInput`, `useShinyOutputValue`, `useShinyMessageHandler`) and corresponding server-side primitives. If the bridge grows large, something has gone wrong.

### Tenet 8: Pre-built component libraries are a parallel path

For organizations with design systems (government style guides, enterprise UI kits), curated component libraries remain valuable. These should be standalone JavaScript packages that ui.tsx authors import — not a framework-level registry. When authors want reusable UI beyond a single app, the right path is a standalone JS library — not a server-side component registry. The ui.tsx-first approach and component libraries coexist; they are not competitors.

### Tenet 9: The build step is real but invisible to the author

A React app with npm dependencies (the Shiny client runtime, the bridge hooks, component libraries) requires a build step — there is no honest way around this. The app will have a `package.json`. The key principle is that the author should never have to operate the build toolchain directly. `shiny run` (or equivalent) should handle dependency installation and bundling automatically, the same way `shiny run` today handles serving HTMLDependencies without the author knowing how. The AI generates the `package.json` and source files; the framework builds them.


## 3. Shiny's First Principles

Before proposing a new architecture, we need to revisit the principles that made Shiny successful. These come from Joe Cheng's 2022 keynote, [*The Past and Future of Shiny*](https://www.youtube.com/watch?v=HpqLXB_TnpI), where he describes the philosophy behind Shiny's design as creating a "pit of success" — making the easy path the correct path.

### Principle 1: Eliminate JavaScript and CSS from the author's concern

Joe's original mission was to let R (and now Python) users build professional web applications without mastering the web stack. JJ Allaire pushed this further — authors shouldn't even have to write HTML. The result: authors write pure R or Python code to facilitate both the client and server.

### Principle 2: Replace event handlers with reactivity

Traditional UI programming is "deceptively difficult" because of event handlers — the *when X happens, do Y* model. Event handlers are hard to reason about, lead to global-variable-style bugs, and produce apps that confidently give incorrect answers because the author forgot to update one output. Shiny replaced this with reactive programming, adapted from the Meteor framework: the author defines *relationships* between inputs and outputs, and the framework handles execution order and updates automatically.

### Principle 3: Code structure should mirror UI structure

Joe curated the UI functions so that code is scannable — the visual hierarchy of the code matches the visual hierarchy of the resulting interface. Attributes come first, children second, so the author doesn't have to "look past" screens of code to find where a UI element is defined.

### Principle 4: Shiny is for outward communication

Joe explicitly distinguishes Shiny from notebooks. Notebooks are for the author's own exploration. Shiny apps are for sharing with others who don't know how to code — letting non-programmers "turn the knobs" of a model safely. The UI is curated specifically for this audience.

## 4. How AI Changes the Equation

Each of Shiny's first principles was designed to solve a problem for a human author. AI doesn't eliminate those problems — it changes *who* is solving them. Here's how each principle holds up when AI is driving most UI authoring.

### Principle 1 preserved, mechanism changed

**Original:** Authors don't write JavaScript or CSS because the framework generates the web stack from R/Python UI functions.

**With AI:** Authors still don't write JavaScript or CSS — but not because the framework abstracts it away. Instead, the AI generates the client-side code directly. The R/Python UI function layer, which existed to shield the author from the web stack, becomes unnecessary indirection. The author's app file contains only server logic; the AI produces the client as static assets.

### Principle 2 preserved, scope narrowed

**Original:** Server-side reactivity replaces event handlers so the author doesn't have to reason about execution order.

**With AI:** Server-side reactivity remains essential for computations that live where the data lives — model inference, database queries, expensive transformations. But much of the UI reactivity that previously had to live on the server (show/hide a panel, toggle a loading state, filter a client-side list) can now live on the client, written by AI in standard React. The server's reactive graph gets smaller and more focused: it handles what only the server can handle.

### Principle 3 superseded

**Original:** R/Python UI code is carefully structured so that code hierarchy mirrors visual hierarchy — making the UI scannable for the author.

**With AI:** When the AI generates the UI, the author is no longer primarily reading UI code to understand layout. The scannability of the UI source matters more to the AI (and it handles JSX/HTML natively) than to the app author. This principle was valuable because humans were writing and reading UI code. In an AI-generated React app, the human primarily reads the rendered app and inspects the source only when needed.

### Principle 4 preserved, strengthened

**Original:** Shiny apps are communication tools for non-programmers, distinct from notebooks.

**With AI:** Unchanged — and if anything, strengthened. AI can often generate more polished, accessible, and responsive interfaces than many data scientists would build by hand, especially when guided by clear conventions and followed by validation. And crucially, AI can adopt best practices (accessibility, responsive design, modern UI patterns) as soon as they are established or desired — not only when the Shiny team implements and ships them as framework features. The audience (subject matter experts interacting with models) is the same. The quality of what they receive can go up, and it can improve at the speed of the AI plus the guardrails around it, not only the speed of the framework's release cycle.

### The dynamic UI problem

Beyond the AI argument, there is a deeper architectural motivation: **dynamic UI in traditional Shiny is unreasonably difficult.**

Consider a common pattern: a collection of items distributed across columns (a Kanban board, a card layout, a sortable list). The user drags an item from one column to another. The underlying data change is trivial — move an item from one list to another. But in traditional Shiny, the server must:

- Track the data (which items are in which columns)
- Generate unique input/output IDs for each item's UI controls
- Re-render the UI for every affected column via `render.ui`
- Register and destroy observers dynamically as items appear and disappear
- Manage the lifecycle of those observers to avoid stale handlers, duplicate firings, and race conditions

The server is forced to manage both the data *and* the UI simultaneously. Even experienced Shiny developers find this pattern error-prone. Observer lifecycle bugs are subtle — they don't crash the app, they produce incorrect behavior that is difficult to diagnose.

Now consider the same problem when UI lives on the client. The server manages only the data: receive an event ("item X moved to column Y"), update the data structure, send the new state back. The client — a standard React app — receives the updated data and re-renders. React's reconciliation handles the DOM updates automatically. No dynamic observers, no generated IDs, no lifecycle management. The server code goes from tangled UI+data logic to just pure data logic.

This is not merely a convenience improvement. It eliminates an entire class of bugs that exists only because the server was responsible for UI it should never have owned. The ui.tsx-first architecture makes the natural solution the easy solution: data flows down, events flow up, and the framework handles the rest.

## 5. The ui.tsx-first Architecture

### What an app looks like

A Shiny app under the ui.tsx-first model consists of two parts:

```
my-app/
  app.py              # Server logic: reactive computations, data access, business logic
  package.json        # JS dependencies (AI-generated)
  index.html          # Entry point for the React app (AI-generated)
  src/                # Client source (AI-generated)
    App.jsx
    styles.css
  dist/               # Built bundle (generated by build step, served by Shiny)
    app.js
    styles.css
```

The author owns `app.py`. Everything else is generated by AI (Claude or equivalent), typically via a Claude Skill or similar tooling that understands Shiny's client-server bridge. The `package.json` declares dependencies on the Shiny client runtime (`@posit/shiny`), the bridge hooks (`@posit/shinyreact`), React, and any component libraries. The build step (managed by `shiny run` or equivalent) resolves dependencies and bundles `src/` into `dist/`.

### What the server file contains

The server file is pure business logic:

- Reactive computations (`@reactive.calc`, `@reactive.effect`)
- Data access (database queries, file reads, model loading)
- Input handlers (receiving values from the client)
- Output renderers (sending computed results to the client)

It does **not** contain any UI definitions — no layout, no component trees, no styling, no HTML.

### What the client contains

The client is a standard React app that:

- Renders the full UI (layout, components, styling, client-side interactivity)
- Connects to the Shiny server via websocket
- Uses a small set of hooks (`useShinyInput`, `useShinyOutputValue`, `useShinyMessageHandler`, ...) to communicate with the server
- Handles UI-only reactivity locally (show/hide panels, loading states, client-side filtering)

The client is static — it can be served from a CDN, a `static/` directory, or any file server. It does not need a build step at runtime. Because the client has no server-generated state baked in, features like bookmarking will require the server to send an init message over the websocket on connection to hydrate (initialize) the client with the appropriate state.

### The bridge between them

The core communication layer is intentionally minimal:

| Direction | Mechanism | Example |
|-----------|-----------|---------|
| Client → Server | `useShinyInput(id, defaultValue)` | User selects a filter option |
| Server → Client | `useShinyOutputValue(id)` | Server sends computed plot data |
| Server → Client (push) | `useShinyMessageHandler(messageType, handler)` | Server pushes a notification |

### Server-side primitives

The server file uses a constrained set of primitives for communicating with the client. Standard Shiny render methods that produce UI (`render.ui`, `render.text`, `render.table`, etc.) are **not supported** in ui.tsx-first apps — they assume the server controls the DOM, which it does not.

The supported primitives:

**`@shinyreact.reactive_output`** (proposed in this document as `@render.json`) — Sends a value to the client as JSON. The client subscribes via `useShinyOutputValue(id)` and receives the data. This is the primary mechanism for server → client data flow. The server computes the data; the client decides how to render it.

```python
columns = reactive.value(initial_data)

@shinyreact.reactive_output
def column_data():
    return columns()
```

**`input.*`** — Values sent from the client via `useShinyInput`. The server reads them reactively as usual.

### What is explicitly disallowed

- **`render.ui`** — The server must not generate or manipulate DOM.
- **Other standard Shiny renders** (`render.text`, `render.table`, `render.plot`, `render.image`) — These assume server-controlled output slots in the DOM. In ui.tsx-first apps, use `reactive_output` to send data and let the client render it however it chooses. (In practice a narrow escape hatch shipped for embedding traditional output bindings inside a React tree: the `<ShinyOutput>` component plus `ImageOutput` for plots.)
- **Unbroken reactive loops** — A pattern where the server sends data to the client, the client immediately sends it back as input, which triggers the server again, creates an infinite loop. The communication model is designed to be unidirectional per interaction: input flows up (client → server), computed data flows down (server → client). The client should never echo server data back as input without user action in between.

### How `shiny run` works

`shiny run app.py` handles the full lifecycle: installs JS dependencies if needed, runs the build step to bundle `src/` into `dist/`, starts the Python server process, and serves the built static assets. The development experience remains a single command. In watch mode, it rebuilds the client when source files change. The author never runs `npm install` or `npx vite build` directly.

## 6. Shiny's Existential Question

### The uncomfortable question

As AI becomes more capable, why would someone use Shiny at all? Claude can already generate a FastAPI backend plus a React app from scratch. The resulting app scales horizontally, has no warm-session overhead, and uses patterns familiar to any web developer. What does Shiny offer that this doesn't?

### The honest answer

Shiny's advantage is narrow but real: **stateful reactive computation over a persistent connection.**

Most web applications are request-response: the client sends a request, the server computes a response, the server forgets. This works well when computation is cheap or results can be cached.

For applications where:

- The computation is expensive and inputs change incrementally (rerun only what changed)
- The server holds state that evolves during a session (a fitted model, a filtered dataset, a simulation)
- Multiple outputs depend on shared intermediate computations (compute once, use many times)

...a live reactive graph on the server, connected by websocket, is genuinely better than stateless request-response. The server knows what has already been computed, what depends on what, and what minimum work is needed when an input changes.

### The counterpoint: "stateless" APIs aren't always stateless

APIs can support session tokens via cookies, sticky routing, or other mechanisms to preserve user state across requests. But once a system depends on server-held session state, incremental recomputation, or request routing tied to a warm process, it gives up much of the simplicity and operational advantage that purely stateless request-response systems claim. At that point, it begins to converge on capabilities that Shiny already provides explicitly with a persistent reactive session.

### The risk

The resulting audience is smaller than what Shiny serves today. Many Shiny apps — simple dashboards, form-based tools, report generators — don't actually need stateful reactivity. They could be (and increasingly will be) built as a stateless API plus a React app by AI, without Shiny.

If we stay only in this niche, we will have fewer users over time.

### Where to look beyond the niche

We don't have answers yet, but these are directions worth exploring:

- **MCP (Model Context Protocol) app communication.** As AI agents interact with applications programmatically, Shiny's reactive model could be valuable — an agent changes an input, the server recomputes only what's needed, the agent reads the result. This requires stateless request-response support that Shiny doesn't have today.
- **Hybrid connection models.** Not every interaction in an app needs a websocket. If Shiny could serve stateless endpoints alongside the reactive graph, it could compete with FastAPI for the simple cases while maintaining its advantage for the complex ones.
- **The "graduated complexity" path.** A user starts with a simple app (AI generates everything, minimal server logic). As their needs grow — shared computed state, incremental updates, complex reactive dependencies — Shiny's reactive engine becomes the reason they stay. The ui.tsx-first architecture makes this on-ramp smoother: the client is already a standard React app, and the server grows in complexity as needed.

## 7. Things to Be Addressed

### `reactive.sync()` — sugar for reactive value + render

Evaluate whether a `reactive.sync(client_name=...)` primitive is worth adding as syntactic sugar for the common pattern of a `reactive.value` paired with a `reactive_output` that just returns it. The longer form (`reactive.value` + `@render.data`) is explicit and clear, but the pattern is common enough that a single-line equivalent may improve ergonomics. Key constraints: must be server-authoritative (not bidirectional — race conditions), full replacement (not patches), and should not obscure the data flow for readers of the server file.

### Message passing model

Today, Shiny's custom messages are broadcast to the document — any handler registered for a given message type receives it. In the ui.tsx-first model, message passing should be more targeted: addressed by element id, message type, and handler. If the id is omitted, the message falls back to the document level. The exact API shape needs design work.

### Hybrid connection model

The websocket is right for stateful reactive apps, but not every interaction requires it. Could Shiny serve stateless REST endpoints alongside the reactive graph? This would let simple operations (fetching a static resource, submitting a one-off computation) bypass the session overhead. This is a framework-level question, not specific to ui.tsx-first.

### MCP and agent communication

As AI agents begin interacting with applications programmatically (via MCP or similar protocols), Shiny's reactive model could be valuable — an agent changes an input, the server recomputes minimally, the agent reads the result. But this requires stateless request-response support that Shiny doesn't have today. How should this be designed?

### AI tooling for generating the client

The ui.tsx-first model depends on AI reliably generating correct React clients that communicate with Shiny via the bridge hooks. What does the Claude Skill (or equivalent) look like? What conventions, templates, or scaffolding make generation reliable? How do we test that generated clients are correct?

### Generated client verification

If the default path is AI driven client generation, then verification cannot be an afterthought. The architecture should assume that generated clients are trustworthy only when they are produced against a constrained target and passed through a managed validation pipeline.

At minimum, that pipeline should include:

- **Constrained generation targets.** The AI should generate against a narrow, well-documented surface area: stable bridge hooks, known file conventions, supported dependency patterns, and templates for common app shapes. Reliability comes as much from limiting the generation space as from improving the model.
- **Managed validation behind the scenes.** Since a build step now exists (see Tenet 9), type checking, linting, and packaging checks can run as part of the build pipeline. The app author is not expected to operate these tools directly — they run as part of `shiny run` or the AI generation workflow.
- **Browser-level end-to-end tests.** Playwright or an equivalent browser automation layer should validate the behaviors that matter most: websocket connection, input-to-output flow, message type delivery, bookmarking/init hydration, and failure handling when the server or bridge is not ready.
- **Security and accessibility review hooks.** The supported pipeline should include explicit checks for dependency provenance, XSS-sensitive rendering paths, and baseline accessibility expectations. AI can accelerate implementation, but it should not bypass the normal guardrails for client code shipped to users.

### Bookmarking and initial state — shipped

A static `index.html` bypasses Shiny's HTML-injection bookmarking. This shipped ([#27](https://github.com/posit-dev/shinyreact/issues/27)) with a different mechanism than originally sketched: the page entry points (`set_react_page()` / `page_react_html()`) read the active RestoreContext and emit a head `<script>` carrying the restored input values; the bundle seeds `useShinyInput` initial values from it before first render. See `examples/10-bookmarking/`.

### Migration path for existing Shiny apps

A Claude Skill (or equivalent) to migrate existing Shiny apps — which define UI in R/Python — to the ui.tsx-first model: a pure server file plus an AI-generated React client. This would lower the barrier for adoption and provide a concrete validation that the architecture works for real-world apps, not just greenfield projects.

### Disabling dynamic dependency injection

In ui.tsx-first apps, `shiny run` should explicitly disable HTMLDependency injection. Today, Shiny's server can inject JS/CSS into the page at serve time — this is how traditional Shiny apps load their UI libraries. In the ui.tsx-first model, all client dependencies are declared in `package.json` and resolved at build time. Allowing both paths simultaneously would create version conflicts, unpredictable load order, and a confusing developer experience. The server should refuse to inject HTMLDependencies when running in ui.tsx-first mode, and surface a clear error if server code attempts it.

### Shiny client runtime as an npm package

`shiny.js` and the bridge hooks need to be published as `@posit/shiny` and `@posit/shinyreact` so client bundlers can resolve them via `package.json` instead of HTMLDependency injection — replacing IIFE bundles, `window.shinyreact` globals, and ad-hoc React deduplication. Significant upstream ask to the Shiny team. Tracked in [#28](https://github.com/posit-dev/shinyreact/issues/28); the hybrid distribution plan (npm runtime alongside the HTMLDependency zero-build tier) is decided in `decisions/2026-08-17-js-distribution.md`.

### `shiny run` build integration

`shiny run` needs to detect a `package.json` in the app directory and automatically handle `npm install` + bundling before starting the server. This should work transparently — the author runs `shiny run app.py` and the build happens behind the scenes. Watch mode should rebuild on client source changes. The build tool (Vite, esbuild, or similar) and its configuration should be managed by the framework, not the author.

### Layout stability during initialization

The uninitialized UI (before the websocket connects and data arrives) should match the initialized UI's size and layout as closely as possible. No jittering, flickering, or layout shifts during the transition. Loading indicators like "Connecting..." or "Loading..." should never be the default — prefer empty placeholders that reserve the correct space. The goal is that the user perceives the app as already loaded; content simply appears in place.

### Asset versioning and caching

Static assets introduce operational concerns that server-generated UI largely hides. The ui.tsx-first path needs a supported story for cache busting, versioned asset URLs, and ensuring regenerated client bundles are picked up reliably in both development and deployment.

### Local edit loops

The default workflow should preserve a tight, single-command development loop. `shiny run` in watch mode should rebuild client assets on change and hot-reload the browser. When AI-generated files drift from the server logic, the author should be able to ask the AI to regenerate — not debug the build toolchain.

### Cross-origin deployment

Serving the client assets and the Shiny websocket server from different origins introduces CORS, cookies/authentication, websocket origin checks, and routing questions. The architecture needs an explicit same-origin default and a clear story for supported cross-origin deployments.

### R client-generation tooling

The R package (`pkg-r/`) ships with parity for the server surface (`page_react_html()`, `reactive_output()`, `send_message()`, input handlers, bookmarking) and shares the same JS bundle, so the same React client works against either server — `examples/01-hello/` runs one `www/` client from both `app.py` and `app.R`. The open question is the AI tooling: does R need its own Claude Skill for client generation, or does a shared skill cover both?

## 8. Current State and Next Steps

The ui.tsx-first architecture proposed in this document has been built, validated, and is now the repo's only pattern. The open questions in Section 7 remain relevant — the items below reflect the current status:

1. **Design tenets (Section 2) are the guiding principles.** The app file contains server logic; the framework handles reactivity; the app is a polished product.
2. **The pattern is implemented and working.** `set_react_page()` (Express) / `page_react_html()` (Core, and the R package) plus `reactive_output` ship in both Python and R.
3. **The JSON wire-tree transfer layer was removed with the app.py pattern (#168).** `reactive_output` sends raw JSON that the client renders directly. The original design of the wire tree lives at the [`archive/v0`](https://github.com/posit-dev/shinyreact/tree/archive/v0) tag.
4. **The bridge library is stable.** `useShinyInput`, `useShinyOutputValue`, `useShinyMessageHandler`, `useShinyInitialized`, `useShinyBusy`, `ShinyModuleProvider`, and `ImageOutput` are vendored from `@posit/shiny-react` and re-exported on `window.shinyreact`.
5. **Remaining open work** is tracked in the [GitHub issue tracker](https://github.com/posit-dev/shinyreact/issues).

## Appendix: Previous Explorations — `@json-render/react` and Server-Driven UI

### The original assumption

The `shinyreact` project was originally built on the assumption that a JSON spec transfer layer — powered by [`@json-render/react`](https://github.com/vercel-labs/json-render) — would be the right way to bridge server and client. (`@json-render/react` was dropped in #46 in favor of an in-house Spec walker, but the architectural argument below applies to either renderer.) The server would describe UI as a flat map of elements (`Spec`), serialize it as JSON, send it over the wire, and the client would render it into a live React component tree. This enabled server-driven UI: the Python/R process controlled *what* got rendered, not just *what data* was displayed.

### Why the assumption breaks down

This approach is valuable when the UI must be defined on the server — for example, when the app author writes Python/R UI functions that generate component trees. But if AI is generating the client directly as a React app, the JSON spec becomes unnecessary indirection:

- The AI can write React components directly — it doesn't need an intermediate JSON representation.
- The spec transfer layer adds complexity (serialization, registry, element resolution) without adding capability that the AI couldn't achieve in plain React.
- Server-driven UI was solving the problem of "how does a Python author control the UI without writing JavaScript." When the AI writes the JavaScript, that problem dissolves.

### What remains valuable

Not everything from this exploration is discarded:

- **The `shiny-react` hooks** (`useShinyInput`, `useShinyOutputValue`, `useShinyMessageHandler`, ...) are the communication bridge between the React app and the Shiny server. These carry forward directly.
- **The understanding of Shiny's output binding lifecycle**, module namespacing, and initialization sequencing — all hard-won during `shinyreact` development — informs how the client bridge works.

### The shift

Instead of: **Server describes UI as JSON → client renders JSON into React**

The model becomes: **Client is a React app → server sends data via hooks → client renders however it wants**
