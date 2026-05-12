# RFC: Conventions for downstream React UI helper packages

## Summary

Define the shape of a "well-formed" `shinyreact` helper package — a downstream Python+JS package that exposes components from an existing React UI library to `shinyreact` users. Validate the conventions with a working MUI prototype, then use that spine to spawn per-category helper packages (`shinymui`, `shinyradix`, a copy-paste pick, `shinyaggrid`, ...) without re-litigating bundling, naming, and asset-injection conventions each time.

This is a strategic RFC. The terminal artifacts are (a) a written conventions doc, (b) a 5-component MUI prototype, and (c) a Claude Code skill that scaffolds a new helper package from a given upstream-library repo location. Per-package implementation issues are deliberately out of scope — they get filed in a follow-up umbrella issue once the conventions are validated.

## Motivation

`shinyshadcn` is one concrete reference implementation. Before a second helper package appears, we want shared conventions so consumers can mix `shinyshadcn + shinymantine + shinyaggrid` in one app without:

- React duplication (each helper package shipping its own React copy)
- Component-name collisions (two packages both registering `Button`)
- Inconsistent Python API shapes (one package using factories, another using classes, a third using raw `Spec` builders)
- Inconsistent asset injection (`HTMLDependency` passed via `ui_output(extra_deps=...)` in one package, via a render-class attribute in another)

Establishing the spine now is cheaper than retrofitting later. The RFC is also a reference document we can hand to external contributors who want to wrap a library we haven't covered.

## Scope: which categories

The RFC covers four of the five categories from the broader React UI landscape:

| # | Category | Example libraries | Why include |
|---|---|---|---|
| 1 | Styled component libraries | MUI, Ant Design, Mantine, Chakra | The "default" case — large component set, opinionated styles |
| 2 | Headless primitives | Radix, React Aria, Headless UI, Ariakit | Different shape — ships behavior, not styles; styling is the consumer's problem |
| 3 | Copy-paste / "owned code" | shadcn/ui (already covered), Tremor, Park UI | Different shape — may not need a JS bundle at all if components live in the consumer's app |
| 5 | Specialized | AG Grid, TanStack Table, Recharts, Plotly | Different shape — huge prop surfaces, often one-component packages |

**Out of scope:** Tailwind-centric (category 4). Flowbite-style packages collapse into category 1; Tailwind UI collapses into category 3. Carving it out separately would be more taxonomy than insight.

## Conventions the RFC resolves

These are the structural decisions every helper package author needs *before* they start writing code. Each subsection lands a concrete recommendation.

### 4.1 JS bundle shape

**Recommendation:** IIFE matching the `shinyreact` / `shinyshadcn` precedent.

- Single file, self-contained, no module loader required.
- React and ReactDOM externalized to `window.shinyreact.React` / `window.shinyreact.ReactDOM` — never bundle React. This prevents duplicate React instances when multiple helper packages load.
- The bundle's only side effect at load time is calling `window.shinyreact.registerComponents(catalog, registry)`.
- `shiny-react` hooks (`useShinyInput`, `useShinyOutputValue`, ...) accessed via `window.shinyreact.*` rather than imported.

This is the same contract `shinyshadcn` uses today. Codifying it makes it explicit for new packages.

### 4.2 Component naming / namespacing

**Recommendation:** Namespace-prefixed keys in the catalog (`mui:Button`, `radix:Dialog`, `aggrid:AgGridReact`). Python factories on the Python side can use shorter names locally (`mui.button(...)` produces `{"type": "mui:Button", ...}`).

Two-line rationale:

- Without namespacing, two packages both exposing `Button` silently clobber each other; the load order determines which wins.
- Prefixed keys are still readable in JSON specs when debugging.

The prefix is the package's short name (`mui`, `radix`, `tremor`, `aggrid`), not the full package name.

### 4.3 Python API shape

**Recommendation:** Factory functions returning `Spec` / `Element` for the initial prototype. Acknowledge #68's class-per-component model as the forward-looking direction, and structure helper-package code so the migration is mechanical (one factory per future class).

