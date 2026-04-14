# Skip null dimensions in useShinyInput

## Problem

`ImageOutput` initializes its clientdata dimension inputs (`.clientdata_output_X_width` and `_height`) to `null` via `useShinyInput`. On mount, `useShinyInput` sends this `null` to Shiny via `setInputValue()`.

In traditional Shiny (non-React), clientdata values start in a `MISSING` state. When `render.plot` reads a `MISSING` value, it raises `SilentException`, which the session catches silently — the output simply waits until real dimensions arrive.

With React `ImageOutput`, sending `null` explicitly means the reactive input **has** a value. Instead of `SilentException`, `render.plot` receives `null` and passes it into matplotlib sizing code, which errors or produces incorrect output.

## Solution

Add a `skipNull` option to `useShinyInput` that prevents `null`/`undefined` values from being sent to Shiny. The value still updates React state locally, but `Shiny.setInputValue()` is not called until a real (non-nullish) value is set. This keeps the server-side clientdata in `MISSING` state until the `ResizeObserver` measures actual pixel dimensions.

## Changes

### 1. `useShinyInput` option — `js/src/shiny-react/use-shiny.ts`

Add `skipNull?: boolean` to the options object:

```ts
export function useShinyInput<T>(
  id: string,
  defaultValue: T,
  {
    debounceMs = 100,
    priority,
    namespace: explicitNamespace,
    skipNull,          // <-- new
  }: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    skipNull?: boolean; // <-- new
  } = {},
): [T, (value: T) => void]
```

Pass `skipNull` through to `InputRegistryEntry` via `getOrCreate` or an update method.

### 2. `InputRegistryEntry` — `js/src/shiny-react/input-registry.ts`

Store `skipNull` on the entry. In `setValue()`, gate the Shiny send:

```ts
setValue(value: T) {
  this.value = value;
  if (this.opts.skipNull && (value === null || value === undefined)) {
    // Update React state only — don't send to Shiny
    this.useStateSetValueFns.forEach((fn) => fn(value));
    return;
  }
  this.shinySetInputValueDebounced(value);
  this.useStateSetValueFns.forEach((fn) => fn(value));
}
```

### 3. `ImageOutput` — `js/src/shiny-react/ImageOutput.tsx`

Add `skipNull: true` to both dimension inputs:

```ts
const [imgWidth, setImgWidth] = useShinyInput<number | null>(
  `.clientdata_output_${namespacedId}_width`,
  null,
  { namespace: null, skipNull: true },
);
const [imgHeight, setImgHeight] = useShinyInput<number | null>(
  `.clientdata_output_${namespacedId}_height`,
  null,
  { namespace: null, skipNull: true },
);
```

### 4. Tests — `js/src/shiny-react/__tests__/`

Add a test verifying:
- With `skipNull: true`, setting a `null` value does **not** call `Shiny.setInputValue()`
- With `skipNull: true`, setting a real number **does** call `Shiny.setInputValue()`
- Without `skipNull`, `null` values are sent normally (existing behavior preserved)

## Scope

This is a focused change — four files touched, no API-breaking changes. Existing callers of `useShinyInput` are unaffected (option defaults to `undefined`/falsy).
