# scaffold-component

Add one new component to an existing ui-frameworks framework (shadcn, mui, etc.).

## When to use

When the user says "add a `<ComponentName>` component to shadcn/mui/…" or "wrap `<LibraryComponent>` for shinyreact."

---

## Step 0 — Identify component type

Every component falls into one of five types. The type determines which hook to use and how to structure the bridge.

| Type | Hook | Examples |
|------|------|---------|
| **Display** | none | Badge, Alert, Separator |
| **Container** | none | Card (passes `children`) |
| **Input** | `useShinyInput` | Input, Slider, Select, Checkbox, Switch |
| **Action** | `useShinyInput` with event opts | Button |
| **Overlay** | `useShinyInput` for open state + `children` | Dialog, Popover, Sheet |

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
- Use `radix-ui` (unified package), not individual `@radix-ui/react-*` packages
- Do not externalize `react-dom` — Radix portals need `createPortal` from `react-dom`, which is not in `react-dom/client`
