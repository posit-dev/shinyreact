# Dynamic renderer dependency delivery — investigation & decision

**Issue:** [#160](https://github.com/posit-dev/shinyreact/issues/160) — `set_react_page`:
automatically deliver dependencies for renderers registered after page load.
Builds on [#87](https://github.com/posit-dev/shinyreact/issues/87).

**Status: investigation complete; automatic delivery DEFERRED to #160.** An earlier
draft of this spec proposed a flush-diff "Layer B" push. Spikes disproved that
design for widget outputs (see findings). This PR does **not** ship automatic
dependency delivery for post-page-load registrations; that work is tracked in #160.

## What this PR delivers

Automatic `HTMLDependency` discovery for every renderer that is **mounted while the
app body runs** — which covers the common cases:

- **Top-level renderers** in the `ui.tsx` pattern (`set_react_page`).
- **Renderers inside `@module.server`** (the original #87 bug) — discovered via the
  session's registered outputs at page-generation time (Layer A).
- **Dynamic UI via Shiny's `@render.ui` / `insert_ui`** — dependencies are delivered
  by Shiny's own native path (`_process_ui` → `renderContent` → `renderDependencies`),
  with correct dep-then-bind ordering. Proven by `test_dynamic_ui_plotly_dep`.

Concretely, this PR contains: the Layer-A session-output harvest in `_react_page_fn`,
the flipped module-dependency e2e test, the dynamic-UI (`@render.ui`) e2e test, the
`set_react_page` docstring note, and the R-asymmetry issue (#146).

## What remains (deferred to #160)

The **server-registers-a-renderer-after-page-load + React-supplied placeholder**
pattern — e.g. a `render_plotly` created in a `@reactive.effect` on a button click,
with the React client mounting its `<ShinyOutput>`. This does not render today, and a
clean automatic fix was not found. Tracked in #160.

## Investigation findings (why automatic delivery is hard)

All verified with Playwright spikes against `shinywidgets` `render_plotly`:

1. **Value delivery is fine.** A dynamically-registered output sends its value;
   Shiny's `bindOutput` replays a stored `$values[id]` when the element binds. A
   dynamically-registered `render.text` renders correctly (its binding JS is in core
   `shiny.js`).
2. **The gap is the missing dependency.** `dep_scripts=0 → bound=0 → no render`.
   Proof: a `ui.hold()`-ed warm-up `render_plotly` (Layer A injects the binding JS at
   startup) makes the dynamically-registered output render (`bound=1, plotly=1`).
3. **Naive late-push fails for widgets.** Pushing the dep after registration +
   `renderDependenciesAsync` + `bindAll` errors with `No model found for id …`.
   shinywidgets transmits the model via a `comm_open` **custom message** sent with the
   value; because the dependency (which registers the comm handler) loads *async, after*
   `comm_open` arrives, that message is dropped and the model is never created. A
   fundamental **ordering** problem (retrying `bindAll` for 2.4s did not help).
4. **A re-trigger handshake works** (`bound=1, plotly=1`): push deps → client loads them
   → client signals server → output **recomputes** → shinywidgets re-sends `comm_open`
   with its handler now present.
5. **Auto-triggering that recompute is the blocker.** The handshake only worked when the
   renderer depended on a reactive bumped by the deps-ready signal (one line of user
   cooperation). Two no-cooperation triggers failed: re-registering the renderer
   (`session.output(renderer)`) and `effect._ctx.invalidate()` (invalidation without
   Shiny's flush scheduling does not drive the recompute).

## Decision

- Ship the synchronous-mount coverage above (this PR).
- Defer automatic post-page-load delivery to #160, which records the goal, the proven
  re-trigger handshake, the recompute-trigger blocker, and candidate directions
  (supported invalidate-and-flush primitive; `suspend_when_hidden` reveal dance;
  shinyreact-owned implicit dependency). An interim opt-in fallback (the renderer
  depends on a shinyreact deps-ready reactive) is proven but intentionally not shipped.

## Superseded design (historical)

The original flush-diff push design (`on_flushed` diff of `session.output._outputs` →
`session._process_ui` → `shinyreact.deps` custom message → client
`renderDependenciesAsync` + `bindAll`) is **not** pursued: it delivers the dependency
but cannot render widgets because of the `comm_open` ordering problem (finding 3).
