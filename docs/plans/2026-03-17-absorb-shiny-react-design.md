# Design: Absorb @posit/shiny-react into shinyjson

## Goal

Vendor the TypeScript source from `@posit/shiny-react` (v0.0.16, ~500 lines, 9 files) into this repo, removing the npm dependency. This gives us ownership of the code so we can fix shortcomings directly without waiting on upstream releases.

## What changes

**New directory:** `js/src/shiny-react/` containing the vendored source + LICENSE:

```
js/src/shiny-react/
  LICENSE                  # MIT license from wch/shiny-react
  index.ts
  ImageOutput.tsx
  get-shiny.ts
  input-registry.ts
  message-registry.ts
  output-registry.ts
  react-registry.ts
  use-shiny.ts
  utils.ts
```

**Modified files:**

- `js/src/index.ts` — change import from `"@posit/shiny-react"` to `"./shiny-react"`
- `js/package.json` — remove `@posit/shiny-react` from dependencies

## What stays the same

- The 5 public exports: `useShinyInput`, `useShinyOutput`, `useShinyMessageHandler`, `useShinyInitialized`, `ImageOutput`
- `window.shinyjson` shape — downstream packages see no change
- Python package, examples, everything else untouched

## Verification

1. `npm run build` succeeds
2. Built `js/dist/shinyjson.js` is functionally equivalent
3. Example app (`examples/hello-shinyjson/`) still works
4. `make py-check-tests` still passes

## Attribution

The MIT LICENSE from the upstream repo (`github.com/wch/shiny-react`) is preserved in `js/src/shiny-react/LICENSE`.

## Source

Upstream: https://github.com/wch/shiny-react (commit at time of vendoring)

## Future work

The 10 shortcomings identified in `decisions/2026-03-17-shiny-react-review.md` will be addressed in follow-up work after this absorption is complete.