```python
# Initial shape (factory)
def button(label: str, *, variant: str = "contained", id: str | None = None) -> Element:
    return Element("mui:Button", {"label": label, "variant": variant}, id=id)

# Future shape (class, per #68)
class MuiButton(UiInput):
    def __init__(self, label: str, *, variant: str = "contained", id: str | None = None): ...
    def tagify(self) -> Tag: ...

def button(*args, **kwargs) -> MuiButton:
    return MuiButton(*args, **kwargs)
```

The factory form is what `shinyreact` exposes today; matching it keeps the prototype consistent with the rest of the framework.

### 4.4 Render subclass pattern

**Recommendation:** Helper packages subclass `shinyreact.reactive_output` *only* when they need a custom `transform()` (e.g., to accept a package-specific object and emit its `.to_spec().to_dict()` representation). Otherwise, consumers use the base `reactive_output` directly.

```python
# Only when there's package-specific transform logic
class render(shinyreact.reactive_output):
    async def transform(self, value: MuiComponent) -> Any:
        return value.to_spec().to_dict()
```

If the package only ships static UI factories with no server-rendered package objects, no subclass is needed.

### 4.5 Asset injection

**Recommendation:** `HTMLDependency` lives next to the Python module and is injected via `shinyreact.ui_output(id, extra_deps=[mui_dep()])` — current canonical pattern.

Note an open architectural question (already tracked in `docs/todos.md`): `extra_deps` on `ui_output()` may move to render-class or page level later. Helper packages should keep their `_dep()` constructor as a public helper so a migration is one-liner.

### 4.6 Package layout & naming

**Recommendation:**

- **Naming:** `shiny<lib>` — `shinymui`, `shinymantine`, `shinyradix`, `shinytremor`, `shinyaggrid`. Lowercase, no separators.
- **Repository layout:** *Eventually* per-package repos or a `shinyhelpers` monorepo with GHA-scheduled builds — both are viable and the decision can be made when the first real package ships. For prototyping (and for the MUI prototype this RFC produces), helper packages live in this repo under `downstream-prototypes/`.
- **Per-package internal layout:** Mirror `shinyreact`'s own — `js/` for the IIFE bundle source, `pkg-py/` for the Python package, `pkg-r/` for the (future) R package.

The "eventually" leaves the repo-vs-monorepo choice for the team to make based on real-package experience. A monorepo with GHA-scheduled rebuilds (so upstream library bumps are picked up automatically) is an attractive option but premature to commit to before any real packages exist.

## Open questions explored via prototype (not legislated)

These are the UX-detail questions the MUI prototype will surface answers for. The RFC documents findings rather than legislating in advance — the prototype's job is to make these concrete.

### Theming

How does MUI's `ThemeProvider` get configured? Where does the theme object live (Python-side as part of `page_react()`, or JS-side as a registered config)? How does this hook up to brand.yml?

The MUI prototype will pick one approach; the RFC reports what worked and flags whether the same shape transfers to other libraries (Mantine, Chakra also have `Provider` patterns; Radix has `Theme`; specialized libs vary widely).

**Prototype finding:** The prototype did NOT integrate theming. Each MUI component renders with MUI's default theme; no `ThemeProvider` wraps the React tree. This is deferred until a real `shinymui` package. The MUI pattern would require wrapping the entire React tree inside `ShinyreactRenderer` with `<ThemeProvider theme={...}>`, which is a `shinyreact`-level concern (likely a per-page-react hook or a "provider chain" registration mechanism). **New open question raised:** where do `Provider`-style wrappers register in `shinyreact`? Mantine, Chakra, and Radix have analogous `Provider` patterns; the answer should generalize across categories.

### Slot / compound-component APIs

MUI's `Button` accepts `startIcon` / `endIcon` props that are React nodes. Radix uses compound components (`Dialog.Root`, `Dialog.Trigger`, `Dialog.Content`). How do these map to the Spec model where `props` is JSON?

Candidate answers to test in the prototype:
- Allow `Element` instances as prop values (renderer walks them recursively).
- Reserve special prop names (`startIcon` becomes a child slot, not a JSON prop).
- For Radix-style compound APIs, expose each piece as its own factory.

