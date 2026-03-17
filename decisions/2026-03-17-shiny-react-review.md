# `wch/shiny-react` — Review

Source: https://github.com/wch/shiny-react

## What It Is

**shiny-react** (`@posit/shiny-react`, v0.0.16, experimental) is a React bindings library for Shiny. It provides TypeScript hooks that enable bidirectional communication between a React frontend and a Shiny server (R or Python). The core philosophy: **the entire UI is a React app**, and Shiny serves purely as a reactive data backend.

Each app is a standalone project: an esbuild/TypeScript build produces `main.js`/`main.css`, and the Shiny backend serves a bare HTML page with `<div id="root">`. There is no installable Python/R package — each app copy-pastes a `shinyreact.py` or `shinyreact.R` utility file providing `page_react()`, `render_json`, and `post_message()`.

---

## Approach

### JS Side — React Hooks Library

An ESM npm package (~500 lines of TypeScript) providing four hooks:

| Hook | Direction | Purpose |
|------|-----------|---------|
| `useShinyInput(id, default)` | React → Shiny | Creates React state that syncs to `Shiny.setInputValue()` with debouncing |
| `useShinyOutput(id)` | Shiny → React | Receives JSON data from server-side `render_json` |
| `useShinyMessageHandler(type, handler)` | Shiny → React (push) | One-shot server-push messages |
| `useShinyInitialized()` | — | Tracks when Shiny framework is ready |

Plus a built-in **`ImageOutput`** component that handles Shiny's complex sizing/clientdata protocol automatically.

React is a **peer dependency** (`^18.2.0 || ^19.0.0`), not bundled. Each app uses esbuild to produce its own self-contained bundle.

**Output binding trick:** Creates hidden `<div>` elements in the DOM, calls `Shiny.bindAll()` to register them with Shiny's output binding system, then routes `renderValue()` data into React state via a custom `ReactOutputBinding`.

### Python/R Side — Copy-Pasted Helpers

There is **no installable package**. Each example contains a `shinyreact.py` / `shinyreact.R` file providing:

- `page_react(title, js_file, css_file)` — minimal HTML shell with `<div id="root">`
- `render_json` — a `Renderer[Jsonifiable]` that sends arbitrary JSON to the client
- `post_message(session, type, data)` — wrapper around `session.send_custom_message()`

### Extension Mechanism

**There is none.** No component registry, no plugin system, no `registerComponents()`. Each application is fully self-contained — you write React components, import the hooks, and bundle everything together.

---

## Strengths

1. **Clean, idiomatic React API** — hooks mirror `useState` semantics, natural for React developers
2. **Full React ecosystem access** — any library works (shadcn/ui, Recharts, Tailwind, etc.)
3. **TypeScript-first** with full type safety and generics on all hooks
4. **Lightweight** — small library footprint, React not bundled
5. **Dual R + Python support** from day one
6. **Built-in input debouncing** with configurable delay and priority
7. **Excellent progressive examples** (7 apps from hello-world to AI chat, with Shinylive deployment)
8. **Built-in `ImageOutput` component** that handles Shiny's complex sizing/clientdata protocol automatically

---

## Shortcomings and How They Could Be Addressed

### 1. No installable Python or R package

`shinyreact.py`/`shinyreact.R` is duplicated into every app directory. Helper files diverge between examples. There's no `pip install` or `install.packages()` story.

**Address:** Publish `page_react()`, `render_json`, and `post_message()` as an installable package (like shinyjson does). Bundle the JS as an HTMLDependency so apps don't need to manage script tags manually.

### 2. Every app needs a Node.js build toolchain

`package.json`, esbuild, `tsconfig.json` required per project. Massive barrier vs. Shiny's "just write Python/R" experience.

