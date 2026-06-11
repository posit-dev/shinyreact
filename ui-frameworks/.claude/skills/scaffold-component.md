# scaffold-component

Add one new component to an existing ui-frameworks framework (shadcn, mui, etc.).

This skill is **framework-generic**. shadcn is the running example because it's the
most-built-out target, but the taxonomy, bridge patterns, and API conventions apply to
any React component library (MUI, Mantine, Base UI, custom). Keep new guidance generic;
put genuinely framework-specific notes in clearly-labeled sections (see "shadcn-specific
notes") so they don't leak into the core workflow. If a framework needs so much special
handling that the core no longer fits, that's a signal to ship a dedicated package for it
rather than bend this skill.

## When to use

When the user says "add a `<ComponentName>` component to shadcn/mui/…" or "wrap `<LibraryComponent>` for shinyreact."

---

## Step 0 — Identify component type

Every component falls into one of seven types. The type determines which hook to use and how to structure the bridge.

| Type | Hook | Contents via | Examples |
|------|------|------|---------|
| **Display** | none | props (incl. `columns`/`rows` for data) | Badge, Alert, Separator, Table |
| **Container** | none | `children` | Card |
| **Input** | `useShinyInput` | props | Input, Slider, Select, Checkbox, Switch, Calendar |
| **Action** | `useShinyInput` with event opts | props | Button |
| **Overlay** | `useShinyInput` for open state + `children` | `children` | Dialog, Popover, Sheet |
| **Collection** | mix of event + state inputs | `items` prop array | DropdownMenu, Menubar, ContextMenu |
| **Hybrid** | `useShinyInput` | metadata prop array **+** positional `children` | Tabs, Accordion |
| **Push** | `useShinyMessageHandler` (no input) | nothing — server pushes | Sonner/Toaster |

**How to choose when contents are nested:**
- *Free-form* content (arbitrary nodes the author arranges) → `children`. Container/Overlay.
- *Structured list of known item kinds* (menu actions, options) → data-driven `items` prop array + item-builder helpers. Collection.
- *Structured triggers paired with free-form panels* (each tab has a label AND a content panel) → metadata prop array for the triggers + `children` for the panels, matched **positionally**. Hybrid. The bridge uses `React.Children.toArray(children)[i]` — it does not read child props.

**Push is the inverse of Input.** It has no trigger and no input value — the server *pushes* to it via `send_message()`, and the bridge listens with `useShinyMessageHandler`. Mount it once; it renders nothing until a message arrives.

---

## Step 1 — Run the prep script (shadcn)

**Don't read/strip the `.tsx` by hand — the script does the mechanical, token-heavy
parts.** From `js/`:

```bash
node scripts/prep-component.mjs <name>     # e.g. toggle
```

It reads `src/components-src/<name>.tsx` (download once via `download-components.sh`),
strips TypeScript (keeps JSX), drops `"use client"`, neutralizes the shadcn `export`s,
fixes import paths (`@/registry/.../ui/X` → `@/components/X`; button → `@/lib/button-base`),
appends a bridge stub, and writes `src/components/<name>.jsx`. It then prints the exact
`index.jsx` lines and Python/R helper stubs to paste in Steps 3–5.

You only do the **fuzzy** part: open the written file, look at the props/exports the script
left, and fill the bridge (Step 2). You generally don't need to read the original `.tsx`.

### npm library (MUI, Mantine, etc.)

No source to strip — write the file by hand importing from the npm package (the structure
below). Skip the script.

---

## Step 2 — Fill the bridge stub

The script wrote `src/components/<name>.jsx` = shadcn source (stripped) + a TODO bridge
stub. Replace the stub with the real bridge: pick the component type, wire the hook, read
`element.props`, forward `className`. Final shape:

```jsx
import * as React from "react";
import { ComponentPrimitive } from "radix-ui";   // (script kept the source's imports)
import { cn } from "@/lib/utils";
import { useShinyInput } from "@/hooks";          // add if the component needs a hook

// --- shadcn source (written by the script; leave as-is) ---
function ComponentName({ className, ...props }) { /* … */ }

// --- shinyreact bridge (you fill this) ---
// Props: input_id (str), label (str, optional), className (str, optional), ...
function ShinyComponentName({ element, children }) {
  const { input_id, label, default_value = "", className } = element.props;
  const [value, setValue] = useShinyInput(input_id, default_value);
  return (
    <ComponentName value={value} onChange={setValue} className={className}>
      {children}
    </ComponentName>
  );
}

export { ShinyComponentName as ComponentName };
```

(For an npm-library framework with no script, write the whole file in this shape by hand.)

**Every bridge forwards `className`.** Destructure `className` from `element.props`
and pass it to the component's root, which merges it last via
`cn(componentClasses, className)` — variant defaults come from cva, the caller's
class wins on conflict (tailwind-merge). For a hand-rolled root, wrap its class
string in `cn("...", className)` and add a `cn` import. This pairs with the
`class_` (Python) / `class` (R) helper arg (Steps 4–5) so app authors can restyle
any component. Lands on the sensible root: wrapper for inputs, content panel for
overlays/menus, root element for display/table/tabs.

**Don't hard-code layout into a component.** Width/margin/placement are the
caller's job — e.g. the button is auto-width, *not* `w-full`; a baked-in `w-full`
breaks every horizontal row. Ship only the component's own look; let `className`
and the parent layout decide size and position.

**Why `export { ShinyFoo as Foo }`:** The bridge function is named `ShinyFoo` to avoid clashing with the shadcn source function `Foo` defined above it in the same file. The exported name is clean.

**Use the `ShinyFoo as Foo` form for every component, even when there's no clash.**
Trivial components with no shadcn source function (Badge, Alert, Card, Separator, Input)
*could* write `export function Badge({ element })` directly, but using the same
`ShinyBadge` + `export { ShinyBadge as Badge }` shape everywhere means every file reads
the same way and a reader always knows which function is the bridge. Consistency beats
saving two lines.

### Hook patterns by type

**Display / Container — no hook:**
```jsx
function ShinyBadge({ element }) {
  const { text, variant = "default" } = element.props;
  return <Badge variant={variant}>{text}</Badge>;
}

function ShinyCard({ element, children }) {
  const { title } = element.props;
  return <Card>{title && <CardHeader>{title}</CardHeader>}{children}</Card>;
}
```

**Input — `useShinyInput`:**
```jsx
function ShinyInput({ element }) {
  const { input_id, placeholder = "", label, debounce_ms = 250 } = element.props;
  const [value, setValue] = useShinyInput(input_id, "", { debounceMs: debounce_ms });
  return <Input value={value} placeholder={placeholder} onChange={(e) => setValue(e.target.value)} />;
}
```

**Action — two event idioms.** Both use `priority: "event"` and `debounceMs: 0`
(so rapid actions are not coalesced). Pick by whether the bridge needs to *read*:

*Counter idiom* — when there's nothing to send but "it happened." Read+increment,
so use the full `useShinyInput`:
```jsx
function ShinyButton({ element }) {
  const { input_id, label, variant = "default" } = element.props;
  const [count, setCount] = useShinyInput(input_id, 0, { debounceMs: 0, priority: "event" });
  return <Button variant={variant} onClick={() => setCount(count + 1)}>{label}</Button>;
}
```
*Nonce idiom* — when the action carries a payload (which menu item, which row). Write-only,
so use `useSetShinyInput`; attach a nonce so repeat-firing the *same* payload still registers:
```jsx
const setSelected = useSetShinyInput(input_id, null, { debounceMs: 0, priority: "event" });
const onSelect = (value) => setSelected({ value, nonce: Date.now() });
```
Server (both): `@reactive.event(input.btn, ignore_init=True)` — `ignore_init=True` prevents
firing on page load. Counter reads `input.btn()`; nonce reads `input.btn()["value"]`.

**Overlay — open state + children:**
```jsx
import { TriggerButton } from "@/lib/trigger-button";

function ShinyDialog({ element, children }) {
  const { input_id, trigger_label = "Open", title } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <Dialog open={!!open} onOpenChange={setOpen}>
      <DialogTrigger asChild><TriggerButton>{trigger_label}</TriggerButton></DialogTrigger>
      <DialogContent>
        {title && <DialogTitle>{title}</DialogTitle>}
        {children}
      </DialogContent>
    </Dialog>
  );
}
```
Server reads `input.<input_id>()` as `True`/`False` while the overlay is open.

**Always coerce round-tripped booleans with `!!`.** A value that came back from
Shiny (restored bookmark, server-set) may arrive as `0/1`, `null`, or `undefined`
rather than a strict boolean. Radix `checked`/`open` props want a real boolean, so
write `checked={!!checked}` / `open={!!open}` — never pass the raw value. This applies
to Checkbox, Switch, Dialog, Popover, and checkbox menu items.

**Slider — Radix uses array values, bridge wraps/unwraps:**
```jsx
const [value, setValue] = useShinyInput(input_id, default_value);
<Slider value={[value]} onValueChange={([v]) => setValue(v)} />
```

**Collection — data-driven `items` array, mixed event + state inputs:**

Compound components with many subcomponents (DropdownMenu exports 15) are bridged
as a *single* component fed by an `items` data array — not by registering every
subcomponent. Keep all shadcn subcomponents as verbatim source; the bridge uses
only the subset it needs and walks `items` recursively.

```jsx
function MenuItems({ items, onSelect }) {
  return items.map((item, i) => {
    switch (item.type) {
      case "label":     return <DropdownMenuLabel key={i}>{item.label}</DropdownMenuLabel>;
      case "separator": return <DropdownMenuSeparator key={i} />;
      case "checkbox":  return <CheckboxMenuItem key={i} item={item} />;
      case "submenu":
        return (
          <DropdownMenuSub key={i}>
            <DropdownMenuSubTrigger>{item.label}</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <MenuItems items={item.items ?? []} onSelect={onSelect} />  {/* recursion */}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        );
      default:          // "item"
        return <DropdownMenuItem key={i} onSelect={() => onSelect(item.value)}>{item.label}</DropdownMenuItem>;
    }
  });
}

function ShinyDropdownMenu({ element }) {
  const { input_id, trigger_label = "Open", items = [] } = element.props;
  const setSelected = useSetShinyInput(input_id, null, { priority: "event" });
  // Event nonce: a plain string would be deduped by Shiny, so clicking the same
  // item twice would not re-fire. The nonce forces a distinct value each click.
  const onSelect = (value) => setSelected({ value, nonce: Date.now() });
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild><TriggerButton>{trigger_label}</TriggerButton></DropdownMenuTrigger>
      <DropdownMenuContent><MenuItems items={items} onSelect={onSelect} /></DropdownMenuContent>
    </DropdownMenu>
  );
}
```

Two input kinds coexist in one Collection:
- **plain items are events** → reported through the component's own `input_id` (with nonce)
- **stateful items (checkbox/radio) own separate inputs** → each gets its own `input_id` and `useShinyInput`

```jsx
function CheckboxMenuItem({ item }) {
  const [checked, setChecked] = useShinyInput(item.input_id, item.checked ?? false);
  return (
    <DropdownMenuCheckboxItem
      checked={!!checked}
      onCheckedChange={setChecked}
      onSelect={(e) => e.preventDefault()}  // keep the menu open while toggling
    >
      {item.label}
    </DropdownMenuCheckboxItem>
  );
}
```

Server reads the event input as a dict: `input.<input_id>()["value"]`, paired with
`@reactive.event(input.<input_id>, ignore_init=True)`. Stateful items are read
independently: `input.<checkbox_input_id>()`.

For the Python/R side, provide **item-builder helpers** that return plain dicts/lists
(`menu_item`, `menu_label`, `menu_separator`, `menu_checkbox`, `menu_submenu`) rather
than making authors hand-write dicts. `menu_submenu(label, *items)` nests recursively.

**Hybrid — metadata prop array + positional children:**

When each "item" pairs a structured trigger with a free-form content panel (tabs,
accordion), pass the trigger metadata as a prop array and the panels as `children`,
matched by index. The bridge never reads child props — only their order.

```jsx
function ShinyTabs({ element, children }) {
  const { input_id, tabs = [], selected } = element.props;
  const [value, setValue] = useShinyInput(input_id, selected ?? tabs[0]?.value ?? "");
  const panels = React.Children.toArray(children);  // index-matched to tabs
  return (
    <Tabs value={value} onValueChange={setValue}>
      <TabsList>{tabs.map((t) => <TabsTrigger key={t.value} value={t.value}>{t.label}</TabsTrigger>)}</TabsList>
      {tabs.map((t, i) => <TabsContent key={t.value} value={t.value}>{panels[i]}</TabsContent>)}
    </Tabs>
  );
}
```
Python: `tabs(input_id, [tab("a","A"), tab("b","B")], panel_a, panel_b)` — panels are
`*children` after the `tabs` metadata list. R: `shadcn_tabs(id, tabs, panel_a, panel_b)`.

**Push — server pushes, no input:**

A Push component has no trigger and no input value. It renders a host once and
listens for server messages. This is the inverse of Input.

```jsx
function ShinyToaster({ element }) {
  const { message_type = "toast", position = "bottom-right" } = element.props;
  useShinyMessageHandler(message_type, (data) => {
    const { message, description, type = "default" } = data ?? {};
    // Do NOT do toast[type](...) — sonner has no toast.default, so the common
    // type="default" would throw. Select explicitly and fall through to toast().
    const fn =
      type === "success" ? toast.success
      : type === "error" ? toast.error
      : type === "warning" ? toast.warning
      : type === "info" ? toast.info
      : type === "loading" ? toast.loading
      : toast;
    fn(message, { description });
  });
  return <Toaster position={position} />;  // renders nothing until a message arrives
}
```
Pair with a server-side push helper, not a Node-state builder:
```python
async def toast(session, message, *, type="default", message_type="toast", **rest):
    await shinyreact.send_message(session, message_type, {"message": message, "type": type, **rest})
```
The `message_type` is a contract: the host's listener id must match the push helper's.

---

## Step 3 — Register in index.jsx

Add one import and one registry entry to `ui-frameworks/<framework>/js/src/index.jsx`:

```jsx
import { ComponentName } from "@/components/component-name";

window.shinyreact.registerComponents(null, {
  // existing entries...
  "<framework>:ComponentName": ComponentName,
});
```

---

## API conventions (Python + R) — read before Steps 4 & 5

Both languages follow the same shape, so positional misuse is impossible and new
optional args can be added later without breaking callers:

- **Required args first**, positionally (`input_id`, `label`, `choices`, …).
- **Optional args are keyword-only.** In Python, put a bare `*` before them. In R,
  put `...` before them and call `rlang::check_dots_empty()` as the first line — this
  rejects stray positional args and reserves `...` as a forward-compatible separator.
- **Children are the exception.** Container / overlay / collection components take
  child nodes through `*children` (Python) / `...` (R) — mirroring `node(type, ...)`.
  Their optional scalars go *after* the children sink, which makes them keyword-only
  too. These do **not** call `check_dots_empty()` (the dots are legitimately children).
- **Every component takes a class override.** The last optional is `class_` (Python)
  / `class` (R), default `None`/`NULL`, passed through as the `className` prop. The JS
  bridge forwards it and merges via `cn()`. Wire key is always `className`.

| | leaf (scalar options) | container (children) |
|---|---|---|
| Python | `def x(req, *, opt=…, class_=None)` | `def x(req, *children, opt=…, class_=None)` |
| R | `x <- function(req, ..., opt=…, class=NULL)` + `check_dots_empty()` | `x <- function(req, ..., opt=…, class=NULL)` (no check) |

## Step 4 — Add Python helper

Add to `ui-frameworks/<framework>/pkg-py/<framework>/__init__.py`:

```python
# Leaf: optional args are keyword-only (bare *); class_ is always last.
def component_name(
    input_id: str,
    *,
    label: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """One-line description. Server reads ``input.<input_id>()`` as <type>.

    Args:
        input_id: Shiny input id.
        label: Optional label text.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="<framework>:ComponentName",
        props={"input_id": input_id, "label": label, "className": class_},
    )

# Container: children via *children; optional scalars after are keyword-only.
def dialog(
    input_id: str, *children: object, trigger_label: str = "Open", class_: str | None = None
) -> shinyreact.Node:
    return shinyreact.Node(
        type="<framework>:Dialog",
        props={"input_id": input_id, "trigger_label": trigger_label, "className": class_},
        children=list(children),
    )
```

---

## Step 5 — Add R helper

Add to `ui-frameworks/<framework>/pkg-r/<framework>.R`:

```r
# Leaf: `...` is a keyword separator; check_dots_empty() rejects stray args.
#' One-line description. Server reads \code{input$<input_id>} as <type>.
#' @param input_id Shiny input id.
#' @param label Optional label text.
#' @param class Extra CSS classes merged onto the root element.
<framework>_component_name <- function(input_id, ..., label = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("<framework>:ComponentName", props = list(
    input_id = input_id, label = label, className = class
  ))
}

# Container: `...` collects child nodes (node() convention) — no check_dots_empty.
<framework>_dialog <- function(input_id, ..., trigger_label = "Open", class = NULL) {
  node("<framework>:Dialog", ..., props = list(
    input_id = input_id, trigger_label = trigger_label, className = class
  ))
}
```

---

## Step 6 — Build, test, verify

```bash
cd ui-frameworks/<framework>/js && npm run build
```

Check `www/<framework>.js` was produced with no errors, then verify in this order
(cheapest first):

1. **Wire-format check (minimum).** Assert the Python builder produces the expected
   Node `.to_dict()` shape — props named, children placed, item arrays serialized. This
   is fast, needs no browser, and catches the most common mistakes (wrong prop name,
   forgot `children=`). The repo's testing policy expects a test per component; this is it.
2. **Example app.** Add or extend an example and confirm the component renders and the
   Shiny input updates. Prefer Playwright (headless) over eyeballing — assert the input
   value changes on interaction and that there are **zero console errors** (the
   `createPortal` class of bug only shows at runtime).
3. **R parity.** R helpers are easy to write and easy to leave unverified. At minimum run
   the shared wire-format fixtures (`make r-check-fixtures`) so R's JSON matches Python's,
   and add the `<framework>_*` example alongside the Python one. Don't let R drift
   behind — a component is not "done" if only Python is exercised.

---

## Naming conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| JS file | `kebab-case.jsx` | `dropdown-menu.jsx` |
| Bridge function | `ShinyPascalCase` (internal) | `ShinyDropdownMenu` |
| Export / registry name | `PascalCase` | `DropdownMenu` |
| Registry key | `"framework:PascalCase"` | `"shadcn:DropdownMenu"` |
| Python function | `snake_case` | `dropdown_menu` |
| R function | `<framework>_snake_case` | `shadcn_dropdown_menu` |
| Server props | `snake_case` | `input_id`, `default_value`, `debounce_ms` |

---

## shadcn-specific notes

- `@/hooks` — import all hooks from here, never destructure `window.shinyreact` inline
- `@/lib/utils` — the `cn()` helper for merging Tailwind classes
- `@/lib/trigger-button` — shared styled button for overlay triggers (Dialog, Popover, Sheet)
- `@/lib/button-base` — shadcn's `Button` + `buttonVariants` primitive (see cross-component note below)
- Use `radix-ui` (unified package), not individual `@radix-ui/react-*` packages
- Do not externalize `react-dom` — Radix portals need `createPortal` from `react-dom`, which is not in `react-dom/client`

## Gotchas (learned from hard components)

**Cross-component imports.** Some shadcn components import others, e.g. calendar has
`import { Button, buttonVariants } from "@/registry/new-york-v4/ui/button"`. That import
is the *raw shadcn primitive*, not your Shiny bridge (your `button.jsx` exports an action
button wired to an input). Extract the shared shadcn primitive into `@/lib/<name>-base.jsx`
and repoint the import there. `button-base.jsx` already exists for this reason; the button
bridge itself delegates to it.

**class-variance-authority.** shadcn ships `cva` for variant styling (button, tabs, badge,
alert). **Keep it** — `class-variance-authority` is a dependency. Copying the cva block
verbatim is the lowest-edit path and gives `defaultVariants` + compound variants for free.
Pair it with `className` passthrough so callers can override: the component destructures
`className` (no/undefined default) and merges it last via `cn(fooVariants({ variant }),
className)` — cva sets the defaults, tailwind-merge lets the caller win on conflicts. The
bridge forwards `element.props.className` through. See `button-base.jsx`, `badge.jsx`.

**Expose the full variant/size set the cva defines — don't under-expose.** The Python/R
helper's `variant`/`size` options should match what `fooVariants` actually supports (e.g.
button has 6 variants + 4 sizes; badge has 6 variants). Mirror them in the `Literal` (Python)
and the doc (R), and forward `size` through the bridge if present. A good way to keep this
honest is a **variants gallery** (`examples/variants-{py,r}`) — a reference sheet showing
each component across every variant/size/state in rows; it doubles as living docs and a
visual regression check.

