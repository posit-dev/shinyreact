# scaffold-component

Add one new component to an existing ui-frameworks framework (shadcn, mui, etc.).

**Framework-generic.** shadcn is the running example; the taxonomy, patterns, and API
conventions apply to any React component library. Genuinely shadcn-specific notes are
in clearly-labeled sections at the end.

---

## Component type reference

Every component is one of eight types. The type drives the hook choice and bridge shape.
Pick it in Step 0 — everything else follows automatically.

| Type | Hook | Input to Shiny | Contents via | Examples |
|------|------|---------------|--------------|---------|
| **Display** | none | nothing | props | Badge, Alert, Separator, Table, Chart, Empty |
| **Container** | none | nothing | `children` | Card, ScrollArea |
| **Input** | `useShinyInput` | value | props | Input, Slider, Select, Calendar, InputOtp, Pagination |
| **Action** | `useShinyInput` w/ event opts | counter or nonce | props | Button |
| **Overlay** | `useShinyInput` for open state | bool | `children` | Dialog, Popover, Sheet, Drawer, Collapsible |
| **Collection** | event hook (+ per-item hooks for stateful items) | nonce dict | `items` array | DropdownMenu, ContextMenu, Menubar |
| **Hybrid** | `useShinyInput` | value | metadata prop array **+** `children` panels (positional) | Tabs, Accordion, Carousel |
| **Push** | `useShinyMessageHandler` | ← server pushes | nothing | Toaster/Sonner |

**Decision heuristic:**
- Content is arbitrary nodes the author arranges → `children`. Container or Overlay.
- Content is a typed list of menu-like items (actions, options) → `items` prop array + builder helpers. Collection.
- Content pairs structured triggers (label, value) with free-form panels → metadata array + positional `children`. Hybrid.
- `input_id` is present but *optional* (component makes sense without one) → use the unconditional-hook-with-noop guard (see Rule 6 below).
- Server sends data into the component; it renders nothing until it arrives → Push.

---

## Two-phase workflow (shadcn)

The work is split between a script (mechanical) and you (semantic). Every manual step that
can be automated is in a script — you only do the parts that require judgment.

```
Phase 1 — prep (script)
  node scripts/prep-component.mjs <name>
  → strips TS, fixes imports, writes src/components/<name>.jsx with a bridge stub + @shiny template
  → prints two-step instructions

Phase 2 — fill (you / Claude)
  a. Add any missing hook imports at the TOP of the file (never mid-file)
  b. Install any missing npm deps (e.g. npm install vaul)
  c. Fill the @shiny annotation: type=, children=, props=
  d. Write the bridge logic

Phase 3 — finalize (script)
  node scripts/finalize-component.mjs <name>
  → reads @shiny annotation → inserts import + registry into index.jsx
  → appends Python helper to pkg-py/shadcn/__init__.py
  → appends R helper    to pkg-r/shadcn.R
  → all three writes are idempotent (safe to re-run)

Phase 4 — build + verify
  npm run build
  (then test in an example app)
```

---

## @shiny annotation format

The annotation is a single comment line in the bridge block. The finalize script reads it.

```jsx
// @shiny type=Input children=false props=input_id:str,total_pages:int=10,current:int=1,show_ellipsis:bool=True,class_:str=None
```

| Field | Values | Meaning |
|---|---|---|
| `type` | `Display` `Container` `Input` `Action` `Overlay` `Collection` `Hybrid` `Push` | Bridge type — determines hook and structure |
| `children` | `true` / `false` | `true` = takes `*children` / `...`; Python gets `*children: object`, R skips `check_dots_empty()` |
| `props` | `name:type[=default]` | Comma-separated prop specs (see below) |

**Prop spec rules:**
- `name:type` — required positional (no default)
- `name:type=None` — optional, null default
- `name:type=value` — optional with default (`str` values need no quotes; type is context)
- `class_:str=None` — **always the last prop**; the script maps it to `className` on the wire and `class` in R. Auto-added if omitted (with a warning).

**Types:** `str` `int` `float` `bool` `list`

**Examples:**

```
// Leaf Input:
// @shiny type=Input children=false props=input_id:str,total_pages:int=10,show_ellipsis:bool=True,class_:str=None

// Overlay with children:
// @shiny type=Overlay children=true props=input_id:str,trigger_label:str=Open,side:str=right,title:str=None,class_:str=None

// Display with no input_id:
// @shiny type=Display children=false props=text:str,variant:str=default,class_:str=None

// Container (children only):
// @shiny type=Container children=true props=title:str=None,class_:str=None
```

