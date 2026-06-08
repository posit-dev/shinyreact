# `type=` option on `useShinyInput` / `useSetShinyInput` for Shiny input handlers

**Date:** 2026-05-13
**Status:** Proposal — pending implementation plan
**Resolves:** #97

## Summary

Add an optional `type?: string` to the options bag of `useShinyInput` and `useSetShinyInput`. When set, the hook sends values to Shiny as `Shiny.setInputValue("${namespacedId}:${type}", value, opts)`, opting into Shiny's server-side input handler dispatch (e.g. `shiny.datetime` → `datetime.datetime` on `input.foo()`). The registry key stays the bare id, so the read-side hook `useShinyInputValue("foo")` continues to subscribe correctly. Invalid `type` strings throw at mount; conflicting `type` values across multiple mounts of the same id throw.

## Context

PyShiny and R Shiny support **input handlers** — server-side functions that intercept and transform raw values arriving from the client before they land in `input.xxx`. The wire-level convention is a `:type` suffix on the input id when calling `Shiny.setInputValue`:

```js
Shiny.setInputValue("when:shiny.datetime", 1731436800);
// server: input.when() returns a datetime, not a number
```

Built-ins: `shiny.action`, `shiny.date`, `shiny.datetime`, `shiny.password`, `shiny.symbol`, `shiny.matrix`, `shiny.number`. Apps and downstream packages can register additional handlers via `registerInputHandler()` (R) / `Inputs.set_input_handler()` (Py).

Today, `shinyreact` hooks expose no way to specify the type. Values flow as raw JSON, so apps can't opt into existing handlers and downstream packages can't ship typed inputs that decode cleanly on the server.

This spec covers *invoking* existing handlers from the JS hooks. *Registering* new handlers from Python is tracked separately in `docs/todos.md` ("Python-side input handlers for useShinyInput values") and is out of scope here.

## Design

### API surface

`type?: string` is added to the options bag of both write-side hooks:

```ts
export function useShinyInput<T>(
  id: string,
  defaultValue: T,
  options?: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
  },
): [T, (value: T) => void];

export function useSetShinyInput<T>(
  id: string,
  defaultValue: T,
  options?: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
  },
): (value: T) => void;
```

Read-side hooks (`useShinyInputValue`, `useShinyOutputValue`, `useShinyOutputStatus`) are untouched. Input handlers fire on the write path; the value subscribed to on read is already the post-handler form.

### Validation (throws at hook mount)

Validation runs synchronously in the hook body (not inside `useEffect`) so the error surfaces with a stack trace pointing at the call site:

```ts
if (type !== undefined && !/^[^\s:]+$/.test(type)) {
  throw new Error(
    `useShinyInput("${id}"): invalid type=${JSON.stringify(type)}. ` +
    `Must be non-empty and contain no whitespace or ':' characters.`,
  );
}
```

The same check appears verbatim in `useSetShinyInput` (with the function name updated in the message).

Rejected values: empty string, any string containing whitespace, any string containing `:`. `undefined` is the "no suffix" sentinel and bypasses validation.

### Registry changes

`InputRegistryEntry` gains a `type?: string` field. The wire call appends it; the registry map key stays the bare id.

```ts
// js/src/shiny-react/input-registry.ts

export class InputRegistryEntry<T> {
  id: string;
  type?: string;
  private typeFinalized = false;
  // …existing fields…

  private setShinyInputValue(value: T) {
    const wireId = this.type ? `${this.id}:${this.type}` : this.id;
    getShiny()?.setInputValue?.(wireId, value, this.opts);
  }

  updateType(type: string | undefined): void {
    if (!this.typeFinalized) {
      this.type = type;
      this.typeFinalized = true;
      return;
    }
    if (type === undefined) return;
    if (this.type !== type) {
      throw new Error(
        `Input "${this.id}" is already registered with type=${JSON.stringify(this.type)}. ` +
        `A second mount requested type=${JSON.stringify(type)}. ` +
        `An input's handler type changes server-side semantics and must be consistent ` +
        `across every useShinyInput / useSetShinyInput call for the same id.`,
      );
    }
  }
}
```

**Why a `typeFinalized` flag instead of just checking `this.type === undefined`:** an entry whose first mount omitted `type` has *finalized* its policy as "no type" — a later mount adding a type would route some wire calls through a handler and others not, which is the exact inconsistency we're guarding against. The flag distinguishes "no mount has registered yet" (impossible by the time `updateType` runs, since the registry entry is created in the same `useEffect`) from "a mount has registered with no opinion".

**Why a later mount omitting `type` is a no-op (not a conflict):** the second mount isn't expressing a preference. If the first mount set `type=X`, the second mount's omission is "I defer to whoever set this." Treating that as a conflict would force every reader/writer pair across a codebase to redundantly repeat the `type` argument.

**Why throw on conflict instead of warn:** `type` changes the server-side semantics of `input.foo()`. A disagreement between mounts is almost certainly a bug; silently picking a winner would ship broken apps. This is stricter than the existing `priority` / `debounceMs` "last-writer-wins" treatment because those are tuning knobs, not contracts.

The hooks call `inputRegistryEntry.updateType(type)` inside the existing `useEffect`, alongside `updateDebounceDelay` / `updatePriority`. `type` joins the effect dep array. Because `updateType` throws on conflict, the throw surfaces from React's effect runner to the nearest error boundary.

### First-writer-wins semantics

| Sequence | Outcome |
| -------- | ------- |
| Mount A `{ type: "X" }`, then mount B `{ type: "X" }` | OK — same value |
| Mount A `{ type: "X" }`, then mount B (no `type`) | OK — B's omission is not a claim |
| Mount A (no `type`), then mount B `{ type: "X" }` | A established `type=undefined`; B's `"X"` is a *change* — **throws** |
| Mount A `{ type: "X" }`, then mount B `{ type: "Y" }` | **throws** at B's effect |

The third row deserves a note: under "first-writer-wins", once an entry has been created without `type`, a later mount adding `type` is also a conflict. This is the right behavior — the first mount's wire calls have already gone out as `"foo"`, switching mid-session to `"foo:X"` would inconsistently route values. Document this in the JSDoc.

### Namespacing interaction

`useNamespacedId(id, explicitNamespace)` produces the namespaced id (e.g. `"ns-foo"`). The `type` suffix is appended *after* namespacing, so the wire id is `"ns-foo:shiny.datetime"`. The registry key is the namespaced id (`"ns-foo"`), matching the existing pattern.

## Example app

New example at `examples/ui-tsx/08-input-handler/` demonstrating the `shiny.datetime` round trip. Implementation matches the build pattern (importmap vs. Vite) of the nearest existing `examples/ui-tsx/` example to minimize boilerplate.

### `ui.tsx`

```tsx
function App() {
  const [when, setWhen] = useShinyInput<number>(
    "when",
    Math.floor(Date.now() / 1000),
    { type: "shiny.datetime" },
  );
  const echoed = useShinyOutputValue<string>("when_info");

  return (
    <div>
      <label>
        Unix seconds:{" "}
        <input
          type="number"
          value={when}
          onChange={(e) => setWhen(Number(e.target.value))}
        />
      </label>
      <p>Server saw: <code>{echoed ?? "…"}</code></p>
    </div>
  );
}
```

### `app.py`

```python
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.set_react_page()

