# Changelog

Significant changes to `ui-frameworks/`. Newest first. This is a running log of
*decisions and milestones* — for the rationale behind the initial shadcn refactor
(before/after of the file structure), see [updates.md](updates.md).

Dates are absolute. This directory is a prototype area; entries are grouped by
working milestone rather than published versions.

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