The finalize script generates correctly-typed Python + R helpers from these specs — multi-line
Python signatures (always under ruff's 88-char limit), aligned R props lists, `check_dots_empty()`
on leaves, `children=list(children)` on containers.

**After running finalize:** fill in the `TODO` descriptions in the generated helpers — the
script can't know what `total_pages` means. Everything else is ready to use.

---

## Pre-flight checklist

Run these before writing any bridge code.

- [ ] **Identify type** (table above). Write it down — it determines the hook and bridge shape.
- [ ] **Run the prep script** (shadcn): `cd js && node scripts/prep-component.mjs <name>`. Reads `src/components-src/<name>.tsx`, strips TS/exports/bad imports, appends a bridge stub with `@shiny` template.
- [ ] **Scan the generated file's imports.** Look for any `@/registry/…/ui/X` paths — the script fixes most but some slip through. Map them to the correct local path or `@/lib/button-base`.
- [ ] **Check for npm deps.** Does the source import from a package not in `package.json`? (e.g. `vaul`, `cmdk`, `embla-carousel-react`, `input-otp`, `react-resizable-panels`, `recharts`). Install *before* writing: `npm install <pkg>`. A missing dep gives a Vite "could not resolve" error at build time, not at write time.
- [ ] **Check for cross-component shadcn imports.** Does the source import `DialogHeader`, `Button`, etc. from sibling shadcn files? Our bridges export only the Shiny wrapper — sibling imports that expect sub-components will fail at build. Decide: use a shared lib file (`@/lib/button-base`), or strip the unused import.

---

## Bridge checklist

Fill the stub in `src/components/<name>.jsx` in this order.

- [ ] **Add missing imports at the TOP of the file** — immediately after the existing imports, before any function definitions. NEVER place `import { useShinyInput }` or any hook import after the bridge comment; Vite/esbuild requires all imports at the top. This is the single most common mistake made by agents and humans alike.
- [ ] **Replace the TODO stub** with the bridge for the identified type (see patterns below).
- [ ] **Fill the `@shiny` annotation** — set `type=`, `children=`, and the complete `props=` list. This is what the finalize script reads; a placeholder will cause an error.
- [ ] **Destructure `className` from `element.props`** and forward it to the component root.
- [ ] **Coerce round-tripped booleans with `!!`** on every prop that controls a Radix `open`/`checked`/`disabled`.
- [ ] **Apply the unconditional-hook-with-noop guard** for any optional `input_id` (see Rule 6).
- [ ] **Verify the export line** uses the `export { ShinyFoo as Foo }` form — always, even when there is no name clash.

---

## Post-bridge checklist

After filling the bridge and annotation:

- [ ] **Run finalize**: `node scripts/finalize-component.mjs <name>` — inserts index.jsx entry, appends Python + R helpers. All idempotent.
- [ ] **Fill in `TODO` descriptions** in the generated Python docstring and R roxygen comments. The script can't know what each prop means.
- [ ] **Build**: `cd js && npm run build` — zero errors, no unresolved imports.
- [ ] **Wire-format test**: assert `.to_dict()` shape from the Python builder. Minimum: props keyed correctly, children list present if needed. Required by the testing policy.
- [ ] **R parity**: run `make r-check-fixtures`. A component is not done if R is untested.

---

## Strict rules

**RULE 1 — Imports belong at the top.**
All `import` statements must appear before any function definitions. Placing `import { useShinyInput } from "shinyreact"` after the `// --- shinyreact bridge ---` comment will cause a Vite build error ("import must be at the top level"). The prep script appends a stub *after* the source functions — the first thing you do is add needed hook imports to the import block at the top.

**RULE 2 — Always use `export { ShinyFoo as Foo }`, never `export function ShinyFoo`.**
Consistent shape across every file. The internal name `ShinyFoo` avoids clashing with the shadcn source function `Foo` in the same file. The exported name is clean.

**RULE 3 — Every bridge forwards `className`.**
Destructure `className` from `element.props` (no default — let it be `undefined`). Pass it to the root via `cn(componentClasses, className)`. This is the call site's override escape hatch. Lands on the sensible root: wrapper for inputs, content panel for overlays, root element for display/container.

**RULE 4 — Never hard-code layout into a component.**
No `w-full`, `mx-auto`, `mt-4` baked into a bridge. Width/margin/placement are the caller's job. The button is auto-width — `w-full` breaks every horizontal row. Components ship only their own look; the caller's `className` and parent layout decide placement.

**RULE 5 — Always coerce booleans with `!!`.**
Shiny may return `0`, `1`, `null`, or `undefined` for a value that should be boolean (open state, checked state, disabled). Radix `open`, `checked`, `defaultChecked` want real booleans. Write `open={!!open}`, `checked={!!checked}` — never pass the raw value.

**RULE 6 — Optional `input_id` must use the unconditional-hook-with-noop guard.**
React hooks cannot be called conditionally. When `input_id` is optional (the component makes sense without Shiny wiring), call the hook unconditionally with a noop fallback id, then conditionally invoke the setter:
```jsx
const [, _setValue] = useShinyInput(input_id ?? "__noop_carousel__", 0);
const setValue = input_id ? _setValue : null;
// later: if (setValue) setValue(newValue);
```
The noop id `"__noop_*__"` is an intentionally invalid Shiny id — it never registers. Pick a descriptive suffix so debug tooling identifies it.

**RULE 7 — Event inputs MUST have `debounceMs: 0` and `priority: "event"`.**
Buttons, menu selections, confirm actions, alert dialogs: all use `{ debounceMs: 0, priority: "event" }`. Without `debounceMs: 0`, the default 100ms debounce coalesces rapid clicks. Without `priority: "event"`, Shiny may batch the input update.

**RULE 8 — Repeat-payload actions need a nonce.**
If an action fires the same value twice (same menu item selected, same button clicked), Shiny deduplicates and the second click does not re-fire. Add `nonce: Date.now()` or `nonce: Math.random()` to the payload: `setValue({ value, nonce: Date.now() })`. Applies to DropdownMenu, ContextMenu, Menubar, NavigationMenu.

**RULE 9 — `check_dots_empty()` on leaf R helpers only.**
Call `rlang::check_dots_empty()` for components that take no children (`...` is a keyword-only separator). Do NOT call it for container/overlay/hybrid components whose `...` legitimately collects child nodes.

**RULE 10 — Python `class_` always maps to wire key `className`.**
The Python arg is `class_: str | None = None` (to avoid the reserved word). The prop sent over the wire is always `"className": class_`. Never use `"class"` as the wire key.

**RULE 11 — `ignore_init=True` on all event reactive handlers.**
Server-side: `@reactive.event(input.btn, ignore_init=True)` prevents firing when `useShinyInput` registers the initial `0`/`null` value on page load.

**RULE 12 — Anchor-based interactive components need `e.preventDefault()`.**
Components that render `<a>` for interactive buttons (e.g. shadcn Pagination's `PaginationLink`) will navigate or submit a form on click. Add `onClick={(e) => { e.preventDefault(); /* your handler */ }}`.

---

## Bridge patterns (copy-paste and adapt)

### Display — no hook

```jsx
function ShinyBadge({ element }) {
  const { text, variant = "default", className } = element.props;
  return <Badge variant={variant} className={className}>{text}</Badge>;
}
export { ShinyBadge as Badge };
```

For data-display components (Table, Chart), read structured props (`columns`, `rows`, `data`, `series`) directly. No hook.

### Container — no hook, children as content

```jsx
function ShinyCard({ element, children }) {
  const { title, className } = element.props;
  return (
    <Card className={className}>
      {title && <CardHeader><CardTitle>{title}</CardTitle></CardHeader>}
      <CardContent>{children}</CardContent>
    </Card>
  );
}
export { ShinyCard as Card };
```

### Input

```jsx
import { useShinyInput } from "shinyreact";

function ShinyTextInput({ element }) {
  const { input_id, placeholder = "", label, debounce_ms = 250, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, "", { debounceMs: debounce_ms });
  return (
    <div className="flex flex-col gap-1.5">
      {label && <Label>{label}</Label>}
      <Input
        value={value ?? ""}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
        className={className}
      />
    </div>
  );
}
export { ShinyTextInput as Input };
```

**Slider quirk — Radix uses array values:**
```jsx
const [value, setValue] = useShinyInput(input_id, default_value);
<Slider value={[value]} onValueChange={([v]) => setValue(v)} />
```

**Pagination — anchor click:**
```jsx
<PaginationLink
  isActive={p === page}
  onClick={(e) => { e.preventDefault(); setPage(p); }}
  className="cursor-pointer"
>
  {p}
</PaginationLink>
```

**OTP — dynamic slot array:**
```jsx
const slots = Array.from({ length }, (_, i) => <InputOTPSlot key={i} index={i} />);
```

### Action — counter idiom (nothing to send but "it happened")

```jsx
import { useShinyInput } from "shinyreact";

function ShinyButton({ element }) {
  const { input_id, label = "Click", variant = "default", className } = element.props;
  const [count, setCount] = useShinyInput(input_id, 0, { debounceMs: 0, priority: "event" });
  return (
    <Button variant={variant} className={className} onClick={() => setCount(count + 1)}>
      {label}
    </Button>
  );
}
export { ShinyButton as Button };
```

Server: `@reactive.event(input.btn, ignore_init=True)` reads `input.btn()` as an int.

### Action — nonce idiom (action carries a payload; write-only)

```jsx
import { useSetShinyInput } from "shinyreact";

// Inside the bridge:
const setSelected = useSetShinyInput(input_id, null, { debounceMs: 0, priority: "event" });
const onSelect = (value) => setSelected({ value, nonce: Date.now() });
```

Server: `input.<id>()["value"]` with `@reactive.event(input.<id>, ignore_init=True)`.

### Action — AlertDialog (two optional action ids, both unconditional)

```jsx
import { useShinyInput } from "shinyreact";

function ShinyAlertDialog({ element }) {
  const {
    confirm_id, cancel_id,
    trigger_label = "Open", title = "Are you sure?",
    description, confirm_label = "Continue", cancel_label = "Cancel", className,
  } = element.props;
  // Both hooks unconditional — noop guard for the optional cancel_id.
  const [, setConfirm] = useShinyInput(confirm_id ?? "__noop_confirm__", 0, { debounceMs: 0, priority: "event" });
  const [, setCancel]  = useShinyInput(cancel_id  ?? "__noop_cancel__",  0, { debounceMs: 0, priority: "event" });
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild><TriggerButton>{trigger_label}</TriggerButton></AlertDialogTrigger>
      <AlertDialogContent className={className}>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && <AlertDialogDescription>{description}</AlertDialogDescription>}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => { if (cancel_id) setCancel(n => n + 1); }}>{cancel_label}</AlertDialogCancel>
          <AlertDialogAction onClick={() => setConfirm(n => n + 1)}>{confirm_label}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
export { ShinyAlertDialog as AlertDialog };
```

### Overlay — open state + children

```jsx
import { useShinyInput } from "shinyreact";
import { TriggerButton } from "@/lib/trigger-button";

function ShinyDialog({ element, children }) {
  const { input_id, trigger_label = "Open", title, description, className } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <Dialog open={!!open} onOpenChange={setOpen}>
      <DialogTrigger asChild><TriggerButton>{trigger_label}</TriggerButton></DialogTrigger>
      <DialogContent className={className}>
        {title && <DialogHeader><DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>}
        {children}
      </DialogContent>
    </Dialog>
  );
}
export { ShinyDialog as Dialog };
```

**Variants that take a `side` prop** (Sheet, Drawer): same shape, add `side`/`direction` to the root component props.

**vaul Drawer** accepts the same `open`/`onOpenChange` shape as Dialog, plus `direction` ("bottom" | "top" | "left" | "right").

### Collection — data-driven items array

Items are walked recursively. Always support: `"item"`, `"label"`, `"separator"`, `"submenu"`. Stateful items (checkbox/radio) get their own `input_id`.

```jsx
import { useSetShinyInput, useShinyInput } from "shinyreact";
import { TriggerButton } from "@/lib/trigger-button";

function MenuItems({ items, onSelect }) {
  return items.map((item, i) => {
    if (item.type === "label")     return <DropdownMenuLabel key={i}>{item.label}</DropdownMenuLabel>;
    if (item.type === "separator") return <DropdownMenuSeparator key={i} />;
    if (item.type === "checkbox")  return <CheckboxItem key={i} item={item} />;
    if (item.type === "submenu") return (
      <DropdownMenuSub key={i}>
        <DropdownMenuSubTrigger>{item.label}</DropdownMenuSubTrigger>
        <DropdownMenuSubContent>
          <MenuItems items={item.items ?? []} onSelect={onSelect} />
        </DropdownMenuSubContent>
      </DropdownMenuSub>
    );
    return (
      <DropdownMenuItem key={i} onSelect={() => onSelect(item.value)}
        className={item.variant === "destructive" ? "text-destructive" : ""}>
        {item.label}
      </DropdownMenuItem>
    );
  });
}

function CheckboxItem({ item }) {
  const [checked, setChecked] = useShinyInput(item.input_id, item.checked ?? false);
  return (
    <DropdownMenuCheckboxItem
      checked={!!checked}
      onCheckedChange={setChecked}
      onSelect={(e) => e.preventDefault()}  // keep menu open while toggling
    >
      {item.label}
    </DropdownMenuCheckboxItem>
  );
}

function ShinyDropdownMenu({ element }) {
  const { input_id, trigger_label = "Open", items = [], className } = element.props;
  const setSelected = useSetShinyInput(input_id, null, { debounceMs: 0, priority: "event" });
  const onSelect = (value) => setSelected({ value, nonce: Date.now() });
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild><TriggerButton>{trigger_label}</TriggerButton></DropdownMenuTrigger>
      <DropdownMenuContent className={className}>
        <MenuItems items={items} onSelect={onSelect} />
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
export { ShinyDropdownMenu as DropdownMenu };
```

**ContextMenu** is identical in shape but the trigger is `children` (the right-click area), not a button:
```jsx
function ShinyContextMenu({ element, children }) {
  const { input_id, items = [], className } = element.props;
  // ...
  return (
    <ContextMenu>
      <ContextMenuTrigger asChild><div className={className}>{children}</div></ContextMenuTrigger>
      <ContextMenuContent><MenuItems items={items} onSelect={onSelect} /></ContextMenuContent>
    </ContextMenu>
  );
}
```

**Menubar** fires `{ menu: menuLabel, value: itemValue, nonce }` — the extra `menu` field identifies which menu was open:
```jsx
function handleSelect(menuLabel, itemValue) {
  setValue({ menu: menuLabel, value: itemValue, nonce: Date.now() });
}
```

### Hybrid — metadata array + positional children panels

```jsx
import * as React from "react";
import { useShinyInput } from "shinyreact";

function ShinyTabs({ element, children }) {
  const { input_id, tabs = [], selected, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, selected ?? tabs[0]?.value ?? "");
  const panels = React.Children.toArray(children);   // stable array, index-matched to tabs
  return (
    <Tabs value={value} onValueChange={setValue} className={className}>
      <TabsList>
        {tabs.map((t) => <TabsTrigger key={t.value} value={t.value}>{t.label}</TabsTrigger>)}
      </TabsList>
      {tabs.map((t, i) => (
        <TabsContent key={t.value} value={t.value}>{panels[i]}</TabsContent>
      ))}
    </Tabs>
  );
}
export { ShinyTabs as Tabs };
```

Python: `tabs(input_id, [tab("a", "A"), tab("b", "B")], panel_a, panel_b)` — panels are `*children` after the metadata list.

**Carousel — optional input_id + embla `setApi`:**
```jsx
import * as React from "react";
import { useShinyInput } from "shinyreact";

function ShinyCarousel({ element, children }) {
  const { input_id, orientation = "horizontal", loop = false, className } = element.props;
  const [, _setValue] = useShinyInput(input_id ?? "__noop_carousel__", 0);
  const setValue = input_id ? _setValue : null;
  const childArray = React.Children.toArray(children);
  return (
    <Carousel
      orientation={orientation}
      opts={{ loop }}
      setApi={(api) => {
        if (!api || !setValue) return;
        api.on("select", (a) => setValue(a.selectedScrollSnap()));
      }}
      className={className}
    >
      <CarouselContent>
        {childArray.map((child, i) => <CarouselItem key={i}>{child}</CarouselItem>)}
      </CarouselContent>
      <CarouselPrevious />
      <CarouselNext />
    </Carousel>
  );
}
export { ShinyCarousel as Carousel };
```

**Accordion** is Hybrid with `open` state as a second input on top of the panels:
panel content = `React.Children.toArray(children)[i]`; `items` = `[{value, title}]` metadata.

### Push — server sends, no input

```jsx
import { useShinyMessageHandler } from "shinyreact";

function ShinyToaster({ element }) {
  const { message_type = "toast", position = "bottom-right" } = element.props;
  useShinyMessageHandler(message_type, (data) => {
    const { message, description, type = "default" } = data ?? {};
    // NEVER do toast[type](...) — toast.default does not exist and throws.
    // Select explicitly:
    const fn =
      type === "success" ? toast.success
      : type === "error"   ? toast.error
      : type === "warning" ? toast.warning
      : type === "info"    ? toast.info
      : type === "loading" ? toast.loading
      : toast;
    fn(message, { description });
  });
  return <Toaster position={position} />;
}
export { ShinyToaster as Toaster };
```

---

## Gotchas: symptom → cause → fix

### Build-time errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| Vite: `SyntaxError: import must be at the top level` | Hook import placed after bridge comment (mid-file) | Move `import { useShinyInput }` to the top of the file, alongside other imports |
| Vite: `Could not resolve import "vaul"` | npm dep missing from `package.json` | `npm install vaul` (or whichever package), then rebuild |
| Vite: `"DialogHeader" is not exported by "src/components/dialog.jsx"` | A shadcn source imports sibling sub-components that our bridge doesn't re-export | Strip the import block (if the feature is unused) or add the sub-exports to the sibling file |
| Vite: `@/registry/new-york-v4/ui/button` cannot resolve | Shadcn registry import the prep script missed | Replace with `@/lib/button-base` |

### Runtime errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| React error #62 on `style` prop | String `style="display:flex"` passed inside a render_react tree | Use `class_=` with Tailwind instead; string `style=` only safe on page-chrome outside `output_react` |
| Radix overlay never opens / Checkbox always unchecked | Raw 0/1/null passed to a boolean prop | Add `!!`: `open={!!open}`, `checked={!!checked}` |
| Slider fires wrong values | Radix `value`/`onValueChange` expects `[number]` array | Wrap: `value={[val]}`, unwrap: `onValueChange={([v]) => setVal(v)}` |
| Clicking same menu item twice doesn't re-fire | Shiny deduplicates identical consecutive values | Add nonce: `setValue({ value, nonce: Date.now() })` |
| Pagination / anchor component navigates instead of updating input | `PaginationLink` renders as `<a>` | `onClick={(e) => { e.preventDefault(); setPage(p); }}` |
| Page load fires a reactive event | `useShinyInput` registers initial value on mount, triggering the handler | `@reactive.event(input.x, ignore_init=True)` |
| Carousel slide index doesn't update | Hook called with `input_id ?? "__noop_x__"` but setter always invoked | Check: `const setValue = input_id ? _setValue : null; if (setValue) setValue(...)` |

### Python/R errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ruff: E501 line too long` on commit | Docstring line > 88 chars | Wrap long docstring lines before 88 chars |
| `ruff-format: 1 file reformatted` on commit | Code style drift | `git add` the reformatted file and retry commit |
| `trailing whitespace` in `www/<framework>.js` on commit | Pre-commit hook fixes it automatically | Re-stage `www/<framework>.js` and retry commit |
| R: `unused arguments (...)` | Leaf R helper missing `check_dots_empty()` | Add `rlang::check_dots_empty()` as first line |
| R single-column table row auto-unboxes | jsonlite unboxes length-1 vectors to scalars | Use `I()` to force array: `rows = list(I(c("Ada")))` |

### Visual / behavioral surprises

| Symptom | Cause | Fix |
|---------|-------|-----|
| Text/inputs too big | Bootstrap unlayered beats Tailwind layered | Fix in `styles.css` typography reset, not per-component |
| `grid-cols-2` shows 12 columns | Bootstrap `.grid` overrides Tailwind | `.shinyreact-output .grid-cols-2 { grid-template-columns: ... !important; }` in `styles.css` |
| App-only Tailwind class silently no-ops | Tailwind only scans `js/src`, not app files | `@source inline("grid grid-cols-2 flex-wrap …")` in `styles.css` |
| Alert text wraps word-by-word | shadcn's Alert uses `grid-cols-[0_1fr]` for icon column — no icon collapses content | Keep variant colors, replace grid with plain block layout |
| Toast.default throws | `toast["default"]` is not a function in Sonner | Explicit ternary chain (see Push pattern above) |
| Chart doesn't render | `style={{ height }}` missing on `ChartContainer` | `<ChartContainer config={config} style={{ height }}>` |
| ScrollArea doesn't scroll | `height` prop not applied to root | `<ScrollArea style={{ height }}>` |

---

## API conventions (Python + R)

Identical shape in both languages — positional misuse is impossible, new optionals are backward-compatible.

| | Leaf (scalar options only) | Container (takes children) |
|---|---|---|
| **Python** | `def x(req, *, opt=…, class_=None)` | `def x(req, *children, opt=…, class_=None)` |
| **R** | `x(req, ..., opt=…, class=NULL)` + `check_dots_empty()` | `x(req, ..., opt=…, class=NULL)` (no check) |

Rules:
- Required positional args come first.
- All optional scalar args are **keyword-only** (bare `*` in Python; `...` guard in R).
- Children `*children` / `...` are the exception — they stay positional so callers can write `card(child1, child2)`.
- The last optional is always `class_` (Python) / `class` (R), default `None`/`NULL`.
- Wire key is always `"className"`. Python's `class_` → `props["className"]`; R's `class` → `props$className`.
- Provide **item-builder helpers** for Collection components (`menu_item`, `menu_label`, `menu_separator`, `menu_checkbox`, `menu_submenu`, `menubar_menu`, `nav_item`, `chart_series`, etc.). Never make app authors hand-write dicts.

### Python leaf example

```python
def pagination(
    input_id: str,
    *,
    total_pages: int = 10,
    current: int = 1,
    show_ellipsis: bool = True,
    class_: str | None = None,
) -> shinyreact.Node:
    """A page-number pagination bar.

    Server reads ``input.<input_id>()`` as int (1-based).

    Args:
        input_id: Shiny input id — current page number (1-based).
        total_pages: Total number of pages.
        current: Initially selected page (default 1).
        show_ellipsis: Collapse distant pages into ellipsis when True.
        class_: Extra CSS classes merged onto the nav element.
    """
    return shinyreact.Node(
        type="shadcn:Pagination",
        props={
            "input_id": input_id,
            "total_pages": total_pages,
            "current": current,
            "show_ellipsis": show_ellipsis,
            "className": class_,
        },
    )
```

### Python container example

```python
def dialog(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    title: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    return shinyreact.Node(
        type="shadcn:Dialog",
        props={"input_id": input_id, "trigger_label": trigger_label,
               "title": title, "className": class_},
        children=list(children),
    )
```

### R leaf example

```r
#' A page-number pagination bar. Server reads input$<input_id> as integer (1-based).
#' @param input_id Shiny input id — current page number.
#' @param ... Must be empty (leaf component).
#' @param total_pages Total number of pages (default 10).
#' @param current Initially selected page (default 1).
#' @param show_ellipsis Collapse distant pages into ellipsis when TRUE.
#' @param class Extra CSS classes merged onto the nav element.
shadcn_pagination <- function(input_id, ..., total_pages = 10L, current = 1L,
                              show_ellipsis = TRUE, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Pagination", props = list(
    input_id      = input_id,
    total_pages   = total_pages,
    current       = current,
    show_ellipsis = show_ellipsis,
    className     = class
  ))
}
```

### R container example

```r
#' A side-panel sheet. Server reads input$<input_id> as boolean (open state).
shadcn_sheet <- function(input_id, ..., trigger_label = "Open", side = "right",
                         title = NULL, class = NULL) {
  # No check_dots_empty() — ... collects child nodes.
  node("shadcn:Sheet", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    side          = side,
    className     = class
  ))
}
```

---

## shadcn-specific notes

**Import paths:**
- `shinyreact` — all hooks (`import { useShinyInput } from "shinyreact"`). This is an *external* module: vite maps it to the host's `window.shinyreact` global (same mechanism as React/ReactDOM), so the hooks are never bundled. Never destructure `window.shinyreact` inline and never re-add a local hooks shim — import from `"shinyreact"`.
- `@/lib/utils` — `cn()` helper
- `@/lib/trigger-button` — shared styled trigger for overlay components
- `@/lib/button-base` — shadcn `Button` + `buttonVariants` primitive (calendar, pagination)
- `radix-ui` — unified Radix package; never use individual `@radix-ui/react-*`
- Do NOT externalize `react-dom` — Radix portals need `createPortal`

**npm packages for specific components:**

| Component | Package | Note |
|-----------|---------|------|
| Drawer | `vaul` | Same `open`/`onOpenChange`/`direction` shape as Dialog |
| Command | `cmdk` | Export is `CommandPrimitive`; strip the unused `CommandDialog` block |
| Carousel | `embla-carousel-react` | Slide index via `setApi` + `api.on("select", ...)` |
| InputOtp | `input-otp` | `OTPInput` from `"input-otp"`; slots via `InputOTPSlot index={i}` |
| Resizable | `react-resizable-panels` | `ResizablePanelGroup` + interleaved `ResizablePanel` / `ResizableHandle` |
| Chart | `recharts` | Via shadcn's `ChartContainer`; CSS var injection via `--color-{key}` |

**`class-variance-authority` (cva):** keep it — it's a dependency. Copy the `cva(...)` block verbatim from the source. The bridge forwards `element.props.className` and the component merges via `cn(fooVariants({ variant }), className)`. Mirror all cva variants + sizes in the Python `Literal` and R docs.

**Dead imports to strip:**
- `import * as React from "react"` — only keep if the file actually references `React.*` (`React.useRef`, `React.useMemo`, `React.Children`, etc.)
- `"use client"` directive — the prep script removes this; check it did
- `next-themes` `useTheme()` — replace with a plain `theme` prop or delete if unused

**Components that import shadcn siblings:** When `command.tsx` imports `DialogHeader` from its sibling `dialog.tsx`, our `dialog.jsx` only exports `ShinyDialog as Dialog` — not the sub-components. Strip the sibling import block if the sub-components are unused in the bridge (e.g. `CommandDialog` in the command bridge).

**Dates:** Send as ISO strings (`"YYYY-MM-DD"`), not `Date` objects. Parse with `date.fromisoformat()` (Python) / `as.Date()` (R).

**Icon-grid Alert layout:** shadcn's Alert uses `grid-cols-[0_1fr]` + `col-start-2` to reserve an icon column. Without an icon, the content column collapses (text wraps to one word per line). Keep the cva variant colors; replace the grid with a plain block layout.

---

## Bulk-wrapping with parallel agents

When wrapping 5+ components at once:

1. **Prep scripts first** — run `prep-component.mjs <name>` for every component. Produces N independent `.jsx` stub files, each with the `@shiny` annotation template.
2. **One agent per file** — spawn one Sonnet agent per component, each scoped to its own `.jsx` file only. Each agent: fills the bridge + fills the `@shiny` annotation. Do NOT have agents touch `index.jsx`, `__init__.py`, or `shadcn.R`.
3. **Audit imports** — agents frequently place `import { useShinyInput }` after the bridge comment (mid-file). Before finalizing: `grep -n "^import" js/src/components/<name>.jsx` and confirm all imports are at the top.
4. **Run finalize for each** — `node scripts/finalize-component.mjs <name>` for every component in sequence. Each call is idempotent. This replaces the previous manual integration of 3 files × N components.
5. **Build once** — `npm run build` after all finalize calls complete.

---

## Why the two-phase script design saves tokens

The per-component cost used to be:
1. Reading the long `.tsx` (tokens)
2. Transcribing the stripped source (tokens)
3. Writing boilerplate: import + registry + Python helper + R helper (tokens + error-prone)

**Phase 1 (`prep-component.mjs`)** does (1) and (2) deterministically — esbuild strips types, string fixups handle imports/exports. Zero model tokens.

**Phase 3 (`finalize-component.mjs`)** does (3) deterministically — reads the `@shiny` annotation and generates correctly-typed Python + R helpers, plus idempotent index.jsx edits. Zero model tokens.

**Only the irreducible judgment remains (Phase 2):**
- Which type (Display / Input / Overlay / …)
- Value-shape quirks (Slider array-wrap, Calendar ISO string, event nonce, Carousel `setApi`)
- Hook wiring, noop guard, `e.preventDefault()` for anchors
- The `@shiny` annotation prop list

Loop per component:
```
prep-component.mjs <name>
→ fill bridge + @shiny annotation
→ finalize-component.mjs <name>
→ npm run build + verify
```

The `@shiny` annotation is also the canonical record of the component's API surface — it's what the finalize script uses to derive helpers, and it documents the props in a machine-readable way that future scripts (e.g. a registry-drift checker) can also consume.