**Prototype finding:** Slot props for MUI Buttons (`startIcon`, `endIcon`) were passed as icon-name strings (e.g. `start_icon="Save"`) and resolved client-side via `@mui/icons-material`. This avoided the alternative of teaching the renderer to walk `Element`-valued props. The convention generalizes: prefer string-keyed slot lookups when the library exposes a finite, named catalog (icons, variants, theme tokens); fall back to allowing nested `Element` references in props when the slot accepts arbitrary user-defined React content. The latter pattern was NOT exercised in the prototype — it remains an open question for compound-component libraries like Radix where `Dialog.Trigger`/`Dialog.Content` siblings would need to compose as named slots in a single factory or as separate factories returning matching `Element` types.

### Controlled inputs vs server-pushed values

When MUI's `<Slider value={x} onChange={...} />` wraps `useShinyInput`, what's the contract? Does the helper package provide a single `mui.slider(id, ...)` factory that handles both directions, or does the consumer wire `useShinyInput` themselves?

**Prototype finding:** Three patterns surfaced cleanly across the 5 components. (1) **Action-button events** (Button): `useShinyInput<number>(input_id, 0, { debounceMs: 0, priority: "event" })` + `onClick` increments a counter; server-side uses `@reactive.event(input.<id>, ignore_init=True)`. (2) **Value-tracking inputs** (TextField, Slider): `useShinyInput` with library-appropriate `debounceMs` (250ms for text, 100ms for slider drags); the component is fully controlled. (3) **Server-pushed outputs** (DataGrid): `useShinyOutputValue<Payload | null>(output_id, null)` with a `"Loading…"` fallback while the value is null. The factory naming convention (`input_id` for inputs, `output_id` for outputs) reads clearly at the call site and should be codified as the contract.

### Per-category divergences

The prototype is MUI (category 1). The RFC will flag what's expected to *differ* for the other three categories:

- **Headless (category 2)** — no CSS in the bundle; consumer ships their own styles. Likely needs documented styling integration patterns rather than a styling story baked into the helper package.
- **Copy-paste (category 3)** — the consumer owns the component source. The helper package may ship *no JS bundle at all* — just Python factories that target the consumer's already-copied components. This is a meaningfully different shape and may need its own RFC follow-up.
- **Specialized (category 5)** — AG Grid has hundreds of props. Per-prop Python typing isn't tractable; the package probably exposes a thin pass-through (`aggrid.grid(props_dict)`) plus a few common-case helpers.

**Prototype finding:** All five components fit the same shape — Python factory returns `shinyreact.Node(type="mui:<Name>", props=...)`, JS component reads `element.props` after registration. DataGrid stretched but did not break the shape: its `output_id` + server-side payload (`{rows, columns}`) is the per-prop-typing workaround flagged in §4.3 — the factory exposes only `output_id` and `height`, deferring MUI DataGrid's hundreds of props to the server payload. Bundle size grew substantially with each MUI dependency (see §6 "Bundle size baseline" for numbers). Real-world specialized-category packages should consider tree-shakable imports (named imports rather than `import * as MuiIcons`) and lazy-loading heavy components (e.g., DataGrid behind a dynamic import) to keep the baseline payload reasonable.

## MUI prototype

**Location:** `downstream-prototypes/shinymui/` (repo root). Explicitly not under `examples/` — these are not user-facing examples and not published.

**Internal layout:** mirrors `shinyreact`'s — `downstream-prototypes/shinymui/js/`, `downstream-prototypes/shinymui/pkg-py/`.

**Components (5):** chosen to exercise each open question from §5:

| Component | Exercises |
|---|---|
| `Button` | Basic factory, slot API (`startIcon`/`endIcon`), controlled-event input |
| `TextField` | Controlled string input, label + helper-text composition |
| `Slider` | Controlled numeric input, value-range props |
| `Card` | Children / composition, layout container |
| `DataGrid` | Specialized component with large prop surface, server-pushed data via `useShinyOutputValue` |

