# scaffold-component

Add one new component to an existing ui-frameworks framework (shadcn, mui, etc.).

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

## Step 1 — Get the component source

### shadcn (copy-paste framework)

Fetch the source via the shadcn MCP tool or GitHub API, then strip TypeScript annotations (`type`, `interface`, `: Type` return types, `as Type` casts). Do **not** strip `"use client"` markers as comments — just delete them.

```bash
# Alternative: shadcn CLI from the js/ directory
cd ui-frameworks/shadcn/js
npx shadcn@latest add <component-name>
# Move the generated file: src/components/ui/<name>.tsx → src/components/<name>.jsx
# Strip TypeScript
```

### npm library (MUI, Mantine, etc.)

No source to copy — the component imports directly from the npm package. Skip to Step 2.

---

## Step 2 — Write the component file

Create `ui-frameworks/<framework>/js/src/components/<component-name>.jsx`.

The file has two sections separated by a comment:
1. **shadcn source** (or npm import) — unchanged from the original
2. **shinyreact bridge** — reads `element.props`, wires the hook, delegates to the source component

### File structure

```jsx
import * as React from "react";
import { SomeIcon } from "lucide-react";
import { ComponentPrimitive } from "radix-ui";   // shadcn: from radix-ui
// OR: import { Component } from "@mui/material"; // npm library
import { cn } from "@/lib/utils";                 // shadcn only
import { useShinyInput } from "@/hooks";          // only if component needs a hook

// --- shadcn source (or npm imports above, no source section needed) ---

function ComponentName({ className, ...props }) {
  // exact shadcn source here, TypeScript stripped
}

// --- shinyreact bridge ---
// Props: input_id (str), label (str, optional), ...
// Server reads input.<input_id>() as <type>.

function ShinyComponentName({ element, children }) {
  const { input_id, label, default_value = "" } = element.props;
  const [value, setValue] = useShinyInput(input_id, default_value);
  return (
    <ComponentName value={value} onChange={setValue}>
      {children}
    </ComponentName>
  );
}

export { ShinyComponentName as ComponentName };
```

**Why `export { ShinyFoo as Foo }`:** The bridge function is named `ShinyFoo` to avoid clashing with the shadcn source function `Foo` defined above it in the same file. The exported name is clean.

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

**Action button — `useShinyInput` with event options:**
```jsx
function ShinyButton({ element }) {
  const { input_id, label, variant = "default" } = element.props;
  const [count, setCount] = useShinyInput(input_id, 0, { debounceMs: 0, priority: "event" });
  return <Button variant={variant} onClick={() => setCount(count + 1)}>{label}</Button>;
}
```
Server: `@reactive.event(input.btn, ignore_init=True)` — `ignore_init=True` prevents firing on page load.

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
    toast[data.type ?? "message"](data.message, { description: data.description });
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

## Step 4 — Add Python helper

Add to `ui-frameworks/<framework>/pkg-py/<framework>/__init__.py`:

```python
def component_name(
    input_id: str,
    label: str | None = None,
    # ... other props
) -> shinyreact.Node:
    """One-line description. Server reads ``input.<input_id>()`` as <type>.

    Args:
        input_id: Shiny input id.
        label: Optional label text.
    """
    return shinyreact.Node(
        type="<framework>:ComponentName",
        props={"input_id": input_id, "label": label},
    )
```

For container/overlay components that accept children, use `*children`:

```python
def dialog(input_id: str, *children: object, trigger_label: str = "Open") -> shinyreact.Node:
    return shinyreact.Node(
        type="<framework>:Dialog",
        props={"input_id": input_id, "trigger_label": trigger_label},
        children=list(children),
    )
```

---

## Step 5 — Add R helper

Add to `ui-frameworks/<framework>/pkg-r/<framework>.R`:

```r
#' One-line description. Server reads \code{input$<input_id>} as <type>.
#'
#' @param input_id Shiny input id.
#' @param label Optional label text.
<framework>_component_name <- function(input_id, label = NULL) {
  node("<framework>:ComponentName", props = list(input_id = input_id, label = label))
}
```

For overlay/container components that accept children, use `...`:

```r
<framework>_dialog <- function(input_id, ..., trigger_label = "Open") {
  node("<framework>:Dialog", ..., props = list(input_id = input_id, trigger_label = trigger_label))
}
```

---

## Step 6 — Build and verify

```bash
cd ui-frameworks/<framework>/js && npm run build
```

Check `www/<framework>.js` was produced with no errors. Run one of the example apps to confirm the component renders and the Shiny input updates correctly.

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

**class-variance-authority.** shadcn ships `cva` for variant styling (button, tabs, badge).
This project has no cva dependency — inline the variants as a plain object and select with
`variantClasses[variant] ?? variantClasses.default`, or a small `buttonVariants()`-style
function. See `button-base.jsx` and `tabs.jsx`.

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
