# Changelog

Significant changes to `ui-frameworks/`. Newest first. This is a running log of
*decisions and milestones* — for the rationale behind the initial shadcn refactor
(before/after of the file structure), see [updates.md](updates.md).

Dates are absolute. This directory is a prototype area; entries are grouped by
working milestone rather than published versions.

---

## 2026-06-11 — Hooks consumed as an external module (removed `hooks.js`)

Replaced the hand-written `src/hooks.js` shim with bundler externalization —
treating the host's `window.shinyreact` global the same way React is already
treated.

- **Why:** `hooks.js` did `export const { useShinyInput, … } = window.shinyreact`
  — an *eager destructure of a runtime global at module-eval time*, plus a
  hand-maintained hook list that had to stay in sync with core. That reinvented,
  by hand, what `vite.config.js` already does for `react` / `react-dom/client`.
  `window.shinyreact` is a host-injected runtime dependency — architecturally
  identical to React — so it should be an *external*, not a local file reaching
  into a global.
- **Change:** added `shinyreact` to `rollupOptions.external` + `output.globals`
  (→ `window.shinyreact`). The 28 component bridges now
  `import { useShinyInput } from "shinyreact"`; the bundler rewrites named imports
  to property access on the global and tree-shakes unused ones. Deleted
  `src/hooks.js`.
- **Types:** new `src/shinyreact.d.ts` (ambient `declare module "shinyreact"`)
  types all 8 hooks for editor IntelliSense. Interim — these declarations
  ultimately belong in the core package (fully TS, owns the API).
- **Verified:** build clean; `useShinyInput` appears exactly 28× (call sites) with
  zero bundled implementation — confirming it resolves through the injected
  global. App boots, no errors. Runtime is unchanged by construction (same global,
  same property; lazy access instead of eager destructure).

Skill (`scaffold-component`), shadcn README, and updates.md §2 updated to the
`from "shinyreact"` import path.

---

## 2026-06-11 — Component Explorer gallery (`shinyreact-shadcn`, Python + R)

New standalone gallery `examples/shinyreact-shadcn/` (app.py + app.R) — a
reference explorer showing **all 47 components, every variant, individually**
(no combined demos). The existing `gallery-py`/`gallery-r` is left as-is. Layout:
hero + a category toggle-group nav (Inputs/Display/Overlays/Navigation/Layout/
Feedback) that lazily renders one category at a time; each component is a section
of variant cards in an even 2-column grid (`col-span-2` for wide content).

Two skill-documented anti-patterns were hit while building it, and fixed per the
skill's prescription (worth re-stating since they recur):