**Address:** For apps that only need pre-built components, a server-driven spec (like shinyjson's `Spec`/`Element`) eliminates the need for per-app JS builds entirely.

### 3. No extension/plugin mechanism

Each app builds its entire React UI from scratch. No way for downstream packages to contribute components without the user modifying their own esbuild bundle.

**Address:** Provide a `registerComponents()` API (similar to shinyjson's `window.shinyjson.registerComponents`) so downstream packages can contribute component catalogs that any app can use.

### 4. Server cannot describe UI structure

The server can only send data, never describe what to render or how to lay it out. The entire UI layout is hardcoded in React source.

**Address:** Implement a JSON-based UI spec (like shinyjson) where the server returns `{root, elements}` describing the component tree. The client renders from the spec, enabling server-driven dynamic UIs without rebuilding JS.

### 5. Hidden DOM element hack for outputs is fragile

`OutputRegistry` creates invisible `<div>` elements and calls `Shiny.bindAll()`/`unbindAll()` via `requestAnimationFrame` to piggyback on Shiny's output binding system. The author acknowledges it may not be "100% reliable."

**Address:** Consider a more direct integration — e.g., a custom output binding that doesn't require DOM elements, or a WebSocket/message-based channel that bypasses the binding system entirely.

### 6. One-way inputs (no server-to-client updates)

`useShinyInput` only sends data to Shiny. Server-side `update*Input()` calls do not propagate back to React state. Code comments explicitly acknowledge this gap.

**Address:** Extend the input registry to listen for server-initiated update messages (e.g., via custom message handlers or a dedicated update channel) and sync them back into React state.

### 7. Message system has streaming limitations

The chat example bypasses `useShinyMessageHandler` entirely, using raw `Shiny.addCustomMessageHandler` for streaming.

**Address:** Support streaming/chunked messages in the message registry, or provide a dedicated streaming hook.

### 8. jQuery dependency in a React app

`ReactOutputBinding.find()` uses `$(scope).find(...)`, pulling in jQuery even though the rest of the frontend is pure React.

**Address:** Use native DOM APIs (`scope.querySelectorAll(...)`) instead. Shiny's newer output binding API may support this directly.

### 9. Incomplete error handling

`renderError` logs to `console.log` instead of surfacing errors in the React UI. Users see nothing when an output errors.

**Address:** Route errors into React state (similar to how `recalculating` is tracked) so components can render error boundaries or inline error messages.

### 10. Unsettled initialization lifecycle

Several `if (!shinyInitialized)` guards are commented out, and TODOs suggest the timing between React mount and Shiny initialization isn't fully resolved.

**Address:** Establish a clear contract: either gate all hook effects behind `shinyInitialized`, or make the registries work independently and sync when Shiny becomes available (the code partially does this but inconsistently).

---

## Comparison with shinyjson

| | shiny-react | shinyjson |
|---|---|---|
| **UI defined in** | TypeScript / React | Python / R (via JSON spec) |
| **Server role** | Data only | UI structure + data |
| **Extension** | None — everything in one bundle | `registerComponents()` catalog |
| **App toolchain** | Node.js required per app | Hidden from app developers |
| **Target user** | React developers using Shiny | Shiny developers using components |
| **JS format** | ESM library (peer dep React) | IIFE bundle (bundles React) |
| **Python package** | None (copy-paste helpers) | Installable via pip |

shiny-react maximizes flexibility for developers who already know React. shinyjson keeps app developers in Python/R and hides the JS layer entirely.

---

## TODO List

- [ ] Evaluate publishing `shinyreact.py`/`shinyreact.R` as installable packages with bundled JS HTMLDependency
- [ ] Investigate eliminating per-app Node builds for apps using only pre-built components
- [ ] Design a component registry API for cross-app/cross-package component reuse
- [ ] Design server-driven UI spec format for dynamic component trees
- [ ] Replace hidden DOM element output binding hack with a direct message-based approach
- [ ] Implement server-to-client input update channel (bidirectional inputs)
- [ ] Support streaming/chunked messages in the message registry
- [ ] Remove jQuery usage from `ReactOutputBinding.find()` in favor of native DOM APIs
- [ ] Surface output errors in React UI instead of console-only logging
- [ ] Resolve initialization lifecycle — consistent gating on `shinyInitialized`
- [ ] Clean up commented-out code and resolve open TODOs in source
