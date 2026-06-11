# shinyshadcn — goals & TODOs

Forward-looking goals and open work for the shadcn-for-shinyreact package. Newest
thinking at the top of each section. This is a prototype area; prefer a GitHub
issue for substantive work and link it here.

The package today is a strong *primitive* set (47 components, consistent API,
codegen-driven) but has **no story for layout or server-output interop** — the two
things that turn primitives into an actual app. The three goals below close that
gap; all three were motivated by reviewing the root `examples/` (`app-py/05-shadcn`,
`ui-tsx/04-shadcn`), which demonstrate patterns the package can't yet express.

---

## Goals

### 1. Embed traditional Shiny outputs inside shadcn layouts ⭐

**Gap.** There is no way to place a server-rendered Shiny output — `@render.plot`
(matplotlib), `@render.data_frame`, `@render.text`, an htmlwidget (plotly, etc.) —
inside a shadcn component. `chart` is data-driven (recharts from a data array) and
`table` takes `columns`/`rows` as props; neither surfaces a classic Shiny output.
This locks the package out of most real dashboards.

**Why it matters.** Every root shadcn example does this (matplotlib via
`ImageOutput`, plotly, `render.text`), and the core machinery already exists —
shinyreact core ships `ShinyOutput` / `ImageOutput` (`js/src/shiny-output.tsx`).
The package just doesn't surface it.

**Shape.** A thin `output(id)` / `plot_output(id)` helper (Python + R) wrapping
core's `ShinyOutput`, so users can compose `sc.card(sc.plot_output("p1"))` and pair
it with an ordinary `@render.plot` on the server. Highest-leverage addition — it
bridges the shadcn shell with real Shiny server outputs.

### 2. Layout primitives (`grid`, `page`/`container`, `stack`)

**Gap.** The package ships zero layout helpers. App authors hand-write
`ui.div(class_="grid grid-cols-2")` *and* must know to register classes via
`@source inline(...)` in `styles.css` and add Bootstrap-precedence overrides —
otherwise the classes silently no-op. These were the exact footguns hit while
building the `shinyreact-shadcn` gallery.

**Why it matters.** Delivers "good spacing by default, ready to use" (Barret's
stated goal) and removes a whole class of app-author errors instead of documenting
around them.

**Shape.** `grid(...)`, `page(...)`/`container(...)`, `stack(...)` (Python + R)
whose classes are **baked into the JS bundle** (always generated, never
silently dropped) and pre-hardened against Shiny's unlayered Bootstrap. The grid
helper should encapsulate a *working* responsive approach rather than exposing raw
`md:` prefixes (which lose to Bootstrap — see "do not adopt" below).

### 3. Theming / dark mode

**Gap.** `js/src/styles.css` defines light-only `@theme` tokens — no `.dark`
variant, no toggle path. Theming is shadcn's signature feature.

**Why it matters.** A stated direction rather than urgent work, but it's a core
part of what makes shadcn *shadcn*. Worth designing the token set + `.dark` variant
+ a toggle story before the API ossifies.

**Shape.** TBD — CSS-variable token set with a `.dark` scope, plus a documented way
to switch themes (server-driven message handler, or a client toggle).

---

## Explicitly NOT goals (rejected after review)

- **Coarse-grained composite components as API** (e.g. a `TextInputCard` bundling
  an input + two outputs, like `examples/app-py/05-shadcn`). This contradicts the
  atomic-primitive design, which is intentional. Ship such combinations as example
  *recipes* instead — pedagogically useful, not package API.
- **Raw responsive `md:` grid prefixes.** They work in `ui-tsx/04-shadcn` only
  because that example has its own Tailwind build with no Bootstrap. Inside Shiny's
  Bootstrap page they lose. Encapsulate responsiveness in the layout helper (#2)
  instead of exposing the prefixes.

---

## Packaging / formalization

### Convert to formal package format (like shinyreact core)

The API and JS bundle are mature enough to formalize; the scaffolding and tests are
not yet there. Intended name (already used by both `HTMLDependency` objects):
**`shinyshadcn`**.

- **Python:** `pkg-py/pyproject.toml` (hatchling, mirror core), `src/shinyshadcn/`
  layout, bundle `www/` as package data so `_dep()` reads the package path (drop the
  `../../www` relative hack), pytest wire-format tests.
- **R:** DESCRIPTION + NAMESPACE + `R/` + `man/` + `inst/` for the bundle. Roxygen
  comments already exist on the helpers (head start for `man/`). `dep()` reads
  `system.file(package = "shinyshadcn")` instead of taking an absolute `www_dir`.
  testthat tests + Py↔R wire-format parity fixtures.
- **Decisions to make:** confirm `shinyshadcn` for both; keep the R `shadcn_` prefix
  or drop it once there's a namespace; resolve the **vendoring** question (how the
  `www/` JS ships in the wheel / `inst` — pin vs vendor).
- **Blocker:** there are currently **zero tests** (Python, R, or shadcn JS). Core
  models all three (pytest, testthat, vitest); formalization should land *with* a
  test suite, not after.

---

## Smaller follow-ups

- **Hook type declarations should live in core.** `js/src/shinyreact.d.ts` (the
  ambient `declare module "shinyreact"` typing the 8 hooks) is an interim copy.
  Core owns the API and is fully TypeScript; it should export these so every
  downstream framework references them instead of re-declaring.
- **Keyword-only consistency for dict-builders.** `crumb` / `nav_item` (Python + R)
  have optional *positional* args, the one deviation from the "optionals are
  keyword-only" convention. Low-stakes, but worth aligning.
- **No R shadcn example at root.** `examples/app-r/` and `examples/ui-tsx-r/` have no
  shadcn coverage; only Python (`app-py/05-shadcn`) and JS (`ui-tsx/04-shadcn`) do.
- **No root example consumes the package.** The root `examples/` reimplement
  shadcn-styled components locally; none `import shadcn as sc`. The package-consuming
  story lives only under `ui-frameworks/shadcn/examples/`.
