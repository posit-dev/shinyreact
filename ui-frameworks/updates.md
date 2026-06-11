# shadcn/shinyreact — Refactor Updates

This document records the structural changes made to `ui-frameworks/shadcn/js/src/` and why each one is better than what it replaced.

---

## 1. Collapsed two-layer structure into single files per component

**Before**

```
js/src/
  components/
    dialog.tsx        ← raw shadcn source, typed, no bridge
  wrappers/
    ShinyDialog.jsx   ← bridge that imported from components/
```

Every component needed two files with a 1:1 relationship and an import between them. Adding a new component meant touching four files just to get to "hello world".

**After**

```
js/src/
  components/
    dialog.jsx        ← shadcn source + bridge, one file
```

The shadcn source lives at the top of the file (converted from TypeScript, structurally unchanged). The shinyreact bridge sits below it in the same file, uses the local functions directly, and exports the clean name. Adding a new component touches one JS file instead of two.

---

## 2. Hooks consumed as an external module, not a hand-written shim

**Before**

Every interactive component file repeated:

```js
const { useShinyInput } = window.shinyreact;
```

or pulled in `window.shinyreact.useShinyInput` inline. An interim improvement collapsed this into a single `src/hooks.js` that destructured the global once and re-exported under a `@/hooks` alias. That removed the repetition but kept two smells: it was a hand-maintained list that had to be synced with core, and it *eagerly destructured a runtime global at module-eval time* — reinventing, by hand, what the bundler already does for React.

**After**

`window.shinyreact` is a host-injected runtime dependency — architecturally identical to React, which `vite.config.js` already externalizes. So the hooks are externalized the same way:

```js
// vite.config.js
external: ["react", "react-dom/client", "shinyreact"],
output: { globals: {
  react: "window.shinyreact.React",
  "react-dom/client": "window.shinyreact.ReactDOM",
  shinyreact: "window.shinyreact",
} },
```

Components import from the external specifier; the bundler rewrites named imports to property access on the global (and tree-shakes the unused ones):

```js
import { useShinyInput } from "shinyreact";
```

No shim file, no eager destructure, no hand-synced list. The entire host API (React, ReactDOM, hooks) is now consumed through **one** mechanism. Editor types come from `src/shinyreact.d.ts`, an ambient `declare module "shinyreact"` (interim — these declarations ultimately belong in the core package, which is fully TypeScript and owns the API).

---

## 3. `lib/trigger-button.jsx` — shared overlay trigger button

**Before**

Dialog and Popover each had an inline `<button>` with identical 6-class Tailwind strings:

```jsx
// dialog.jsx
<button type="button"
  className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 h-9 text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
>
  {trigger_label}
</button>
```

Same 130-character string duplicated across files. When Sheet, DropdownMenu, and other overlay components are added they would each repeat it again.

**After**

```jsx
// src/lib/trigger-button.jsx
export function TriggerButton({ children, ...props }) {
  return (
    <button
      type="button"
      className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 h-9 text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
      {...props}
    >
      {children}
    </button>
  );
}
```

Overlay bridges now do:

```jsx
import { TriggerButton } from "@/lib/trigger-button";

<DialogTrigger asChild>
  <TriggerButton>{trigger_label}</TriggerButton>
</DialogTrigger>
```

One place to adjust the trigger style. The `...props` spread means callers can pass `onClick`, `disabled`, `aria-*` through without any changes here.

---

## 4. Export naming: `export { ShinyFoo as Foo }`

**Before**

Components either avoided the name clash with an underscore suffix or a different internal name, or were exported as `ShinyDialog` and imported as `ShinyDialog` in `index.jsx` — leaking the internal prefix into the registry key.

**After**

The internal bridge function carries the `Shiny` prefix to avoid colliding with the shadcn source function of the same name in the same file:

```jsx
function Dialog({ ...props }) { ... }        // shadcn source
function ShinyDialog({ element, children }) { ... }  // bridge

export { ShinyDialog as Dialog };            // exported cleanly
```

`index.jsx` imports `{ Dialog }` — no prefix visible anywhere outside the file. The shadcn source stays untouched and the bridge name makes the role obvious when reading the file.

---

## 5. Checkbox, Switch, Slider — upgraded to real shadcn/Radix source