- **No string `style=` inside a `render_react` tree** (React error #62). The
  first draft set `style="position:sticky; …"` on wrapper divs *inside* the
  rendered tree. Moved the only legitimate inline style to the page-chrome div
  wrapping `output_react` (outside the React tree — the one safe place); every
  in-tree wrapper uses `class_=` Tailwind.
- **App-only Tailwind classes silently no-op** — Tailwind scans `js/src`, not app
  files, so `max-w-screen-xl`, `bg-card`, `col-span-2`, `size-10`, `w-5/6`, etc.
  were never compiled. Registered the gallery's full class vocabulary via
  `@source inline(...)` in `styles.css` and added a `.shinyreact-output
  .col-span-2` Bootstrap-precedence override (next to the existing grid-cols
  overrides). Dropped Bootstrap-fighting bits (responsive `xl:`/`sm:` grid
  prefixes, sticky/backdrop) for a robust fixed `grid-cols-2` + `col-span-2`.

Verified both languages: all 47 sections render and serialize to the wire format
(Python ~140 KB across 6 categories; R 47 sections); both servers boot HTTP 200;
`ruff` clean, R formatted with `air`.

---

## 2026-06-11 — `finalize-component.mjs` + scaffold-component skill overhaul

Completed the two-phase codegen workflow and made the skill strict/checklist-driven.

- **`js/scripts/finalize-component.mjs`** — the "after" half of the loop: reads a
  machine-readable `@shiny` annotation in the bridge block and *idempotently*
  inserts the `index.jsx` import + registry entry, appends the Python helper
  (multi-line signature, always < 88 chars), and appends the R helper (aligned
  props list, `check_dots_empty()` on leaves / `...` on containers). `class_`→
  `className` / `class` mapping handled; required props → positional, optional →
  keyword-only. Derives snake-case names from the *export* name (handles
  `sonner.jsx → Toaster → toaster`).
- **`prep-component.mjs`** — bridge stub now emits the `@shiny` annotation
  template; printed instructions describe the two-phase (prep → fill → finalize)
  flow.
- **`scaffold-component.md`** — comprehensive rewrite: two-phase workflow diagram,
  `@shiny` annotation format table, pre-flight/bridge/post-bridge checklists, 12
  strict rules, copy-paste bridge patterns for all 8 component types, a
  symptom→cause→fix gotchas table, API conventions, and the npm-package table.
  `scaffold-framework.md` gained the pre-commit-hook behavior notes.

Per-component cost is now: `prep` (deterministic, zero tokens) → fill bridge +
`@shiny` annotation (judgment only) → `finalize` (deterministic, zero tokens) →
build. The annotation doubles as the machine-readable record of each component's
API surface.

---

## 2026-06-11 — Empty, Pagination + gallery expanded (45 → 47)

Two Tier-1 components wrapped + gallery updated to 7 tabs.

- **Empty** (Display/Container): `title`, `description`, children = action area.
  Sub-components: `EmptyHeader`, `EmptyTitle`, `EmptyDescription`, `EmptyContent`.
- **Pagination** (Input): `input_id` tracks 1-based current page. Props:
  `total_pages`, `current`, `show_ellipsis`. Renders prev/next + page number
  buttons; ellipsis collapses distant pages. `PaginationLink` clicks use
  `e.preventDefault()` (renders as `<a>`).

**Gallery** (`examples/gallery-py/app.py`) expanded from 4 → 7 tabs: new
**Overlays** (Drawer, ContextMenu, ScrollArea), **Navigation** (Menubar,
NavigationMenu, Command), **Layout** (Carousel, Resizable) tabs added. Existing
tabs updated with Tooltip, HoverCard, Empty, Chart (Display), AlertDialog +
Sheet (Actions), OTP + Pagination (Inputs).

---

## 2026-06-11 — Tier 3 wrap: Carousel, InputOtp, Resizable, Chart (41 → 45)

Four complex components wrapped directly (no agent delegation — reasoning about
the bridge design mattered more than parallelism here).

- **Carousel** (Hybrid): `embla-carousel-react`. Children = slides; each wrapped
  in `CarouselItem`. Optional `input_id` tracks current 0-based slide index via
  `api.on("select")`. Hook called unconditionally with `__noop_carousel__` guard.
- **InputOtp** (Input): `input-otp` library. Props: `length` (slot count),
  `separator` (dash between halves). Renders `InputOTPGroup`+`InputOTPSlot` array
  dynamically.
- **Resizable** (Container): `react-resizable-panels`. Children matched to panels
  positionally; `ResizableHandle` auto-inserted between each pair. `panels` array
  controls `defaultSize`/`minSize` per panel.
- **Chart** (Display): `recharts` via shadcn's `ChartContainer`. Supports bar,
  line, area, pie via `type` prop. `series` array maps `{key, label, color}` →
  CSS variable injection via `ChartStyle`. PALETTE fallback for unspecified colors.
  `chart_series()` / `shadcn_chart_series()` helper for series specs.

New npm deps: `embla-carousel-react`, `input-otp`, `react-resizable-panels`,
`recharts` (all bundled). Bundle grew to 919 kB / 268 kB gzip (recharts is heavy).

Deferred: `sidebar` (726-line source, too many sub-parts), `form`
(react-hook-form coupling). Can revisit when needed.

---

## 2026-06-11 — Parallel-agent batch 5 (36 → 41)

Second parallel batch. Same pattern: prep scripts → 5 Sonnet agents (bridges
only) → main integrates + builds once.

**Components**: Drawer (Overlay, vaul, `direction` prop), ContextMenu (Collection,
right-click trigger = children), Menubar (Collection, horizontal bar of menus,
fires `{menu, value, nonce}`), NavigationMenu (Collection, data-driven nav links
+ dropdowns, optional `input_id` for click tracking), Command (Input+Collection,
cmdk-powered filterable palette, `items`/`group` grouping).

New npm deps installed: `vaul`, `cmdk` (bundled, not externalized).

Import-order fix: agents placed `import { useShinyInput }` after the bridge
comment (mid-file) — rolled those to the top before building. Build: 931ms,
zero errors.

---

## 2026-06-11 — Parallel-agent batch 4 (31 → 36)

First batch wrapped with parallel Sonnet agents. 5 prep scripts ran first
(`prep-component.mjs` for each), then 5 agents filled the bridges concurrently —
each scoped to one `.jsx` file only. Main session integrated registry + helpers
serially and built once.

**Components**: ScrollArea (Container: `height`/`orientation`), Tooltip (Display:
`content`/`side`), HoverCard (Display: `trigger_label` hover trigger + children
card body), AlertDialog (Action: `confirm_id`/`cancel_id` counters via
`debounceMs:0, priority:"event"`, hooks called unconditionally with `__noop_*__`
fallback ids), Sheet (Overlay: `input_id` open-state + `side` prop, same shape as
Dialog/Collapsible).

Wall-clock: 5 bridges in parallel vs sequential. Shared-file contention avoided
by keeping agents author-only (no index.jsx / py / R writes). Zero build errors.

---

## 2026-06-11 — Bulk wrap batch 3 via the script (27 → 31)

ToggleGroup, Breadcrumb, Collapsible, Accordion. Patterns: ToggleGroup =
single/multi Input over choices; Breadcrumb = Display collection (crumb items);
Collapsible = Overlay-lite (open-state + children); Accordion = Hybrid (items
metadata + positional panels + open-state input). Exported `toggleVariants`
from toggle.jsx so toggle-group can share the cva. Smoke-tested, zero JS errors.

---

## 2026-06-11 — Bulk wrap batch 2 via the script (23 → 27)

First batch wrapped with `prep-component.mjs`: **Kbd, Spinner, AspectRatio,
RadioGroup**. The script did the strip/scaffold; only the bridges were filled by
hand (RadioGroup is a single-select Input over a `choices` array; the rest are
Display/Container). Registered + Python + R helpers. Smoke-tested: kbd/spinner
render, radio group selects (size=lg on click), zero JS errors. The script made
this noticeably faster per component.

---

## 2026-06-11 — Codegen script + Toggle (22 → 23)

Built `js/scripts/prep-component.mjs` to do the mechanical, token-heavy part of
wrapping: esbuild strips TypeScript (keeps JSX), drops `"use client"`,
neutralizes shadcn `export`s, fixes import paths, appends a bridge stub, writes
`src/components/<name>.jsx`, and prints the `index.jsx` + Python/R stubs. Claude
only fills the fuzzy bridge logic now — no reading/transcribing the `.tsx`.

Validated end-to-end on **Toggle** (component #23): `prep-component.mjs toggle`
→ filled the Input/boolean bridge → registered + Python/R helpers (variant +
size) → built → clicking toggles the boolean input. Zero JS errors.

Skill (`scaffold-component`) Steps 1–2 rewritten around the script; the "registry
as source of truth" section updated from "not yet built" to the live workflow +
token rationale.

---

## 2026-06-11 — Bulk wrap batch 1 (17 → 22 components)

Started scaling toward the full shadcn set. Batch 1 (trivial Display/Input,
no new deps): **Textarea, Label, Skeleton, Progress, Avatar** — JS bridges +
Python + R helpers + registry. Smoke-tested: all render, zero JS errors.

Remaining ~34 to go, by tier:
- Tier 1 (trivial, next): toggle, toggle-group, radio-group, aspect-ratio, kbd,
  spinner, breadcrumb, pagination, empty.
- Tier 2 (overlay/collection repeats): sheet, drawer, tooltip, hover-card,
  alert-dialog, collapsible, accordion, context-menu, menubar, navigation-menu,
  scroll-area, command.
- Tier 3 (involved): sidebar, carousel, resizable, input-otp, form, chart.
- Skip/defer: combobox (Base UI, not Radix), native-select, direction, and the
  layout helpers (field, item, input-group, button-group).

---

## 2026-06-11 — Variants gallery + expanded button/badge options

Sizing default corrected first: container base was 14px (too small); set to 16px
(shadcn's real base) and re-assert text-* utilities so controls keep their own
text-sm — the whole UI no longer feels shrunk.

Exposed the variants/sizes the cva already supported but the helpers didn't:
- `button`: variant now default/secondary/destructive/outline/ghost/link; new
  `size` arg (default/sm/lg/icon) — JS bridge forwards `size`.
- `badge`: variant expanded to the full six.

New **variants gallery** (`examples/variants-py`, `examples/variants-r`): a
reference sheet showing each component across its variants, sizes, and states in
rows — plus className customizations (custom color button, pill, colored badge)
to show the override path. Both verified by screenshot, zero JS errors.

---

## 2026-06-11 — Skill revision (captured session learnings)

Revised `scaffold-component` and `scaffold-framework` with everything learned
shipping the components:

- **scaffold-framework Step 7 (styles.css)** rewritten as the most important
  file — the full Bootstrap-interop compat layer (typography reset, grid-cols
  override, `@source inline`, tokens), with the "Bootstrap-unlayered-beats-
  Tailwind-layered" explanation. Was previously just color tokens.
- **scaffold-framework Step 14** now requires *visual* verification (screenshot +
  measure computed sizes), since text assertions pass on broken layouts.
- **scaffold-component**: className passthrough is now a documented standard
  (bridge forwards it + `class_`/`class` helper arg + cn merge); added
  "don't hard-code layout (no `w-full`)" rule; gotchas point to the styles.css
  compat layer and `@source inline` as the fixes for size/grid issues.

---

## 2026-06-11 — Better defaults + redesigned gallery

Root cause of "components look off": **Shiny loads Bootstrap unlayered**, so it
beat Tailwind's layered utilities on every element it targets — bare headings
(card title rendered at Bootstrap's 28px), form controls (inputs at 16px not
14px), and even `.grid` (Bootstrap's 12-column grid overrode `grid-cols-2`).
shadcn's own sizes were correct; Bootstrap was inflating them.

Fixes in `styles.css` (unlayered compat layer, scoped to `.shinyreact-output`):
- Typography reset: system font stack + antialiasing, 14px base, headings
  inherit (no Bootstrap h1–h6 sizes), form controls inherit the font.
- Re-assert `grid-cols-1/2` with `!important` to beat Bootstrap's `.grid`.
- `@source inline(...)` to force-generate layout utilities used only in apps
  (`grid`, `grid-cols-2`, `flex-wrap`, …) — Tailwind scans `js/src`, not apps.
- Added `--radius` token.
- Card: `<h3>` title → `<div>` (avoids Bootstrap heading), shadcn padding (px-6).

Result (verified by screenshot): input 16→14px, card title 28→18px, system
font, correct spacing.

Redesigned gallery (Python + R): a real showcase — header with title/subtitle,
each component in a labeled preview box (shadcn-docs style), 2-column grids
where compact, full-width where the content needs it. Both verified, zero JS
errors.

---

## 2026-06-11 — className arg on every component (Python + R + JS)

Completed the className passthrough Barret asked for — end to end now:

- **JS bridges**: every one of the 14 component bridges destructures
  `className` from `element.props` and forwards it to the root via
  `cn(componentClasses, className)` (cva sets defaults, tailwind-merge lets the
  caller win). Lands on the sensible root per type — wrapper for inputs, content
  panel for overlays/menus, root element for display/table/tabs.
- **Python**: every component helper gains `class_: str | None = None`
  (keyword-only), sent as `props["className"]`.
- **R**: every component helper gains `class = NULL`, sent as
  `props$className`. (Matches htmltools' `class` convention.)

Verified end to end: a custom class reaches the DOM and coexists with the
variant classes (`cn` merge), Python↔R wire parity holds, keyword-only
enforcement still rejects positional optionals, zero JS errors. Existing
examples unaffected (className is optional).

---

## 2026-06-11 — Re-adopt class-variance-authority (cva) + className passthrough

Brought back `cva` (we'd removed it earlier) so variant components stay faithful
to shadcn source and get `defaultVariants` / compound variants for free — the
lowest-edit path for scaling, and what Barret wants for "good defaults, ready to
use."

- `button-base`, `badge`, `tabs` restored to real `cva(...)`; `badge` and `alert`
  upgraded from hand-rolled markup to faithful shadcn source with bridges.
- **className passthrough**: components destructure `className` and merge it last
  via `cn(fooVariants({variant}), className)` (cva = defaults, tailwind-merge =
  caller override). Bridges forward `element.props.className`.
- **Alert adaptation**: shadcn's new Alert uses an icon-reserving grid
  (`grid-cols-[0_1fr]` + `col-start-2`) that collapses the text column when there's
  no icon — our alerts have none, so kept the cva variant colors but used a plain
  block layout. (Caught visually; text was wrapping one word per line.)

Verified: gallery renders cleanly (badges, both alert variants, all tabs),
zero JS errors. Skill gotchas updated (cva is now kept, not stripped).

---

## 2026-06-11 — API conventions: keyword-only optionals (Python + R)

Applied the agreed argument convention across every component helper so
positional misuse is impossible and new optional args stay backward-compatible:

- **Leaf components** (scalar options): required args first, then optionals are
  keyword-only — Python `def x(req, *, opt=…)`; R `function(req, ..., opt=…)`
  with `rlang::check_dots_empty()` reserving `...` as a guarded separator.
- **Container components** keep `...` / `*children` for child nodes (mirrors
  `node(type, ...)`, per Barret); their optional scalars sit after the children
  sink and are keyword-only too — no `check_dots_empty()` there.

Verified both languages: positional optionals now error, wire format unchanged,
no example relied on positional optionals.

Skill (`scaffold-component`) updated with the API-conventions table, a note that
it's framework-generic (shadcn is just the running example), and a **registry as
source of truth** section describing the script-plus-Claude codegen direction
(script derives wrapper surface from the `registerComponents` map + TS types;
Claude fills the per-component semantics).

---

## 2026-06-10 — Component gallery (Python + R)

Added `examples/gallery-py` and `examples/gallery-r` — a single showcase app
displaying all 17 components, organized with Tabs into Inputs / Display /
Actions / Feedback, every panel live-wired. Both verified with Playwright
(identical results, zero console errors).

Also: `dropdown-menu` event input gained `debounceMs: 0` to match the button's
event semantics; verified Python↔R wire-format parity across the five
hard components.

**Button is now auto-width** (was hardcoded `w-full`). Full-width broke any
horizontal layout — in the gallery it shoved sibling triggers out of the card —
and was unfaithful to shadcn, whose buttons are content-width. Standalone form
buttons now render at their natural size.

**Two findings (now in the scaffold-component skill):**
- **No string `style=` inside a `render_react` tree** — React throws error #62.
  Use `class_=`/`class =` with Tailwind utilities; string `style=` is only safe
  on page-chrome tags outside `output_react`.
- **Tailwind ships only utilities it sees in `js/src`** — classes used solely in
  an app (e.g. `flex-wrap`, `grid-cols-2`) silently no-op. Stick to utilities a
  component already uses.

---

## 2026-06-10 — shadcn hard-component learning phase

Wrapped five "hard" components to prove the bridge architecture before
bulk-wrapping the remaining ~39. All verified end-to-end with Playwright
(zero console errors); Python↔R wire format confirmed identical.

**Components added (shadcn): 12 → 17**
- `DropdownMenu` — first compound component (15 subcomponents → one data-driven bridge)
- `Table` — display via `columns`/`rows` data props
- `Tabs` — hybrid: tab metadata prop array + positionally-matched panel children
- `Sonner`/`Toaster` — server-push via `send_message` + `useShinyMessageHandler`
- `Calendar` — single-date picker; value crosses the wire as an ISO `"YYYY-MM-DD"` string

**Component taxonomy expanded to 7 types.** Display, Container, Input, Action,
Overlay, **Collection** (data-driven item list), **Hybrid** (metadata prop +
positional children), **Push** (server pushes, no input). Every remaining shadcn
component maps to one of these — no unknown patterns left.

**New shared primitive: `js/src/lib/button-base.jsx`.** shadcn's `Button` +
`buttonVariants` extracted so cross-component importers (Calendar) and the Button
bridge both use one source. `class-variance-authority` inlined as plain objects
(the project has no cva dependency).

**New npm dependencies (bundled, not externalized):** `sonner`, `react-day-picker`.
The calendar roughly doubled the gzip bundle (44 kB → 85 kB).

**Skills updated** (`scaffold-component.md`, `scaffold-framework.md`):
- Added Collection / Hybrid / Push patterns with bridge examples
- Documented the two event-input idioms (counter vs nonce), `!!` boolean
  coercion, ISO-string dates, cross-component imports, cva inlining,
  stripping `next-themes`, dropping unused `import * as React`
- Step 6 now requires a wire-format test + R parity check, not just "run the app"
- Fixed a latent bug in the Sonner skill example (`toast["default"]` throws)

**Tooling:** `shadcn/download-components.sh` fetches all 56 new-york-v4 sources
into a gitignored `js/src/components-src/` staging dir for local wrapping.

**Known limitations:**
- R single-column table rows auto-unbox to a scalar and would break the JS
  `.map` (multi-column is fine). Use `I()` to force an array if needed.
- New components ship Python examples only; R examples not yet added.
- `combobox` uses `@base-ui/react` (shadcn is mid-migration), so it will not
  follow the `radix-ui` pattern — handle separately or skip.

---

## 2026-06-10 — Foundation: shadcn component library

Initial `ui-frameworks/shadcn` — 12 shadcn components wired to Shiny via
shinyreact, usable from Python and R with no installation.

- Components: Alert, Badge, Button, Card, Checkbox, Dialog, Input, Popover,
  Select, Separator, Slider, Switch
- Single file per component (shadcn source + shinyreact bridge together);
  overlay components use real Radix primitives with full a11y
- `react-dom` bundled (not externalized) so Radix portals get `createPortal`
- Shared `hooks.js` and `lib/trigger-button.jsx`; `export { ShinyFoo as Foo }`
- Consolidated `llms.txt` + `llms-full.txt` at repo root; READMEs for
  `ui-frameworks/` and `shadcn/`
- Rewrote `scaffold-component` / `scaffold-framework` skills for the
  single-file architecture

See [updates.md](updates.md) for the before/after detail of the refactor.
