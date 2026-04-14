# Output Registry Reference-Counted Cleanup

## Problem

`OutputRegistry.remove()` is destructive: it deletes the entire `OutputRegistryEntry`, removes its hidden DOM element, and schedules async `unbindAll`/`bindAll`. When React unmounts one component and mounts another using the same output ID in the same commit (e.g., tab switching), the new `add()` races the old `remove()`'s unbind, causing Shiny to see duplicate output bindings.

The input registry already handles this correctly: `useShinyInput` cleanup removes one subscriber callback without deleting the entry. The output registry should follow the same pattern.

## Design

### Approach: Subscriber-level remove with RAF-deferred entry cleanup

Instead of destroying the entry on unmount, remove only the specific subscriber callbacks. If no subscribers remain, defer a cleanup check via `requestAnimationFrame`. By the time the RAF fires, React has finished committing — if a new component called `add()` in the same commit, the entry will have subscribers again and cleanup is skipped.

`OutputRegistry.add()` returns a dispose function, following the standard React cleanup pattern. Callers never need to track or pass back their callbacks.

### Changes

#### 1. `OutputRegistryEntry.isEmpty()`

New method. Returns `true` when both subscriber Sets (`useStateSetValueFns` and `useStateSetRecalculatingFns`) have size zero.

#### 2. `OutputRegistry.add()` returns `() => void`

After adding subscribers to the entry (existing logic unchanged), `add()` returns a dispose function. The dispose function:

1. Calls `entry.removeUseStateSetValueFn(setValue)`
2. Calls `entry.removeUseStateSetRecalculatingFn(setRecalculating)`
3. Calls `this.scheduleCleanup(outputId)`

The callbacks are captured in the closure — callers don't need to pass them back.

#### 3. `OutputRegistry.scheduleCleanup(outputId)` (private)

Schedules a `requestAnimationFrame` callback that:

1. Looks up the entry for `outputId`
2. If the entry exists and `isEmpty()` is true: removes the DOM element, deletes the entry from the map, and calls `scheduleBindAll()`
3. If the entry doesn't exist or has subscribers, does nothing

Multiple cleanup requests for the same ID within one frame are harmless — the second RAF finds nothing to do or finds the entry re-populated.

#### 4. Remove `OutputRegistry.remove(outputId)`

Delete the method entirely. All cleanup goes through the dispose function returned by `add()`.

#### 5. `useShinyOutput` cleanup

Changes from:

```ts
reactRegistry.outputs.add(namespacedOutputId, setValue, setRecalculating);
return () => {
  reactRegistry.outputs.remove(namespacedOutputId);
};
```

To:

```ts
const dispose = reactRegistry.outputs.add(
  namespacedOutputId, setValue, setRecalculating
);
return dispose;
```

### Testing

New file: `js/src/shiny-react/__tests__/output-registry.test.ts`

- `isEmpty()` returns true on fresh entry, false after adding subscriber, true after removing
- Dispose removes only its own subscribers (two subscribers, dispose one, other remains)
- `scheduleCleanup` removes entry and DOM element when empty after RAF
- `scheduleCleanup` preserves entry when new subscriber added before RAF fires (the core race condition)

### Documentation updates

**STATUS.md:**
- Remove the "Output registry `remove()` is destructive" TODO
- Add a Recent fix bullet describing the change
- Verify example 6-dashboard "duplicate output ID warning on tab switch" is resolved, then clean up that note

**docs/timeline.md:**
- Verify and update the "Duplicate output IDs on tab navigation" bullet (line 41)

Both 6-dashboard and timeline.md notes should only be updated after manual confirmation that the duplicate binding warning is gone.

## Files touched

| File | Change |
|------|--------|
| `js/src/shiny-react/output-registry.ts` | `isEmpty()`, `add()` returns dispose, `scheduleCleanup()` |
| `js/src/shiny-react/use-shiny.ts` | `useShinyOutput` cleanup uses dispose |
| `js/src/shiny-react/__tests__/output-registry.test.ts` | New test file |
| `docs/STATUS.md` | Remove TODO, add Recent fix, conditionally update 6-dashboard |
| `docs/timeline.md` | Conditionally update duplicate ID bullet |
