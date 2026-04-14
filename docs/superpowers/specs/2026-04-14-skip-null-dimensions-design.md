# MISSING sentinel for useShinyInput

## Problem

`ImageOutput` initializes its clientdata dimension inputs (`.clientdata_output_X_width` and `_height`) to `null` via `useShinyInput`. On mount, `useShinyInput` sends this `null` to Shiny via `setInputValue()`.

In traditional Shiny (non-React), clientdata values start in a `MISSING` state. When `render.plot` reads a `MISSING` value, it raises `SilentException`, which the session catches silently — the output simply waits until real dimensions arrive.

With React `ImageOutput`, sending `null` explicitly means the reactive input **has** a value. Instead of `SilentException`, `render.plot` receives `null` and passes it into matplotlib sizing code, which errors or produces incorrect output.

## Solution

Introduce a `MISSING` sentinel symbol that mirrors Shiny Python's `MISSING` type. When `useShinyInput` holds a `MISSING` value, it updates React state locally but does **not** call `Shiny.setInputValue()`. This keeps the server-side clientdata in `MISSING` state until the `ResizeObserver` measures actual pixel dimensions.

This is better than a `skipNull` boolean flag because:
- **Semantic**: "not yet set" is a distinct concept from "null." A `skipNull` flag would prevent ever intentionally sending `null` to Shiny. With a sentinel, `null` remains a valid sendable value.
- **Mirrors Shiny Python**: The server already has a `MISSING` type that raises `SilentException`. A TS-side `MISSING` sentinel is the natural counterpart.
- **No configuration**: The hook just checks `value === MISSING` before sending. No option flag needed.

## Changes

### 1. `MISSING` sentinel — new export from `js/src/shiny-react/`

```ts
export const MISSING: unique symbol = Symbol("MISSING");
export type MISSING = typeof MISSING;
```

Export from `shiny-react/index.ts` and from `window.shinyjson` so downstream component authors can use it.

### 2. `InputRegistryEntry` — `js/src/shiny-react/input-registry.ts`

In `setValue()`, gate the Shiny send when the value is `MISSING`:

```ts
setValue(value: T) {
  this.value = value;
  if (value === MISSING) {
    // Update React state only — don't send to Shiny
    this.useStateSetValueFns.forEach((fn) => fn(value));
    return;
  }
  this.shinySetInputValueDebounced(value);
  this.useStateSetValueFns.forEach((fn) => fn(value));
}
```

Import `MISSING` from the new module.

### 3. `ImageOutput` — `js/src/shiny-react/ImageOutput.tsx`

Use `MISSING` as the default value for dimension inputs:

```ts
const [imgWidth, setImgWidth] = useShinyInput<number | MISSING>(
  `.clientdata_output_${namespacedId}_width`,
  MISSING,
  { namespace: null },
);
const [imgHeight, setImgHeight] = useShinyInput<number | MISSING>(
  `.clientdata_output_${namespacedId}_height`,
  MISSING,
  { namespace: null },
);
```

No changes to `useShinyInput` signature needed — `MISSING` is just a valid value.

### 4. `window.shinyjson` — `js/src/index.ts`

Export `MISSING` on the global API so downstream packages can use it:

```ts
window.shinyjson = {
  // ...existing exports...
  MISSING,
};
```

### 5. Tests — `js/src/shiny-react/__tests__/`

Add a test verifying:
- With `MISSING` as the value, `Shiny.setInputValue()` is **not** called
- When a real number replaces `MISSING`, `Shiny.setInputValue()` **is** called
- `null` values are still sent normally (existing behavior preserved)

## Scope

Four files touched, no API-breaking changes. Existing callers of `useShinyInput` are unaffected — `MISSING` is opt-in by passing it as the default value.
