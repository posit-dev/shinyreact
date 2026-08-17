# Shipping the JS runtime: npm package + HTMLDependency hybrid

**Date:** 2026-08-17
**Status:** Decided, not yet implemented
**Issues:** [#172](https://github.com/posit-dev/shinyreact/issues/172) (spike), [#28](https://github.com/posit-dev/shinyreact/issues/28) (upstream npm publication)

## Context

Today the entire JS runtime ships as a self-contained IIFE inside the Python
and R packages, injected as an HTMLDependency, with its whole public surface on
`window.shinyreact` (`pkg-js/src/global.ts`, `pkg-py/src/shinyreact/_dep.py`,
`pkg-r/R/dep.R`). Issue #172 asked whether we can distribute via npm instead
and drop the global, without letting the JS and the Python/R servers drift out
of sync.

The current architecture provides four guarantees by construction, and any
replacement has to account for each:

1. **Exactly one React instance.** React 19 is inside the IIFE; downstream
   bundles externalize `react`/`react-dom` to `window.shinyreact.React`
   (`examples/04-shadcn/vite.config.js`). No npm hoisting or peer-dep
   resolution can produce two Reacts.
2. **A zero-build tier.** Half the example gallery is plain `.js` in `www/`
   destructuring `window.shinyreact` — no `package.json`, no bundler.
3. **No client/server drift.** The hooks the browser runs ship inside the
   pip/CRAN package, so installing the server package pins the client.
4. **A load-order contract for bookmark restore.** The server emits a head
   `<script>` setting `window.shinyreact._restore` *before* the bundle runs;
   the bundle preserves it via `Object.assign(window.shinyreact || {}, …)`.
   This is the one feature structurally tied to the global's existence.

The known cost of the status quo: the bundled React is production-only, so dev
mode with Fast Refresh requires the dev/prod bridge-alias workaround in
`examples/09-hmr` — the clearest concrete pain the global causes, and a working
prototype of what npm distribution looks like.

### The key reframing

Issue #172 worried that "we can not couple the JS installed via the build and
the API that the python is expecting" and that a runtime assert "feels
brittle." That fear overweights the risk because it targets the wrong contract.
The compatibility surface between an npm-installed client and a pip/CRAN
server is not the JS API — it is the **wire protocol**: custom message shapes
(`shinyReactMessage`), input-id conventions (`:shinyreact.default`,
`:shinyreact.asis`), and the bookmark-restore payload. That surface is narrow
and slow-moving. Asserting a semver range on a *protocol* version delivered by
the server at page render is not brittle; it is exactly how ipywidgets'
`__frontend_version__` range check has worked for a decade, and how LSP/MCP's
`initialize` handshake works.

## Prior art surveyed

- **ipywidgets** — Python and JS published to two registries; sync enforced by
  a semver protocol range the Python package pins for the frontend
  (`_model_module_version` etc.). Skew is possible but loud. This is the
  model for our handshake.
- **anywidget** — eliminated the sync problem instead of managing it: the
  widget's ES module ships *as data inside the Python package*, travels over
  the comm channel, and is loaded via dynamic `import()`. The only permanent
  contract is a tiny injected interface (`render({ model, el })`) — dependency
  injection at the module boundary, stability by minimalism. shinyreact
  already has anywidget's key property (runtime ships in the server package);
  we cannot go all the way to its model because our traveling code is a
  *library the app author's build compiles against* (hooks + shared React),
  not leaf render functions. anywidget's lesson argues for keeping the
  single distribution channel; it concedes the dev-React/HMR goal.
- **JSON-RPC** (considered, rejected) — provides framing and request/response
  correlation, not payload schemas or version negotiation; LSP and MCP both
  needed an `initialize` handshake *on top of* JSON-RPC. shinyreact also
  doesn't own its transport (it rides Shiny's websocket protocol) and its
  traffic is reactive push, not call/response. The useful residue of the idea:
  the wire contract should be written down as a versioned schema document (see
  "Protocol as an artifact" below), not left implicit in three codebases.

## Options considered

**A. Thin npm shim** — publish types + `export const useShinyInput =
window.shinyreact.useShinyInput`; runtime stays server-shipped.
*Pros:* drift structurally impossible (a stale shim can only cause a compile
error); preserves all four guarantees; trivial to maintain.
*Cons:* doesn't drop the global; leaves the prod-React/no-HMR problem
untouched; component libraries still can't peer-depend on real hooks.

**B. Full npm distribution, drop the HTMLDependency** — users bundle
everything including React; sync via protocol handshake.
*Pros:* idiomatic npm DX, tree-shaking, real dev-mode React with Fast Refresh,
peer-dependency component libraries, global fully gone.
*Cons:* kills the zero-build tier; single-React now rests on ordinary npm
peer-dep semantics; release coordination across npm + PyPI + CRAN.