**Don't make the base font tiny.** The framework's base (`styles.css`) should be **16px**
(shadcn's real base); controls opt into `text-sm` (14px) via their own classes. Setting the
base to 14px — or force-flattening all controls to one size — makes the whole UI feel
shrunk. See scaffold-framework Step 7.

**Icon-grid layouts (e.g. Alert).** Some shadcn components reserve a leading-icon column
with `grid grid-cols-[0_1fr]` + `col-start-2` on their sub-parts. If your bridge never
renders an icon, that grid collapses the content column (text wraps to min-content). Keep
the cva *variant colors* but drop the grid for a plain block layout. See `alert.jsx`.

**Dates / typed inputs.** Send dates as ISO strings (`"YYYY-MM-DD"`), not `Date` objects
(not JSON-serializable) and not via the `shiny.datetime` handler (requires server-side
registration you don't control). Parse with `date.fromisoformat()` (Python) / `as.Date()` (R).
See `calendar.jsx`.

**npm-backed components.** Some components need real npm packages (`sonner`,
`react-day-picker`). Install them as `dependencies`; they get bundled into the IIFE (not
externalized) — only `react` and `react-dom/client` are externalized. Watch bundle size:
react-day-picker alone roughly doubled the gzip size.

**Strip `next-themes`.** Components like sonner read the theme from `next-themes`. This
project has no theme provider — replace the `useTheme()` call with a plain `theme` prop.

**Drop the unused `import * as React`.** shadcn source files start with
`import * as React from "react"`. The Vite React plugin uses the automatic JSX runtime,
so that import is only needed if the file actually references `React.*` (e.g.
`React.useRef`, `React.useMemo`, `React.Children`). If nothing uses `React.` after you
strip TypeScript, delete the import — keeping it is dead code (most Radix wrappers, Table,
Sonner don't need it).

## Gotchas when *using* components in app.py / app.R

These bite at the app-authoring layer (example apps, downstream apps), not when wrapping.

**No string `style=` inside a `render_react` tree.** The React renderer passes `style`
straight to React, which throws "error #62" on a string (`style="display:flex"`). Inside
the rendered tree use `class_=` (Python) / `class =` (R) with Tailwind utilities. A string
`style=` is only safe on page-chrome tags *outside* `output_react` (e.g. the page wrapper),
which htmltools renders to real HTML.

**Tailwind only ships utilities it sees in `js/src`.** The build scans component source,
not `app.py`/`app.R`. A class used only in an app (e.g. `flex-wrap`, `grid-cols-2`) won't be
in the bundle and silently no-ops. The fix is `@source inline("…")` in `styles.css` —
force-generate the layout utilities apps need. Otherwise stick to utilities some component
already uses (`flex`, `flex-col`, `gap-2/3/4`, `items-center`, `text-sm`, `text-muted-foreground`).

**Bootstrap (loaded by Shiny) inflates component sizes.** It's unlayered, so it beats
Tailwind utilities on headings, form controls, and `.grid`. If components render too big
or a `grid-cols-2` shows as 12 columns, the fix is the `.shinyreact-output` compat layer in
`styles.css` (typography reset + grid override) — see scaffold-framework Step 7. This is a
framework-CSS concern, not a per-component one: fix it once in `styles.css`, not by hacking
each component. Verify by *measuring* (`getComputedStyle(el).fontSize`) and screenshotting,
not just asserting visibility.

## Why the script + fill split saves tokens

The per-component cost used to be dominated by Claude reading the long `.tsx`, transcribing
the stripped source, and writing boilerplate (bridge skeleton, helper stubs, registry lines).
`scripts/prep-component.mjs` does all of that deterministically (esbuild strips types; string
fixups handle imports/exports; templates print the stubs) — **no model tokens.** Claude is
left with only the irreducible judgment:

- Which prop is the `input_id` and which hook (Display / Input / Action / Overlay /
  Collection / Hybrid / Push — Step 0).
- Value-shape quirks (Slider array-wrap, Calendar ISO string, event nonce).
- Free-form children vs a structured `items`/metadata array.

So the loop per component is: `prep-component.mjs <name>` → fill the bridge → paste the
printed `index.jsx`/Python/R stubs (filling props) → build → verify. Keep wrappers
mechanically derivable from the registry (consistent names/keys + the API conventions) so
the script stays the source of the *surface* and humans only own the *semantics*.

**Possible next extensions to the script** (each removes more manual editing): auto-insert
the `index.jsx` import + registry line (idempotent), and append the Python/R helper stubs to
the package files. Left manual for now because both still need the fuzzy prop list — but the
registry-drift check (registry keys with no Python/R wrapper) is pure win and worth adding.