**Before**

All three used hand-rolled HTML:

```jsx
// checkbox — before
<input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} />
```

```jsx
// switch — before
<button role="switch" onClick={() => setChecked(!checked)} />
```

```jsx
// slider — before
<input type="range" value={value} onChange={(e) => setValue(Number(e.target.value))} />
```

Problems: no keyboard navigation, no focus ring, no ARIA states (Radix manages `aria-checked`, `aria-orientation`, etc. automatically), and the visual style didn't match the rest of the shadcn design tokens.

**After**

All three use the real Radix primitives via the `radix-ui` unified package — the same code shadcn v4 generates:

```jsx
// checkbox — after (shadcn source)
function Checkbox({ className, ...props }) {
  return (
    <CheckboxPrimitive.Root data-slot="checkbox" className={cn("peer size-4 ...", className)} {...props}>
      <CheckboxPrimitive.Indicator ...>
        <CheckIcon className="size-3.5" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}
```

Radix handles focus management, keyboard interaction, and ARIA attributes. The visual output is pixel-identical to what shadcn's own CLI generates.

**Slider-specific note:** Radix Slider uses array values (`value={[50]}`). The bridge wraps the single number and unwraps on change:

```jsx
<Slider value={[value]} onValueChange={([v]) => setValue(v)} />
```

---

## 6. Removed `class-variance-authority` (CVA)

> **Superseded (2026-06-11):** CVA was later **re-adopted** so variant components
> stay faithful to shadcn source and get `defaultVariants` / compound variants for
> free — the lowest-edit path for scaling and good out-of-the-box defaults. The
> removal below was an early-refactor simplification, not the current state. See
> the "Re-adopt class-variance-authority" entry in [CHANGELOG.md](CHANGELOG.md).

**Before**

`package.json` listed `class-variance-authority` as a dependency. It was introduced when the components were first scaffolded but none of the current components use it — variant logic was handled inline with a plain object (`const variants = { default: "...", outline: "..." }`).

**After**

CVA removed. Variant lookup uses a plain object:

```js
const variants = {
  default: "bg-primary text-primary-foreground hover:bg-primary/90",
  outline: "border border-input ...",
};
// usage
variants[variant] ?? variants.default
```

One fewer dependency in the bundle. No behavioral change.

---

## 7. CSS: added `--color-popover` and `--color-popover-foreground` tokens

**Before**

`styles.css` `@theme` block defined the core color tokens but was missing the popover pair. Radix Select and Popover content panels use `bg-popover` / `text-popover-foreground` in their className strings. Without these tokens Tailwind emits nothing for those classes and the dropdown panels render with a transparent background — invisible content floating over the page.

**After**

```css
@theme {
  /* ... existing tokens ... */
  --color-popover: hsl(0 0% 100%);
  --color-popover-foreground: hsl(240 10% 3.9%);
}
```

Select and Popover content panels now have a white background with dark text, matching the shadcn default theme.

---

## 8. Vite config: `react-dom` not externalized

**Before**

```js
external: ["react", "react-dom", "react-dom/client"],
globals: {
  react: "window.shinyreact.React",
  "react-dom": "window.shinyreact.ReactDOM",
  "react-dom/client": "window.shinyreact.ReactDOM",
},
```

This externalized all of `react-dom`. The symptom: `An.createPortal is not a function` at runtime, blocking every overlay component (Dialog, Select, Popover).

**Root cause:** `window.shinyreact.ReactDOM` is `import * as ReactDOM from "react-dom/client"` — it only exposes `createRoot` and `hydrateRoot`. Radix portals call `ReactDOM.createPortal`, which doesn't exist on that object.

**After**

```js
external: ["react", "react-dom/client"],
globals: {
  react: "window.shinyreact.React",
  "react-dom/client": "window.shinyreact.ReactDOM",
},
```

`react-dom` (the base package, ~2 kB tree-shaken gzip) is now bundled. `react-dom/client` remains externalized so `createRoot` calls share the same root as shinyreact. All portals work. The shared React instance is preserved — no broken hooks.

> This block shows only the `react-dom` change. The current external list also
> includes `"shinyreact"` (the hooks), added later — see §2 above.