**Lifecycle:**
- Built alongside the RFC; findings folded back into §4 and §5 as discoveries land.
- Throwaway — gets superseded by the real `shinymui` package once the umbrella issue (see §8) spawns per-package work.
- Not published to PyPI/npm; no CI gating; lives in `downstream-prototypes/` indefinitely as a reference until removed.

### Bundle size baseline

The built `dist/shinymui.js` totaled 4.3 MB minified (876 KB gzipped) covering all 5 components. Growth across tasks:

| Step | Components added | Raw size | Gzip | Delta (raw) |
|------|------------------|----------|------|-------------|
| Task 3 | empty registry  | 129 B    | n/a  | baseline    |
| Task 6 | Button + `@mui/material` core + `@mui/icons-material` | 3,942 KB | 707 KB | +~3.8 MB |
| Task 7 | TextField | 4,021 KB | 729 KB | +~80 KB |
| Task 8 | Slider    | 4,045 KB | 737 KB | +~24 KB |
| Task 9 | Card      | 4,048 KB | —    | +~3 KB |
| Task 10 | DataGrid + `@mui/x-data-grid` | 4,514 KB | 876 KB | +~466 KB |

Most of the weight is in three places: `@mui/material` core (~3 MB, paid on the first component), `@mui/icons-material` (large because the prototype uses `import * as MuiIcons` for runtime icon-name lookup), and `@mui/x-data-grid` (~466 KB).

Implications for real packages:
- **Tree-shake icons.** The prototype trades bundle size for slot-API simplicity (string icon names look up against a wildcard import). A real package should import only the icons it ships, or expose a separate icon catalog so the consumer's bundler can tree-shake.
- **Lazy-load heavy widgets.** Specialized-category components (DataGrid, charts, rich editors) should be reachable via dynamic `import()` so the baseline payload doesn't include them when unused.
- **Provider centralization.** If theming integration adds a `ThemeProvider` wrapper, it should be the only theme-related code shipped in the base bundle; component-specific styling overrides belong with their components.

## Per-category notes

Short forward-looking paragraphs. Each will be expanded once a prototype for that category exists.

### Headless (Radix / React Aria)

Likely deviation from MUI baseline: no CSS in the JS bundle. The helper package's job is to expose Radix primitives to Python; styling integration (Tailwind, CSS modules, vanilla CSS) is the consumer's problem. May need a documented "pair this with your own stylesheet" convention. Open question: does the helper package ship recommended base styles as an *optional* secondary `HTMLDependency`?

### Copy-paste (shadcn-style)

This category may not need a JS bundle at all. If the consumer has copied components into their app, the helper package's job is just to expose Python factories that produce specs targeting those component types. The catalog/registry side becomes the consumer's responsibility (they register their own copied components). RFC follow-up: clarify whether this is still a "helper package" in the same sense, or a different artifact (a Python-only adapter).

### Specialized (AG Grid / TanStack / Recharts)

Per-prop typing is intractable for libraries like AG Grid. Expected shape: a thin pass-through (`aggrid.grid(props: dict)`) plus a handful of common-case helpers (`aggrid.column(...)`). The prototype's `DataGrid` component is included specifically to test this — if it feels right, the convention transfers; if it doesn't, the RFC documents what needs to change for category-5 packages.

## Follow-up: umbrella issue

Once the RFC is settled *and* the MUI prototype validates the conventions, file an umbrella issue in the style of #68 enumerating per-package child issues:

- `shinymui` (graduates from prototype to real package)
- A headless pick — likely `shinyradix` or `shinyreactaria`
- A copy-paste pick — TBD whether this is its own package or a different artifact shape
- `shinyaggrid` or `shinytremor` (specialized)