**C. npm installs from the server package's assets** — ship an npm package
dir/tarball inside the wheel / R `inst/`; users `npm install
"$(python -m shinyreact npm-path)"`. Answers #172's direct question: yes, npm
can install from Python assets (`file:` installs).
*Pros:* perfect version lock with no handshake; no npm pipeline; works
offline.
*Cons:* disqualifying DX — `file:` deps bake machine-specific absolute paths
into `package.json`/lockfiles, breaking every collaborator, CI runner, and
venv/renv rebuild; opaque to Renovate/audit/caching; still needs a separate
no-build answer. **Investigated and rejected.**

**D. Server-served ESM + import maps** — server ships an ESM build and injects
an import map; bundlers mark the runtime external.
*Pros:* keeps the version lock and drops the global; real `import` syntax even
with no build step; single React by construction.
*Cons:* import-map injection ordering is fragile with htmltools head assembly;
Vite dev doesn't resolve bare specifiers against page import maps, so dev mode
needs alias config anyway (inherits B's dev complexity without its ecosystem
payoff); would ship React ESM builds inside pip/CRAN packages.

**E. Hybrid: real npm runtime + keep the IIFE HTMLDependency (chosen).**

## Decision

Adopt **option E**, with the npm package named **`@posit/shinyreact`** (not
`@posit/shiny-react` — name consistency with the Python/R packages; the
upstream `@posit/shiny-react`@0.0.16 that `pkg-js/src/shiny-react/` was vendored
from is a separate, frozen artifact).

1. **Publish `@posit/shinyreact` to npm as the real runtime** — the hooks and
   components as ESM, with `react`/`react-dom` as peer dependencies. The
   bundler tier imports it directly and never touches the global. Dev mode
   gets a dev React and Fast Refresh with no bridge-alias workaround. Built
   from the same source as the IIFE (one codebase, two Vite build outputs).

2. **Keep the IIFE HTMLDependency as the explicitly-second, zero-build tier.**
   `window.shinyreact` remains supported for no-build apps and stays the React
   provider they externalize to. Both tiers speak the same protocol version by
   construction (same source, same release).

3. **Move bookmark restore (and the protocol version) off the global into a
   JSON script tag.** The server emits
   `<script type="application/json" id="shinyreact-config">{"protocolVersion": "…", "restore": {…}}</script>`
   and both tiers read it via `document.getElementById`. This removes the only
   structural dependency on `window.shinyreact` existing before app code runs,
   and gives the handshake its delivery vehicle. This change is independent of
   npm publishing and should land first.

4. **Semver protocol handshake at hook boot.** `@posit/shinyreact` declares a
   supported protocol range (e.g. `^1`); on init it checks the
   server-rendered `protocolVersion` and fails fast with a message naming both
   versions and the fix. The protocol version bumps only when the wire format
   changes — npm and PyPI/CRAN releases do not need lockstep.

5. **Protocol as an artifact.** Write the wire contract (custom message
   shapes, input-handler suffixes, restore/config payload) down as a single
   versioned schema document, with the same fixture payloads validated in TS,
   Python, and R. Its semver *is* the `protocolVersion`, so "what counts as a
   breaking change" is answered by diffing the schema. This is also the class
   of test that would have caught the #182–#186 parity bugs earlier.

### Accepted trade-offs

- **Two shipped artifacts** (npm ESM + IIFE). Mitigated: single source, one
  release builds both; docs must be crisp about which tier an app is in.
- **Drift between an old npm install and a new server package is possible.**
  The handshake makes it a clear, actionable error instead of silent
  breakage — the best any dual-registry design achieves (ipywidgets, plotly,
  bokeh included).
- **An npm release pipeline** is new operational surface (publish workflow,
  `NPM_TOKEN`, versioning discipline).
- **Single-React for the npm tier** rests on standard peer-dependency
  semantics rather than construction. Standard for the React ecosystem;
  the IIFE tier keeps the by-construction guarantee.

## Consequences / sequencing

1. `#shinyreact-config` script tag (restore + protocol version) — lands in
   this repo now; both `_bookmark.py` and `bookmark.R` change, plus
   `global.ts` reading the tag instead of `_restore`.
2. Protocol schema document + cross-language fixture tests.
3. Package `pkg-js/src/` for dual output (ESM + IIFE); add publish workflow for
   `@posit/shinyreact`.
4. Convert one Vite example (`09-hmr` is the natural candidate) to import
   `@posit/shinyreact`; retire its dev/prod bridge alias.
5. Longer term, if the zero-build tier is ever deprecated, the global dies
   with it — completing #172's original goal.

Related: `DESIGN.md` "Shiny client runtime as an npm package" (#28) and
`docs/posit-conf-2026-goals.md` (splitting the vendored hooks into their own
repo) both point at this end state; this record supersedes the
`@posit/shiny-react` naming used there.