def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def when_info():
        v = input.when()
        return f"{type(v).__name__} → {v!r}"

app = App(app_ui, server)
```

Expected output text: `datetime → datetime.datetime(...)`. Without `type="shiny.datetime"` the user would see `int → 1234567890`, which is the manual A/B for verifying the feature works.

## Tests

### Vitest — `js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx` (new)

1. **Suffix appended when `type` set.** Render `useShinyInput("foo", 0, { type: "shiny.datetime" })`, trigger the setter, assert `Shiny.setInputValue` mock was called with `"foo:shiny.datetime"` and the options bag.
2. **No suffix when `type` omitted.** Same setup without `type`; mock called with `"foo"`.
3. **Invalid `type` throws at mount.** Three sub-cases: `type: ""`, `type: "has space"`, `type: "a:b"`. Each renders into an error boundary that captures the thrown `Error`; assert the message matches the regex-validation copy.
4. **Conflict throws.** Mount component A with `{ type: "X" }`, then mount component B with `{ type: "Y" }` for the same id. B's effect throws; A's wire calls remain `"foo:X"`.
5. **Later mount omitting `type` is fine.** Mount A `{ type: "X" }`, then mount B with no `type` — no throw; subsequent wire calls still use `"foo:X"`.
6. **Adding `type` after a no-`type` mount throws.** Mount A with no `type`, then mount B `{ type: "X" }` — B's effect throws (the corner case the first-writer-wins table calls out: A's wire calls already shipped as `"foo"`, switching to `"foo:X"` mid-session would inconsistently route values).
7. **Same mount changing `type` literal also throws.** Re-render a single hook instance with a new `type` literal — confirms `type` is set-once even from the same call site (the registry doesn't distinguish "same mount" from "second mount").
8. **Namespacing.** Wrap case 1 in `ShinyModuleProvider value={{ namespace: "ns" }}`; assert wire id is `"ns-foo:shiny.datetime"`.

### Playwright e2e — `pkg-py/tests/playwright/test_input_handler_type.py` (new)

Fixture app at `pkg-py/tests/playwright/apps/input-handler-type/` mirroring the example app shape (number input + a `@reactive_output` returning `type(input.when()).__name__`). Test assertions:

1. After initial load, the rendered text contains `datetime` (proves the suffix survived the wire and the handler ran).
2. After changing the number input, the rendered text updates and still contains `datetime`.

The fixture-app pattern is documented in `.claude/references/playwright-e2e-tests.md`.

## Docs

- `docs/features.md` — add `type` to the options row for `useShinyInput` and `useSetShinyInput` with a one-line description and a pointer to `examples/ui-tsx/08-input-handler/`.
- `CLAUDE.md` — add a short subsection under "Common patterns" titled "Input handlers via `type=`" with the `shiny.datetime` snippet.
- JSDoc on both hooks — document `options.type`, the wire-format effect, and the consistency-across-mounts requirement.

## Non-goals

- **Registering Python-side input handlers from `shinyreact`.** Tracked separately in `docs/todos.md` ("Python-side input handlers for useShinyInput values").
- **R-package counterpart.** `pkg-r/` is a placeholder; nothing to update.
- **Curated TypeScript union of built-in handler names.** Downstream packages register their own; a hardcoded union would be stale immediately. `type?: string` stays open.
- **Read-side decoding hooks.** The server has already coerced by the time the value comes back; no client decode needed.
- **Migrating existing `examples/` to use `type`.** The issue is about enabling the option, not converting demos.

## Files touched

```
js/src/shiny-react/use-shiny.ts                              # add type option + validation, 2 hooks
js/src/shiny-react/input-registry.ts                         # type field + updateType, suffix at wire call
js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx   # NEW vitest suite
pkg-py/tests/playwright/test_input_handler_type.py           # NEW e2e
pkg-py/tests/playwright/apps/input-handler-type/             # NEW e2e fixture app
examples/ui-tsx/08-input-handler/                            # NEW example (app.py + www/)
docs/features.md                                             # mention type option
CLAUDE.md                                                    # "Input handlers via type=" subsection
```
