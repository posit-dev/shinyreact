# examples/02-columns — behavior

Move items between three columns. The server owns the data and one event
input; the client owns all of the UI. No build step.

Format rules: `../README.md` § "Example behavior trees".

## Data

- three columns, ids `"A"`, `"B"`, `"C"`, in that order
- initial contents `{A: [Apple, Apricot], B: [Banana, Blueberry], C: [Cherry,
  Cranberry]}`
- held in a module-level `reactive.value`, so state is shared by every session
  and survives a reload — it is not per-session

## Server (`app.py`, Express)

- output `column_data` → the whole `{col: item[]}` dict
- input `move_item` → `{item, from, to}`
  - handled by a `@reactive.effect` + `@reactive.event(input.move_item,
    ignore_init=True)`, so the initial `null` from mount is ignored
  - the move is applied to a copy of the dict, then `columns.set(...)` — the
    reactive value is replaced, not mutated in place
  - if `item` is not in `data[from]`, nothing changes (no error) `(test)`
  - the item is appended to the end of the destination column, never inserted
    `(test)`
- `[py]` only — this example has no R server

## Client (`www/ui.js`)

- `React.createElement` with an `h` shorthand; inline `style` objects, no CSS
  file of its own
- renders `null` until `useShinyInitialized()` is true
- `useShinyInput("move_item", null, {debounceMs: 0, priority: "event"})`
  - the value is discarded (`const [, setMoveItem]`) — the client never reads
    back what it sent
  - `debounceMs: 0` so two fast clicks are two moves, not one
- three columns rendered from the hard-coded `["A", "B", "C"]`, not from the
  keys of the server payload `(test)`
  - a column the server did not send renders as empty, it does not throw
- per item row
  - a `←` button when the column index is > 0 `(test)`
  - a `→` button when the column index is < 2 `(test)`
  - so column A has no `←` and column C has no `→`
  - clicking sends `{item, from: <this column>, to: <neighbor>}` `(test)`
- an empty column renders `"(empty)"` in grey `(test)`
- before the first `column_data` value, every column renders `"(empty)"`
- item text is used as the React `key`, so duplicate item names across a single
  column would collide `(verify)`
- no mount container in the page — the client appends its own `<div>` to
  `<body>`