The RFC document is linked from each child issue as the conventions reference. Each child issue scopes its own work: location (this repo's `downstream-prototypes/` graduation path, separate repo, or `shinyhelpers` monorepo) gets decided per-package based on team capacity at the time.

## Follow-up: scaffolding Claude skill

Once the conventions in §4 are stable and the MUI prototype validates them, build a Claude Code skill — working name `scaffold-shinyreact-helper` — that takes a repo location for an upstream React library and produces a scaffolded helper package matching this RFC.

**Why it belongs in this RFC's orbit.** Codifying conventions in prose is necessary but not sufficient; a skill that *enacts* the conventions catches drift the prose misses, and makes the RFC's value concrete (new package in minutes, not days). It also forces the conventions to be precise enough to mechanically apply — a useful pressure on §4.

**Inputs.**
- Path (local) or URL (GitHub) to the upstream React library's source repo, or an npm package name.
- Short package name to use for namespacing and Python module name (e.g., `mantine` → `shinymantine`, catalog prefix `mantine:`).
- Target location on disk (defaults to `downstream-prototypes/<name>/`).

**Outputs.**
- Directory matching the `downstream-prototypes/shinymui/` layout established by the MUI prototype.
- `js/` with Vite IIFE config, externalized React, a `registerComponents()` entry point, and one stub component registration so the bundle is verifiable end-to-end.
- `pkg-py/` with package skeleton, one example factory function, `_dep()` constructor wired to the built JS, and a `reactive_output` subclass stub commented out (per §4.4 — only if needed).
- A minimal example app under `<scaffold>/example/` that mounts the stub component, used as a smoke test that the new package loads.
- A `README.md` pointing at this RFC as the conventions reference.

**Explicit non-goals (deferred).**
- Auto-discovering all components in the upstream library and generating per-component factories. The skill scaffolds *one* example component; populating the rest is the package author's job (and the right hook for an LLM-assisted second pass, but not in this skill's first version).
- Theming/styling integration — depends on per-category answers from §5.
- PyPI/npm publishing setup, CI workflows — deferred until the repo-vs-monorepo choice is made (§4.6).
- Per-category divergence handling. The skill targets the MUI-baseline shape (category 1). Headless / copy-paste / specialized packages will need either skill flags or separate skills once their shapes are pinned down (§7).

**Lifecycle.** The skill lives at `.claude/skills/scaffold-shinyreact-helper/` in this repo. As §4 evolves, the skill is updated in the same PR — keeping prose and tool in lockstep is the whole point. When the conventions stabilize, the skill can be promoted to a shareable plugin.

## Risks

- **Conventions ossify before the prototype reveals problems.** Mitigation: §5 (open questions) is explicitly designed for revision after the prototype lands. The RFC is a living document until the first real per-package issue is filed.
- **Per-package repos balloon — N packages, N CI setups, N release pipelines.** Mitigation: the repo-vs-monorepo choice is deliberately deferred (see §4.6). A `cookiecutter-shinyhelper` template is a likely follow-up but out of scope here.
- **React-version skew across helper packages.** Mitigation: §4.1 mandates externalized React via `window.shinyreact.React`. All packages share the React that `shinyreact` ships.
- **MUI is not representative.** Mitigation: §5 and §7 explicitly call out per-category divergences. The MUI prototype is the spine, not the universal answer.
- **Prototype quality drift.** The prototype is explicitly throwaway, but throwaway code tends to become reference code. Mitigation: README in `downstream-prototypes/shinymui/` clearly marks the package as a non-published reference and points readers to the eventual real package once it exists.

## Acceptance criteria for this RFC

- Conventions in §4 are stable enough that a contributor can read the RFC + look at `downstream-prototypes/shinymui/` and build a second helper package without further consultation.
- Each open question in §5 has a concrete answer (or a documented decision to defer to per-package issues).
- The MUI prototype demonstrates at least one component per archetype (basic factory, controlled input, layout/children, specialized) wired end-to-end against a working example app.
- The `scaffold-shinyreact-helper` skill, run against a fresh upstream-library repo location, produces a new `downstream-prototypes/<name>/` directory whose example app loads in a browser without manual edits.

**Status (2026-05-12):** First three criteria satisfied by `downstream-prototypes/shinymui/` (5 components, all archetypes covered, validated via `downstream-prototypes/shinymui/example/app.py`). The scaffolding-skill criterion remains open and is the subject of the follow-up plan.
