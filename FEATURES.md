# FEATURES.md

Every behavior shinyreact has today, one atomically checkable claim per leaf.
Organized by behavior, not by language, so R/Python divergence is a visible
leaf rather than a diff between two files.

- `[py]` / `[r]` / `[js]` — holds only there. A marker on a parent applies to
  every leaf beneath it.
- **unmarked** — holds in every language the subtree applies to.
- `(verify)` — claim not yet checked against the code.
- `(e2e)` — pinned by a Playwright test in `pkg-py/tests/playwright/`, i.e.
  verified through the browser, not just at the API.

See the "The feature tree" section of `CLAUDE.md` for the format rules, the
completeness bar, and the in-same-PR update rule.
`/audit-shinyreact-features` audits this file against the code.

**Status:** all three packages are covered — `[py]` against
`pkg-py/src/shinyreact/`, `[r]` against `pkg-r/R/`, `[js]` against
`pkg-js/src/`, each with its unit tests plus the Python e2e suite.

**Examples are out of scope for this file** and are documented elsewhere.

R has no e2e suite, so no `(e2e)` leaf covers R (issue #194).

## Wire protocol

- protocol version is `1.0`
  - one string constant per language, all three must be equal
    - `[py]` `PROTOCOL_VERSION` in `_protocol.py`
    - `[js]` `PROTOCOL_VERSION` in `pkg-js/src/shiny-react/config.ts`
    - `[r]` `.protocol_version` in `pkg-r/R/protocol.R` — note the R symbol is
      *not* named `PROTOCOL_VERSION`
    - a parity test in each language asserts all three match
  - `protocol/README.md` is the authoritative prose contract, and
    `protocol/fixtures/config-restore.json` is a shared wire-contract fixture
    that all three suites round-trip through their own config-tag code
    - `[py]` that test skips when the fixture is missing, so its enforcement is
      conditional
    - the README's prose does not yet mention `shinyreact.init`,
      `.shinyreact_init`, or `shinyreact-deps` (#232)
  - `protocol/surface.json` enumerates the whole boundary — custom messages,
    input-handler names, input ids, DOM ids — beside the protocol version
    - all three suites assert their live surface against it: the JS suite scans
      `pkg-js/src`, and the Python and R suites read shiny's input-handler
      registry after loading the package
    - so a new custom message type or handler name fails a test until it is
      added to the manifest, where the version-bump question is unavoidable
    - each guard is verified to fail on an unlisted name, not merely to pass
    - listing a name is **not** automatically a version bump: additive changes
      degrade gracefully both ways and the client compares majors only, so the
      bump policy itself is still open (#232)
  - the source comments in all three languages say it covers exactly three
    boundary shapes, and bumps only when one changes
    - the `#shinyreact-config` payload
    - the `shinyReactMessage` custom message
    - the `shinyreact.default` / `shinyreact.asis` input-handler contract
  - but the wire now carries two more, added by #221 without a version bump
    - the `shinyreact.init` input-handler name, and the
      `.shinyreact_init` ping id
    - the `shinyreact-deps` custom message
  - so the stated scope and the actual boundary disagree; nothing enforces the
    bump rule (#232)
  - `[js]` the client compares only the **major** version at boot
    - a mismatch throws, with a message naming both versions and telling the
      reader to upgrade the older side
    - equal majors means compatible, so client and server package releases
      need not be released in lockstep
- server → client boot config: one `<script type="application/json"
  id="shinyreact-config">` tag
  - it lands in `<head>` in every language and on every path
    - `[py]` via `head_content()`
    - `[r]` `page_react()` via `tags$head()`; `page_react_html()` via a
      dependency's `head` HTML, with `all_files = FALSE` since it ships no files
    - R emitted it inline in `<body>` until #224
  - always carries `protocolVersion`
    - `[js]` a tag *without* one no longer skips the handshake silently: the
      IIFE logs an error, and the npm build throws, since an independently
      installed client cannot assume compatibility
  - carries `restore` (an `{inputId: value}` map) only when a bookmark restore
    is active *and* the map is non-empty
  - emitted by every page entry point except `page_bare()`
  - `[js]` reading it is tolerant by construction
    - the reader returns `null` when the tag is absent
    - the reader logs and returns `null` on malformed JSON rather than
      throwing — a broken config must not take down an app that never bookmarks
    - the reader returns `null` when there is no `document` (non-DOM env)
  - `[js]` whether a *missing* tag is fatal depends on which build is running
    - IIFE bundle (shipped inside the R/Python packages): tolerated, because a
      hand-wired `page_bare()` page legitimately has no tag
    - npm ESM build (`@posit/shinyreact`): fatal, opted into at import time —
      an independently installed client meeting a tagless page means the server
      predates the protocol
- server → client custom message: `shinyReactMessage`, payload `{id, data}`
- client → server input values: the wire id may carry a `:<type>` suffix naming
  a server-side input handler
  - the suffix is stripped before the value reaches `input`
  - a module-namespaced id keeps its `mod-` prefix through dispatch
  - an untyped id bypasses *handler* dispatch — though `[r]` shiny's untyped
    branch still applies `unlist(recursive = TRUE)`, so "untyped" is not
    "untouched"
  - `[py]` values are set with `force=True`, so every wire value recalculates
    dependents (matching R Shiny's `dedupe=FALSE`)
    - this is unconditional in Shiny for *all* inputs, typed or not — not
      something shinyreact's handlers opt into
  - a non-shinyreact handler name works the same way — `type="shiny.datetime"`
    reaches Shiny's own datetime handler and `input.when()` is a
    `datetime.datetime` server-side `(e2e)`
    - it keeps working on later values, not just the first `(e2e)`

## Input handlers

- three handlers are registered under fixed names
  - `shinyreact.default` — the implicit handler; the JS hook appends
    `:shinyreact.default` to every untyped input id
  - `shinyreact.asis` — opt-in pass-through (`type: "shinyreact.asis"`),
    returns the parsed value untouched
  - `shinyreact.init` — per-session bootstrap, not a value transform
    - the client sends exactly one `.shinyreact_init:shinyreact.init` ping per
      session, after Shiny initializes, so apps with no `useShinyInput` are
      covered too
    - it installs renderer dependency discovery for the session
    - it returns the value unchanged
- the contract is defined in terms of the JSON the React hook sent
  - array of objects — `[{name, size}, ...]`
    - `[py]` list of dicts
    - `[r]` list of records, so `for (f in input$x) f$size` works
  - array of scalars — `[0, 100]`, `["a", "b"]` — **deliberate divergence**
    - `[py]` unchanged: `[0, 100]`
    - `[r]` flattened to an atomic vector: `c(0, 100)`
    - reason: it is what R code wants, and it matches shiny's own no-`type`
      coercion — `decisions/2026-08-13-r-python-parity.md`
  - empty array — `[]`
    - `[py]` stays `[]`
    - `[r]` becomes `list()`, **not** `NULL` — shiny's own default handler
      conflates "empty" with "absent"; this fixes that (#184)
  - nested arrays — `[[1, 2], [3, 4]]`
    - nesting is preserved in both languages; shiny's default handler would
      flatten it to `c(1, 2, 3, 4)` (#184)
  - JSON object (a *named* value) — passed through as-is
  - a non-list scalar — passed through as-is
  - anything else — passed through as-is
- `[py]` both handlers are literal no-ops that return `value` unchanged
  - Python's deserializer never simplifies, so there is nothing to undo
  - they exist only so the wire suffixes do not raise "No input handler
    registered for type"
- `[r]` `default_input_handler()` decides in this order
  - not a list, or a list with names → returned untouched
  - zero length → `list()`
  - every element atomic, length 1, and **unnamed** → `unlist(recursive = FALSE)`
    - the per-element `is.null(names(el))` check means one *named* length-1
      element blocks flattening for the whole array (untested)
  - otherwise → returned untouched, so one record or nested array in the array
    preserves the whole shape
- `[r]` `asis_input_handler()` returns its value untouched
- both handlers take three arguments and use only the value, but the **argument
  order differs**
  - `[py]` `(value, name, session)` — Shiny's `InputHandlerType`
  - `[r]` `(value, session = NULL, name = NULL)`, so the R handlers are also
    callable with just a value (which every R test relies on)
  - nothing catches this: both implementations ignore the last two arguments
- registration happens once at load, and re-registration is forced rather than
  fatal
  - `[py]` a side effect of `import shinyreact`, `force=True`, so re-importing
    (dev reload, tests) re-registers instead of raising "already registered"
  - `[r]` in `.onLoad()` via `shiny::registerInputHandler(..., force = TRUE)`

## Outputs

- `reactive_output` publishes a reactive JSON value with no placeholder element
  - the value is passed through unchanged — raw JSON reaches the client
  - it accepts any JSON-serializable value
  - the client reads it with `useShinyOutputValue(id)`
  - call shape — **deliberate divergence**
    - `[py]` a `Renderer[Jsonifiable]` subclass, used as a decorator, assigned
      to `output[id]`
    - `[r]` a function, called as `output$id <- reactive_output(expr, ...)`
    - reason: each language's renderer idiom —
      `decisions/2026-08-13-r-python-parity.md`
  - `[py]` accepted types are whatever `Jsonifiable` admits: `dict`, `list`,
    `tuple`, `str`, `int`, `float`, `bool`, `None`
  - `[py]` a `str` return is sent as a JSON string, not a text node
  - `[py]` `auto_output_ui()` returns `None`, inherited from `Renderer` — there
    is no placeholder element to emit
  - `[py]` it declares no HTML dependencies of its own
  - `[py]` `transform()` is `async`
  - `[r]` built from `shiny::installExprFunction()` +
    `shiny::createRenderFunction()`, so it is a normal Shiny render function
  - `[r]` it takes `(expr, env = parent.frame(), quoted = FALSE)`, the standard
    Shiny render-function signature
  - `[r]` it attaches neither a UI placeholder nor an HTML dependency
  - `[r]` it recomputes when its reactive inputs change, like any render
    function

## Modules and namespacing

- ids are module-scoped on both sides, and the two agree without extra wiring
  - server side: input, output, and message ids are resolved through Shiny's
    normal module resolution
  - `[js]` client side: `ShinyModuleProvider` supplies the namespace, and hooks
    inside it prefix their ids to match
  - a module instance's input round-trips through its own namespaced
    `reactive_output` and leaves a sibling instance untouched `(e2e)`
- `[js]` every id-taking hook and component resolves its namespace identically,
  through one shared `useNamespacedId(id, explicit)`
  - `explicit === undefined` → the enclosing `ShinyModuleProvider`'s namespace,
    or no prefix when there is no provider
  - `explicit === "ns"` → prefix with `"ns-"`, ignoring any provider
  - `explicit === null` → opt out and use the bare `id`, for ids that already
    carry a prefix (e.g. `ImageOutput`'s clientdata ids)
  - `null` is deliberately not conflated with `undefined` — a `??` would
    silently fall through to the context, so the check is `!== undefined`
  - applies to `useShinyInput`, `useShinyInputValue`, `useSetShinyInput`,
    `useShinyOutputValue`, `useShinyOutputStatus`, `useShinyMessageHandler`,
    `ShinyOutput`, and `ImageOutput`
- `[js]` the prefix is joined with a single hyphen: `${namespace}-${id}`
  - an empty-string namespace yields the bare id, same as `null`
- `[js]` nesting `ShinyModuleProvider`s **overrides** rather than concatenates —
  the innermost provider wins, and a combined namespace must be passed whole
- `[py]` `send_message()` resolves `id` the same way input/output ids are, so
  the message reaches the matching in-module `useShinyMessageHandler`

## Custom messages

- `send_message(session, id, data)` sends a `shinyReactMessage` custom message
  - the payload is `{"id": <resolved id>, "data": <data>}`
  - `data` may be any JSON-serializable value
  - consumed by `useShinyMessageHandler(id, handler)` on the client
  - `[py]` it is `async` and must be awaited
  - `[r]` it is synchronous and returns `invisible(NULL)`
  - `[r]` a `session` without a callable `ns()` aborts with a message naming
    the argument — the old silent fallback to an un-namespaced id delivered
    messages no module-scoped handler matched (#184)
    - `[py]` no equivalent guard: `resolve_id()` reads the ambient module
      context rather than the session object
  - `[r]` a top-level session's namespace passes the id through unchanged
  - `[js]` an inline arrow function is safe as the handler — it is stored in a
    ref and invoked through a stable wrapper, so a new function identity each
    render does not deregister/re-register

## `[js]` Client hooks

Shared across every hook: the first hook call on the page initializes shinyreact
once (registry, restore adoption, output binding, message registry, in that
order), and no hook *registers with or sends to* Shiny until Shiny reports
initialized. Note what does **not** wait for Shiny: that one-time init itself,
the protocol-mismatch throw, the `type` validation throw, and reading an
existing registry value at render time.

- `useShinyInput(id, defaultValue, options?)` → `[value, setValue]`
  - `defaultValue` is captured on **first mount only**, like `useState`'s
    initial value
    - it is stabilized in a ref, so inline `{}` / `[]` literals are safe
    - without that, an unstable reference in the effect deps plus
      `priority: "event"` would loop render → send → update → render
  - when a registry entry for the id already exists, its current value wins over
    `defaultValue` — so a second call site, or a remount of a dynamically
    generated component, does not reset the input
  - a restored bookmark value is adopted as the initial render value, taking
    precedence over `defaultValue`
  - `debounceMs` defaults to **100**
  - `priority` maps to Shiny's `EventPriority`; `"event"` marks an event input
  - on mount it re-broadcasts the current value, so Shiny sees the input even
    when nothing has changed it
    - `debounceMs`, `priority`, and `type` are effect dependencies, so changing
      any of them mid-life re-broadcasts as well
  - it sends values *to* Shiny only — a server-side `update*Input()` does not
    flow back into React state
  - `setValue` before Shiny is initialized is a silent no-op
  - `setValue` for an id with no registry entry logs `Input <id> not found` and
    returns
  - unmounting detaches the component's setter but **keeps** the registry entry
    and its value; entries are never garbage-collected automatically
  - known wart: `debounceMs` and `priority` are per-id here, though Shiny scopes
    priority per `setInputValue()` call — with several call sites for one id,
    the last mount wins
- `useShinyInputValue(id, options?)` → `value` (read-only)
  - it returns `undefined` when no producer has registered the id yet
  - mount order does not matter: subscribing before the producer's effect runs
    queues the subscriber, which fires the moment the entry is created
  - the `MISSING` sentinel is mapped to `undefined` for consumers
  - it never writes, so a reader cannot accidentally push a value
- `useSetShinyInput(id, defaultValue, options?)` → `setValue` (write-only)
  - same registration and `defaultValue` semantics as `useShinyInput`, so it
    seeds the registry identically
  - it deliberately registers **no** `useState` setter, so values written
    elsewhere never re-render the calling component
- `useShinyOutputValue(id, defaultValue?, options?)` → `value`
  - `defaultValue` is returned until the server delivers the first value, and
    defaults to `undefined`
  - it subscribes to the value channel only — status and error changes do not
    re-render it
  - the held value **is** reset when the id or namespace changes, so the
    previous id's data is never shown as the new id's
    - it falls back to the caller's `defaultValue`
    - a new id the registry already has a value for is adopted immediately, so
      the reset does not cause a flash of `undefined`
- `useShinyOutputStatus(id, options?)` → status
  - exactly four values: `"pending"`, `"ready"`, `"recalculating"`, `"error"`
  - it starts at `"pending"` and subscribes to the status channel only
- `useShinyMessageHandler(id, handler, options?)`
  - the effect re-runs only when the resolved id changes, never on handler
    identity
  - the handler is removed on unmount and on id change
  - an empty-string resolved id silently skips registration, with no log
- `useShinyInitialized()` → boolean
  - `true` once `window.Shiny.initializedPromise` resolves
  - it resolves via the `shiny:connected` event when Shiny loads *after* the
    React tree mounts
  - a consumer mounting after initialization reads `true` immediately
  - it does not write state after unmount
- `useShinyBusy()` → boolean
  - `false` initially, `true` on `shiny:busy`, `false` on `shiny:idle`, across
    any number of cycles
  - it seeds `true` when `<html>` already carries `.shiny-busy` at first mount,
    so a consumer mounting mid-request is not stale
  - it stops responding after unmount
- both lifecycle hooks read one shared external store through
  `useSyncExternalStore`
  - one pair of DOM listeners per page regardless of consumer count
  - listeners are installed lazily on first subscribe and **never** torn down —
    they belong to the page, which sidesteps mount/unmount races and
    StrictMode re-subscribe churn
  - installation is skipped when there is no `document`, and not latched, so a
    later DOM-available render still installs them
  - the `shiny:connected` listener is `{once: true}`, so if it fires while
    `window.Shiny` is still absent, `initialized` never flips and every hook
    stays gated for the life of the page
  - the store is only for page-global runtime state; per-id hooks must keep
    using their own id-keyed registries

## `[js]` Client registries

Three id-keyed registries hold all cross-component state. The input and output
registries are exposed on `window.Shiny.reactRegistry`; the message registry on
`window.Shiny.messageRegistry`.

### Input registry

- one entry per resolved input id, holding the value, the subscriber set, the
  debounced sender, and the finalized wire type
- the wire id always carries a type suffix
  - no explicit `type` → `${id}:shinyreact.default`, so untyped inputs route
    through shinyreact's own handler
  - an explicit `type` → `${id}:${type}`
- the type is **set once**, on first `updateType()`
  - `undefined` is a valid finalized state, meaning "no explicit type"
  - a later mount omitting `type` is a no-op
  - a later mount with the same `type` is a no-op
  - a later mount with a conflicting `type` throws, and the entry is left
    unchanged; the message names both types and, for the finalized-`undefined`
    case, the actual default wire id
  - the throw is deliberate: the handler name is server-side semantics and must
    be consistent across every call site for one id
- `type` is validated at the hook, before the registry sees it
  - it must match `/^[^\s:]+$/` — non-empty, no whitespace, no `:`
  - a violation throws naming the hook, the id, and the offending value
- `setValue` accepts a React-style functional updater
  - the updater is resolved against the current value *before* sending, since a
    raw function would vanish in JSON serialization
  - successive functional updaters chain correctly
- the `MISSING` sentinel updates React state but is **not** sent to Shiny
  - this leaves the server-side input in its `MISSING` state, which raises
    `SilentException` when read — Shiny's "wait for a real value" mechanism
  - a real value after `MISSING` does send
  - `null` is an ordinary value and does send
- sends are debounced per entry, with the delay adjustable at runtime
  - the debounce is trailing-edge: the call fires after the window elapses, and
    a call inside the window resets the timer
  - `cancel()` drops a pending call and is safe with no timer pending
  - `setDelay()` affects only subsequent calls, not one already scheduled
  - the whole `opts` object, `debounceMs` included, is passed as
    `Shiny.setInputValue`'s third argument
  - a `MISSING` write **cancels** any pending send, so "real value then
    `MISSING`" inside the debounce window retracts the value rather than
    delivering it late
    - a real value written after the cancellation still delivers
- a conflicting `priority` across mounts is last-writer-wins, and **warns** when
  the value actually changes
  - deliberately not an error, unlike `type`: priority changes *when* Shiny
    recalculates, not what the value means, and throwing would break the
    documented action-button pattern (a reader on `useShinyInput` plus a button
    on `useSetShinyInput(..., { priority: "event" })` for one id)
  - the warning names the id and both values, since the winner otherwise depends
    on mount order with no signal
  - setting the same priority again, or setting it for the first time, does not
    warn
- a missing `window.Shiny`, or a `Shiny` without `setInputValue`, is tolerated —
  values are held locally and nothing throws
- `add()` on an id that already exists throws; `getOrCreate()` is the safe path
  and ignores its value argument when the entry exists
- `remove()` cancels any pending debounced send, and returns `false` for an id
  that was never registered
- `subscribe()` is the read-only path
  - it attaches and fires immediately with the current value when the entry
    exists
  - it queues when the entry does not exist yet, and drains on `add()`
  - its dispose function detaches from whichever bucket holds it, is safe to
    call twice, and is independent across multiple subscribers of one id

### Output registry

- one hidden container div (`.shiny-react-output-container`,
  `visibility: hidden`) is appended to `<body>` on the **first** `add()`,
  holding one `.shiny-react-output` div per subscribed output id
  - created lazily, not in the constructor, so constructing the registry in a
    DOM-less environment (SSR, a node test) does not throw
  - this is what lets a React component read a Shiny output with no
    server-rendered placeholder: the binding needs a DOM element, so the
    registry manufactures one
  - the manufactured divs are empty: no text content is shipped into the page
- a `ReactOutputBinding` is registered with Shiny as `shiny.reactOutput`,
  finding `.shiny-react-output` elements and routing to registry entries
  - registration no-ops when `window.Shiny` is absent, with **no retry**, so on
    that path no binding is ever registered and every `useShinyOutputValue` on
    the page silently receives nothing
  - `scheduleBindAll()` likewise returns without Shiny and does not re-arm, so
    the manufactured divs stay unbound
  - `find()` uses the global `$`, so jQuery is an implicit runtime dependency
  - `renderValue` → `setValue`, `renderError` → `setError`,
    `showProgress` → `setRecalculating`
  - a value or progress event for an unknown id logs an error and returns
- status transitions are exact
  - a fresh entry is `"pending"`
  - `setValue` → `"ready"`, and fans the value out to subscribers
  - `setRecalculating(true)` → `"recalculating"`, but **only** if a value has
    already arrived; before the first value the UI stays `"pending"`, because a
    busy server does not mean "was showing data"
  - `setRecalculating(false)` → back to `"ready"` only from `"recalculating"`;
    `"pending"` and `"error"` are left alone
  - `setError` → `"error"`, fanning the error out
  - a value arriving in the `"error"` state clears the error and returns to
    `"ready"`
  - entering `"recalculating"` from `"error"` clears the error, so status and
    error never disagree
  - a repeated identical **status** is not re-emitted; identical values and
    errors *are* re-fanned-out every time
  - `renderError` for an unknown id logs and then silently returns, unlike
    `renderValue` / `showProgress`, which log an error naming the id
- the last value and last error are cached, so a late-mounting subscriber is
  synced on attach rather than waiting for the next server update
  - status is always pushed; the value only if one has been delivered; the error
    only in the `"error"` state
- `bindAll` on the container is coalesced through one `requestAnimationFrame`,
  and preceded by `unbindAll`
- unsubscribing schedules cleanup in a `requestAnimationFrame`
  - the entry and its DOM div are removed only if still subscriber-less when the
    frame runs, so a re-subscribe within the same frame (React remount) keeps
    them
  - removal triggers a re-bind
  - the entry holds a reference to the div it created and removes that node, so
    a colliding id in the app's own markup is untouched (#227; it used a
    document-global `getElementById()` before)

### Registry initialization

- the registry pair is built by a one-time init and published on
  `window.Shiny.reactRegistry`
- the registry pair is **page-scoped**, reached through `getReactRegistry()`
  - it attaches the module registries to `window.Shiny.reactRegistry` on first
    use (`??=`), so the first copy of the library to run owns the page
  - two registries would split one input id's producers from its consumers
  - without `window.Shiny` it returns the module registries and attaches nothing
  - it never returns `undefined`; the old unchecked read of
    `shiny.reactRegistry` did, crashing a call later
- `initializeReactRegistry()` is idempotent — a second call keeps every input
  value and output subscriber, rather than silently discarding them
- construction touches no DOM, so a DOM-less environment can initialize
  shinyreact without throwing — matching the lifecycle store's policy

### Message registry

- one dispatcher is registered with Shiny for `shinyReactMessage`, once, lazily
  on the first `addHandler`
- the registry is **page-scoped**, reached through `getMessageRegistry()`
  - it attaches the module singleton to `window.Shiny.messageRegistry` on first
    use (`??=`), so the first copy of the library to run owns the page and later
    copies adopt it
  - two copies can coexist today (the server injects the IIFE even for npm-tier
    apps until #217), and Shiny has one dispatcher slot per message type — two
    registries would leave one copy's handlers dead
  - without `window.Shiny` it returns the module singleton and attaches nothing,
    since the client legitimately runs before Shiny loads
  - hooks call the accessor rather than reading `window.Shiny.messageRegistry`,
    which could be unset and threw a TypeError (#228)
- `initializeMessageRegistry()` attaches eagerly during shinyreact's init, and is
  a no-op without Shiny — nothing depends on it having run
- messages are routed by `id` to every handler registered for it, so several
  components can listen to one id
- removing the last handler for an id drops the id's entry
- a message with no registered handlers is silently ignored

## `[r]` `output_ui(render_fn, id)`

- builds the HTML a render function's matching `*Output()` would produce —
  `output_ui(renderText(...), "x")` is `textOutput("x")` — without the caller
  knowing which output function that is
- it uses the render function's `outputFunc` / `outputArgs` attributes, the same
  contract shiny's own `knit_print` and Express mode use
- the render expression is **never evaluated**; only the UI constructor runs
- it is the R counterpart of Python's `Renderer.auto_output_ui()`
- a non-render-function argument aborts, naming the argument and the type given
- a render function with no `outputFunc` attribute aborts
  - but `reactive_output()` does **not** hit this branch: passing
    `outputFunc = NULL` to `createRenderFunction()` makes shiny substitute a
    placeholder constructor, so the attribute is present and
    `output_ui(reactive_output({...}), "x")` returns shiny's dep-less
    `<pre>No UI/output function provided...</pre>`
  - the abort's message says so — it points at a render function built outside
    `createRenderFunction()`, which is the only way to reach it (#234)
- the internal `output_ui_or_null()` variant returns `NULL` only when the
  attribute is genuinely absent
  - for `reactive_output()` outputs a harvest therefore builds the placeholder
    UI and finds **zero** dependencies, rather than skipping the output
  - harmless either way, since a dep-less UI contributes nothing
- it is unexported (`@noRd`)

## `[js]` Pushed-dependency client

- it registers a `shinyreact-deps` custom-message handler that renders the
  pushed dependencies, then re-runs `bindAll` on `document.documentElement`
  - this is what lets a `ShinyOutput` that mounted *before* its binding existed
    get bound
  - page-wide re-binding is safe because Shiny skips elements already marked
    `.shiny-bound-*`, and the shiny client replays stored output values on late
    bind
- failures are caught and logged, never thrown
- it sends the `.shinyreact_init:shinyreact.init` ping once, after
  `initializedPromise` resolves
- it installs immediately when Shiny is already present, otherwise once on
  `shiny:connected`
  - the `shiny:connected` listener stays subscribed until `window.Shiny` is
    actually readable, then unsubscribes — it is deliberately **not**
    `{once: true}`, which would consume the event before Shiny existed and
    leave discovery uninstalled
- it no-ops when there is no `document`
- **both entry points install it** — `src/index.ts` (IIFE) and `src/npm.ts`
  (npm ESM), so both tiers get discovery and both send the bootstrap ping
  - the npm entry omitted it until #233, which left bundler-tier apps with no
    `shinyreact-deps` handler and no ping, so the server never installed
    discovery for the session at all
  - pinned by `entry-parity.test.ts`, which imports each entry and asserts its
    side effects — including the two *deliberate* tier differences (only the
    IIFE installs `window.shinyreact`; only the npm build treats a missing
    config tag as fatal)
- installing twice is a no-op, so calling it from both entries is safe

## `[js]` Client components

### `ImageOutput`

- it renders a Shiny `renderImage()` / `renderPlot()` output as an `<img>` sized
  to the element, rather than to the image's intrinsic size
- it drives Shiny's clientdata inputs directly — `.clientdata_output_<id>_width`,
  `_height`, `_hidden` — with its own namespace already applied, so the hooks'
  namespacing is suppressed to avoid double-prefixing
- width/height start as `MISSING`, so the server does not render until the
  element has actually been measured
- before the first image arrives it renders a placeholder div with a spinner,
  and measures **that**
  - without it, `@render.plot` could never fire: the `<img>` only exists once
    image data exists, which needs dimensions, which need the `<img>` — a
    chicken-and-egg loop
  - the first measurement is synchronous, so the very first render request
    carries dimensions
- resizes are watched with a `ResizeObserver` and debounced, default **400 ms**
  - the debounced handler re-measures only when `img.complete`
- `width` / `height` are CSS size strings applied to **both** the placeholder
  and the `<img>`; `className` likewise applies to both
  - with neither, the element must be sized by CSS or the image renders 0×0
- 0×0 measurements are ignored, so a `display: none` element does not trigger a
  server re-render that would invalidate the current image
- a truthy `.clientdata_output_<id>_hidden` renders nothing at all
  - in practice it never fires: that id is a client-owned `useShinyInput`
    defaulting to `false`, and the client never consumes server-pushed input
    values, so nothing sets it
- `onRecalculating` is called with whether the output status is
  `"recalculating"`
- two `ImageOutput`s sharing an id both receive the same image, sized for only
  one of them

### `ShinyReactComponentElement`

- a base class for custom elements that mount a React component with Shiny
  wiring, so server-rendered HTML can host React islands
- `connectedCallback` captures slots, clears content, creates a root, and
  renders; `disconnectedCallback` unbinds Shiny and unmounts the root
- the element's `id` becomes the module namespace, and the tree is wrapped in a
  `ShinyModuleProvider` when there is one
- `getConfig()` turns `data-*` attributes into props
  - each value is `JSON.parse`d when possible, so numbers, booleans, arrays, and
    objects arrive typed
  - a non-JSON value falls back to the raw string
- `captureSlots()` preserves server-rendered children across the React mount
  - `[data-slot]` direct children are captured by slot name
  - all remaining direct children are captured under `"__children__"`
  - an element with no children captures nothing
- `mountSlot()` moves captured nodes into a container and calls
  `Shiny.bindAll` on it, so traditional Shiny inputs inside a slot bind
  - an unknown slot name is a silent no-op
- `clearContent()` is overridable with a no-op for elements that must preserve
  their existing DOM
- `disconnectedCallback` calls `Shiny.unbindAll(this)` **without**
  `includeSelf`, so the element itself is never unbound — the inverse of
  `ShinyOutput`'s deliberate choice, and unexplained (#223)
- a subclass with no `static component` and no `render()` override logs an
  error and renders nothing

## Page entry points

Shared across all of them: the server emits no UI components. Each attaches
the shinyreact bundle dependency and the `#shinyreact-config` tag — except
`page_bare()`, which attaches neither.

### `page_bare(*args, title=None, lang="en")`

- the escape hatch: Shiny's own dependencies, nothing of shinyreact's
  - `[py]` wraps `shiny.ui.page_bootstrap()`, so the page carries Bootstrap
  - `[r]` wraps `shiny::bootstrapPage()`, same effect
  - attaches no shinyreact JS or CSS, and no `#shinyreact-config` tag
  - `title` is emitted exactly **once** (#186 was a duplicate-`<title>` bug)
  - `HTMLDependency` positional args are hoisted to `<head>` by Shiny
  - children are wrapped with no mount container of their own — no `#root`
  - `lang` sets the `<html lang>` attribute, defaulting to `"en"`

### `page_react(*args, src_dir=None, js_file="ui.js", css_file="ui.css", title=None, lang="en")`

- the zero-config page: no HTML file exists or is needed
  - it emits **no body HTML at all** — the client appends its own mount
    container to `<body>`
  - it attaches three things: the bundle dep, the config tag, and the app's own
    asset dep (`page_react_dep`)
  - extra positional args (children, `HTMLDependency`) are included in the page
  - `title` defaults to the app folder's name
    - the app folder is `src_dir`'s **parent** when `src_dir` is named `www`,
      and `src_dir` itself otherwise
    - an explicit `title` overrides that
  - `js_file` / `css_file` are forwarded to `page_react_dep`, so a missing
    `ui.css` is skipped and a missing `ui.js` warns
  - `[py]` `src_dir` defaults to `www/` next to the **calling module**
    - a relative `src_dir` resolves against the calling module's directory
    - an absolute `src_dir` is used verbatim
    - no caller `__file__` (REPL, `exec`) → resolves against `Path.cwd()`
    - the frame read is the *immediate* caller, so a wrapper function resolves
      against the wrapper's directory, not the app's
  - `[r]` `src_dir` defaults to `"www"` and resolves against the working
    directory — **deliberate divergence**
    - under `runApp()` / `shinyApp()` that is the app directory, so the default
      just works
    - R has no per-caller `__file__`, so there is nothing else to resolve
      against; pass an absolute path to be independent of the working directory
    - reason: `decisions/2026-08-13-r-python-parity.md`
  - `[r]` the app name comes from `normalizePath(src_dir, mustWork = FALSE)`,
    so a missing `src_dir` does not error — but it degrades badly: the title
    becomes `.` and the asset dependency is named `.`, serving `/lib/.-0/`
    (#242; untested in either language)

### `page_react_html(path="www/index.html")`

- for apps that own a complete HTML document (what a Vite build emits)
  - the document must contain a `{{ headContent() }}` marker; Shiny's and
    shinyreact's tags render **at the marker**, not appended to `<head>`
    - detection is a plain string match over the whole document, so a marker in
      `<body>` passes and the deps render there — despite the error message
      asserting `<head>` (#243)
    - `[r]` the match is `fixed = TRUE` on the exact spelling, so
      `{{headContent()}}` is rejected even though `htmlTemplate()` accepts it
      — documented in `?page_react_html`
  - `[py]` the document's own body is preserved verbatim
  - `[r]` the body is **not** verbatim: `htmlTemplate()` evaluates every
    `{{ ... }}` anywhere in the document as R code, with `parent = globalenv()`
    - a body containing `{{ 6*7 }}` renders `42`; a Handlebars/Mustache/Vue
      document with `{{ }}` in the body is evaluated as R or errors
    - **deliberate**, and documented in `?page_react_html`: it is R's own
      templating idiom. Python replaces only the marker (#223)
  - a document without the marker raises, and the message names the file, the
    marker, and `page_react()` as the alternative
  - a missing file raises, naming the resolved path
    - `[r]` the error also names the working directory, since that is what a
      relative path resolved against
  - the file is read at call time, and re-read only when it changes on disk
    - `[py]` under `ReactApp` the UI is a per-request function, so edits appear
      with **no restart**; the read is gated on `(st_mtime_ns, st_size)`, so an
      unchanged document is read once and served from cache thereafter
    - `[py]` under `set_react_page()`'s HTML mode the read happens once, at
      call time, so edits there *do* need a restart (issue #82)
    - `[r]` read twice per call — once with `brio` for the marker check, once by
      `htmlTemplate()` to render
  - it does **not** discover traditional-renderer dependencies
  - `[py]` it returns a `ReactHtmlDocument`
    - a `shiny.ui.PageDocument` subclass that also remembers the document's
      directory, so `ReactApp` can serve the assets the document references
    - `PageDocument` prefixes Shiny's own dependencies; shinyreact adds only
      its bundle and the config tag
    - an absolute `path` is verbatim; a relative one resolves against the
      calling module's directory; no caller `__file__` → `Path.cwd()`
    - it works as `shiny.App(ui=...)`, but only `ReactApp` mounts the
      document's directory — under plain `shiny.App` the sibling `ui.js` is
      not served
    - `shiny.ui.PageDocument` arrives with py-shiny#2475, consumed as a git
      dependency until it releases (issue #216)
  - `[r]` used directly as `shinyApp(ui = page_react_html())`, implemented with
    `htmltools::htmlTemplate(path, document_ = TRUE)`
    - a relative `path` resolves against the working directory; there is no
      caller-directory fallback because R has no `__file__`
    - the served document is decoded as UTF-8 by `htmlTemplate()` itself
      (`readChar(useBytes = TRUE)` + an explicit UTF-8 encoding); `brio` only
      reads the throwaway copy used for the marker check
      - `[py]` reads with an explicit `encoding="utf-8"` too, on both the
        `page_react_html()` and `set_react_page()` paths
    - the deps are attached with `attachDependencies(append = TRUE)`, and
      `htmlTemplate()` renders them at the marker
    - the config tag rides in as an `htmlDependency` named
      `shinyreact-config`, versioned by the protocol version, shipping no files
      (`src = c(href = "")`) and carrying the tag as its `head` HTML — a plain
      tag has nowhere to land in a template document
    - assets the document references must live in `www/`, which Shiny serves
      statically — there is no `ReactApp`-style auto-mount

### `[py]` `set_react_page(path=None)` — Shiny Express only

- no R counterpart: R has no Express-style page mechanism
- it sets the Express page via `page_opts(page_fn=...)`
- `path=None` prefers `www/index.html` when it exists
- `path=None` with no `www/index.html` falls back to `page_react()`-style
  discovery of `www/ui.js` / `www/ui.css`, titled after the app folder
- an explicitly passed `path` **must** exist — missing raises `FileNotFoundError`
- an absolute `path` is verbatim; a relative one resolves against the calling
  module's directory; no caller `__file__` → `Path.cwd()`
- it accepts `str` or `Path`
- in HTML mode the file is read **once**, at `set_react_page()` call time
  - the page body is `TagList(bundle + config tag, harvested deps, raw HTML)`
  - a per-request re-read is impossible from inside this package: Express
    tagifies the page once at startup and serves those bytes for every request
    (issue #82), so editing `index.html` requires a server restart
- in **both** modes, traditional Shiny renderer dependencies are discovered and
  injected into `<head>`

### `[py]` `ReactApp(server, *, ui=None, **kwargs)`

- a `shiny.App` subclass whose UI is discovered, not passed — the app file is
  just the server
- with no `ui=`, discovery runs next to the **calling module**
  - `www/index.html` present → `page_react_html()`, and `www/` is mounted at
    `/` through `static_assets`, unless `static_assets` was passed
  - otherwise → `page_react(src_dir=www)`, whose dependency serves the assets
  - no caller `__file__` → discovery resolves against `Path.cwd()`
  - the frame read is the *immediate* caller, so a helper wrapping
    `ReactApp(...)` must pass `ui=` explicitly
- the discovered UI is a **per-request function**, so `bookmark_store="url"`
  restore works with no further wiring
  - the mode is re-checked **per request**, so creating or deleting
    `www/index.html` during a dev session switches modes with no restart
  - `www/` is mounted at `/` whenever the directory exists, since
    `static_assets` is a constructor argument and cannot be per-request —
    mounting a dir the app never serves from is harmless, a missing mount is a
    404 per asset
  - an explicitly passed `static_assets` — **including `None`** — wins over the
    auto-mount, and replaces rather than merges
- `ui=` overrides discovery and otherwise behaves like `shiny.App`'s `ui`
  - a plain UI object passes straight through
  - a `ReactHtmlDocument` passed as `ui=` still gets its directory mounted at
    `/`, unless `static_assets` was passed
- all other `kwargs` reach `shiny.App` untouched
- a `GET /` returns the complete HTML document, not a fragment
- it registers the dependency file routes, so the `/lib/<name>-<version>/`
  URLs the page references actually resolve
- `[r]` no counterpart — R has no `shiny.App` subclass equivalent

## Traditional Shiny interop

### `[js]` `ShinyOutput` — a Shiny output element inside a React tree

- it renders a Shiny output element (by tag name like `shiny-data-frame`, or a
  `div` carrying a binding class like `plotly-output`) and binds it
  - `tagName` defaults to `"div"`
  - it depends on no server-side placeholder — nothing on the server needs to
    emit the element
  - `shiny-data-frame` renders and populates inside it `(e2e)`
  - a plotly widget renders inside it, sized (not 0×0) `(e2e)`
- **no wrapper element** — the `ref` goes directly onto the rendered element,
  so direct-child CSS (`> *`, flex `gap`, grid) behaves as the caller expects
  (#61)
  - pinned by both a direct-child locator and a computed-style check `(e2e)`
- it adds no classes of its own; caller `className` and arbitrary HTML
  attributes land on the rendered element `(e2e)`
  - Shiny's binding pass adds `shiny-bound-output` after mount
- binding scope is deliberately asymmetric, because Shiny's API is
  - `bindAll` receives the **parent** element, since output bindings search
    descendants only and would otherwise skip the element itself
  - re-binding the parent is safe: Shiny skips already-bound elements, so
    siblings are not re-bound
  - `unbindAll` receives **its own** element with `includeSelf=true`, so
    unmounting one output cannot clobber siblings
- it re-binds when the resolved id or `tagName` changes, and not when unrelated
  props change
  - an id change unbinds the previously bound element before binding the new one
- every prop other than `id` / `tagName` / `namespace` is forwarded to the
  rendered element, including event handlers and children
  - children act as fallback content until Shiny renders into the element
- several `ShinyOutput`s bind independently, and unmounting one unbinds only its
  own element
- bind/unbind failures are caught and logged with the resolved output id and the
  phase, never thrown
  - a promise-returning `bindAll` has its rejection caught too
  - the component stays mounted after a failure, and a failing sibling does not
    stop the others from rendering and binding
  - it no-ops when `window.Shiny` is absent, and tolerates a `Shiny` that is
    missing `bindAll` or `unbindAll`
  - `Shiny` appearing on `window` *after* mount is ignored — there is no retry

### Renderer dependency discovery

Both languages deliver traditional renderers' `HTMLDependency` objects
automatically. Every page function gets push-based per-session discovery;
Python's Express `set_react_page()` *additionally* inlines them into the
initial page.

- discovery is per-session and push-based, and covers every page function
  - Core-mode page functions are plain UI values rendered before any `server()`
    runs, so deps cannot be inlined into the initial page the way Express can
  - after **every** reactive flush the session's registered outputs are diffed,
    so outputs registered after startup (a module server mounted in an
    observer) are covered too, not just the first flush
  - each new output's UI comes from the renderer's matching output function
    (`[r]` `output_ui()` + `htmltools::findDependencies()`, `[py]`
    `auto_output_ui()` tagified + `get_dependencies()`); an output whose UI is
    not a tag (e.g. `reactive_output`) contributes nothing
  - deps are de-duplicated by `name@version` against what this session already
    sent, and nothing is sent when nothing is new
  - each dep is registered as a served resource (`[r]`
    `shiny::createWebDependency()`, `[py]` `session._process_ui()`), then ships
    as a `shinyreact-deps` custom message
  - overlap with deps already in the static `<head>` is harmless — the client
    skips those by name
  - `[py]` an output registered after page load in an app with no dynamic-UI
    holder gets its binding only this way `(e2e)`
  - it reads the session's private registered-output list, since neither shiny
    exposes an API to enumerate outputs (`[r]`
    `session$.__enclos_env__$private$.outputs`, `[py]`
    `session.output._outputs`)
  - it no-ops, rather than erroring, on a session missing the pieces it needs
    (`[r]` `NULL`, no `userData`, no `onFlushed` / `getOutput` — which is what
    makes `MockShinySession` safe; `[py]` `None`, no `output._outputs`, no
    `on_flushed`)
  - it installs at most once per session (`[r]` latched on
    `userData$.shinyreact_dep_discovery`, `[py]` on a
    `_shinyreact_dep_discovery` session attribute)
- it does not fix shinywidgets' `comm_open` race (#160) — that message has its
  own side channel, which R's htmlwidgets do not

### `[py]` `set_react_page()` harvesting

- top-level renderers Express passes to the page function are harvested
- renderers registered on the active session are harvested too, which is what
  covers renderers defined inside `@module.server` (issue #87)
  - a `render_plotly` inside a module gets its `ipywidget-output-binding`
    dependency into `<head>` `(e2e)`
- non-`Renderer` positional args are skipped
- a renderer whose `auto_output_ui()` is not a `Tag` / `TagList` (e.g.
  `reactive_output`, which returns `None`) contributes no dependencies
- each renderer's `auto_output_ui()` is **tagified** before its dependencies
  are read, so deps that only materialize during tagification are found
- renderers mounted dynamically *after* page load are not harvested into
  `<head>` (the post-flush push above delivers their deps instead)
  - a renderer registered inside a `@reactive.effect` is absent from the served
    HTML, and its dependency still arrives — pinned `(e2e)` for both delivery
    paths: a `@render.ui` holder (Shiny's own dynamic-UI path also covers that
    one) and a bare `<ShinyOutput>` with no holder, where the post-flush push
    is the only route
    - `[py]` the no-holder case: a `render.data_frame` registered in an effect
      renders its rows and gains `shiny-bound-output` only because the pushed
      dep loaded and `bindAll` re-ran `(e2e)`
- duplicate deps across the two harvest passes are harmless: Shiny
  de-duplicates by name + version

## Asset delivery

- the shinyreact bundle ships as one `HTMLDependency` named `shinyreact`
  - its version is the bundle file's mtime in whole seconds, so browsers
    re-fetch after a `make update-dist`
  - the version fallback when the bundle file is missing differs
    - `[py]` the literal `"0.1.0"`
    - `[r]` `packageVersion("shinyreact")`
  - the script is `shinyreact.js` with a `defer` attribute
  - the stylesheet is `shinyreact.css`, attached unconditionally (no existence
    check)
  - the dependency on its own carries **no** `#shinyreact-config` tag — only
    the page-level helper pairs the two, so a caller embedding just the bundle
    gets no protocol/restore payload
  - `[py]` served from `pkg-py/src/shinyreact/www/`
  - `[r]` served from `pkg-r/inst/lib/shiny/`
- the app's own entry assets ship as a **second, separate** `HTMLDependency`
  - built by `page_react_dep()`, whose `js_file` / `css_file` default to
    `"ui.js"` / `"ui.css"` in both languages
    - `[py]` `name=None`, resolved to the basename inside the body
    - `[r]` `name = basename(src_dir)`, a default argument
  - the dependency name defaults to `src_dir`'s basename
    - except from `page_react()`, which overrides it with the *app folder* name,
      so the URL is `/lib/<appname>-<mtime>/` and never `/lib/www-<mtime>/`
      (both languages)
  - the version is `js_file`'s mtime in whole seconds — every edit busts the
    browser cache, which is why this beats hand-written `<script src>` tags
  - the version is `"0"` when `js_file` is missing
  - the script tag is `type="module"` — unlike the bundle's `defer`
    - a classic `<script defer>` throws on the bundle's first `import`, and
      `type="module"` is implicitly deferred, so no `defer` is added
    - a classic (non-module) bundle needs a hand-built dependency instead
  - the script tag is emitted only when `js_file` exists
    - a missing `js_file` warns, naming the resolved path and suggesting the
      bundle be built, rather than emitting a tag that 404s
    - the warning exists because an empty dependency would otherwise fail
      silently — there would not even be a console 404 to go on
  - the stylesheet is emitted only when `css_file` exists, so a bundle that
    ships no CSS emits no link tag
    - `css_file=None` never emits a stylesheet
  - `[py]` **all four** parameters are keyword-only (a bare `*` leads the
    signature), so there is no positional call form at all
  - `[py]` an omitted `src_dir` is inferred from the immediate calling frame's
    `__file__`, falling back to `Path.cwd()`
  - `[r]` `src_dir` is a required first positional argument, with no inference
    — **deliberate divergence**
    - reason: `decisions/2026-08-13-r-python-parity.md`
- built assets are committed to the repo and shipped inside the packages
  - `pkg-js/dist/` is the build output; `make update-dist` copies it into both
    server packages

## Bookmark restore

- restored input values reach the client through the `#shinyreact-config` tag's
  `restore` key
  - `[js]` the client seeds `useShinyInput` initial values from it
  - `restore` is omitted entirely when no bookmark is active
  - `restore` is omitted when a restore context exists but holds no values
  - a URL-mode bookmark restores React-controlled inputs *and* the
    server-rendered output that depends on them `(e2e)`
  - a plain URL renders the client's own defaults `(e2e)`
- reading the restore values must not consume them
  - `[py]` it reads `ctx.input.as_dict()` directly — not `RestoreInputSet.get()`
    and not the public `restore_input()` — so values are not marked pending and
    stay available to later `restore_input()` callers in the same render
  - `[r]` it reads `ctx$input$asList()` for the same reason — `get()` would
    append to `private$pending` and break the app's own `restoreInput()` calls
    in the same render
    - `asList()` passes `all.names = TRUE`, which preserves keys R treats as
      hidden — i.e. those with a **leading dot**, such as `.clientdata_*`
      (`__proto__` is returned either way; nothing pins the dot case)
- no active session or restore context yields no `restore` key rather than an
  error
  - `[py]` the "no session" case surfaces as a caught `RuntimeError`
  - `[r]` `hasCurrentRestoreContext()` returns `FALSE` rather than erroring, so
    no `tryCatch` is needed
  - `[r]` a context with a `NULL` `$input`, or a `NULL` value map, also yields
    no `restore` key
- `[r]` three Shiny internals are reached through named `shiny___*` wrappers
  using `getFromNamespace()`, so a future public API changes one wrapper each
  - the policy is not total: `ctx$input$asList()` calls a private
    `shiny:::RestoreInputSet` R6 method directly, with no wrapper
  - nor is it package-wide: `install_dep_discovery()` reads
    `session$.__enclos_env__$private$.outputs` unwrapped too, so three wrappers
    cover three of five private couplings
  - `[py]` has no equivalent policy: it reads private `session.output._outputs`
    and imports from private `shiny.bookmark._restore_state` at module top
    level, and pins a py-shiny **git branch** rather than a version (#216)
  - errors from those internals are deliberately allowed to propagate:
    swallowing them would silently disable bookmark restore across a Shiny
    release with no signal to the app author
  - `DESCRIPTION` pins `shiny (>= 1.13.0)` for exactly these internals
- `[js]` restored values are adopted before anything else runs
  - adoption happens inside shinyreact's one-time init, ahead of the output
    binding, so the registry already holds restored values at the first
    `useShinyInput` mount
  - each value is seeded with the registry's `add()`, **not** `setValue()`, so
    nothing is echoed back to the server as a fresh input
  - seeding drains any subscriber that was queued before the entry existed
  - a namespaced restore key seeds the namespaced entry, so module inputs
    restore too
- `[js]` `window.shinyreact._restore` is a DevTools sentinel only
  - it is written as `{"-applied": true, "-values": {...}}`
  - with no restore data it reads `{"-applied":true,"-values":{}}` `(e2e)`
  - a value pre-set there is **ignored** — the config tag is the only channel
  - it is idempotent: a second run sees `"-applied"` and preserves the existing
    snapshot rather than re-applying
  - the protocol handshake runs **before** that check, so a pre-set or forged
    sentinel cannot skip version checking — it only suppresses re-applying
    (#226 fixed the ordering; before it, the sentinel silently disabled both)
  - the namespace is created when `window.shinyreact` does not exist yet
  - `"-values"` is a **null-prototype** object, so an input id of `__proto__` or
    `constructor` cannot pollute the prototype chain — defense in depth, since
    `JSON.parse` already treats those keys as ordinary properties
- the payload is JSON inside a `type="application/json"` script tag, so the
  browser never executes it as JavaScript and no JS-string escaping is needed
  - every `<` is escaped to `\u003c`, so the payload can never contain
    `</script` (which would terminate the tag) or `<!--`
  - U+2028 / U+2029 round-trip intact — they were a hazard only while the
    payload was a JS string literal (#183), and are inert in a JSON tag
    - `[py]` they are escaped to `\uXXXX`, since `json.dumps` defaults to
      `ensure_ascii=True`
    - `[r]` they are emitted literally — jsonlite has no `ensure_ascii`
      equivalent, and no escape is needed because the tag is never parsed as
      JavaScript
  - values containing quotes, newlines, tabs, and other control characters
    round-trip unchanged
  - `[r]` values are serialized with Shiny's own `toJSON()`, not jsonlite's
    defaults, so restored inputs serialize exactly like every other value
    Shiny sends the client
    - `digits = I(16)` — jsonlite's default of 4 silently rounded doubles
      (3.14159265 became 3.1416)
      - it is really `getOption("shiny.json.digits", I(16))`, so an app setting
        `options(shiny.json.digits = 2)` silently truncates restore precision;
        Python has no equivalent global (#223)
    - `null = "null"` / `na = "null"` — jsonlite emits `NULL` as `{}`, where
      Python's `json.dumps` emits `null`
    - `auto_unbox = TRUE`, and `protocolVersion` is explicitly
      `jsonlite::unbox()`ed — though redundantly, since `auto_unbox = TRUE`
      already emits it as `"1.0"`
  - keys like `__proto__` and `constructor` are ordinary own properties after
    `JSON.parse`, so emitting them is safe
- SECURITY: bookmarked values are visible in the page source
  - in URL mode the values are already in the URL, so the tag adds no exposure
  - in server-stored mode (`?_state_id_=`) the URL hides them but the tag
    re-exposes them in the page source
  - anything that can read the HTML — extensions, logging proxies, screen
    capture, View Source — can read them, so apps must not bookmark
    credentials, tokens, or PII

## `[js]` JS distribution

- one source tree produces two builds, so both speak the same protocol version
- the IIFE bundle (`pkg-js/dist/shinyreact.js`) is what the R and Python
  packages ship
  - it is self-contained: React 19 and the vendored `@posit/shiny-react` are
    bundled in
  - it installs the public API at `window.shinyreact` once, at boot, as a plain
    assignment — nothing writes that namespace before the bundle runs
  - CSS is a side-effect import, which is how Vite bundles it
  - a missing `#shinyreact-config` tag is tolerated
- the npm ESM build (`@posit/shinyreact`) is for bundler-tier apps
  - React and ReactDOM are **peer** dependencies resolved by the app's bundler,
    so dev builds get a development React with Fast Refresh
  - hooks are imported directly rather than read off `window.shinyreact`
  - it exports `PROTOCOL_VERSION`
  - it does **not** re-export React / ReactDOM
  - the stylesheet ships as `dist-npm/style.css`, reachable as
    `@posit/shinyreact/styles` (#229; the build emitted no CSS at all before,
    leaving `ImageOutput`'s spinner without its `@keyframes spin`)
    - Vite does not inject a CSS import into a lib-mode ESM bundle, so
      consumers opt in rather than having it forced on them
  - a missing `#shinyreact-config` tag is a hard error, opted into at import
- `window.shinyreact` contains exactly: `useShinyInput`, `useShinyInputValue`,
  `useSetShinyInput`, `useShinyOutputValue`, `useShinyOutputStatus`,
  `useShinyMessageHandler`, `useShinyInitialized`, `useShinyBusy`,
  `ImageOutput`, `MISSING`, `ShinyModuleProvider`,
  `ShinyReactComponentElement`, `ShinyOutput`, `React`, `ReactDOM`
  - `React` / `ReactDOM` are exposed so downstream ESM builds can externalize
    to them and avoid a second React instance

## Public API surface

- `[py]` `shinyreact.__all__` is exactly: `ReactApp`, `page_bare`,
  `page_react`, `page_react_dep`, `page_react_html`, `reactive_output`,
  `send_message`, `set_react_page`
  - `requires-python` is `>=3.10`; the test matrix covers 3.10–3.14
  - it depends on `shiny` and `htmltools>=0.7.0`
    - the `shiny` dependency is a **git** reference until py-shiny#2475
      releases (issue #216)
- `[r]` `NAMESPACE` exports are exactly: `page_bare`, `page_react`,
  `page_react_dep`, `page_react_html`, `reactive_output`, `send_message`
  - the input handlers, the bundle dependency, and the config tag are all
    internal — there is no exported way to attach the bundle without a page
    function
  - it depends on `shiny (>= 1.13.0)`, and imports `brio`, `cli`, `htmltools`,
    `jsonlite`, and `utils` (#225 added the missing `utils`)
- the R surface is Python's minus two: no `set_react_page()` (Express has no R
  counterpart) and no `ReactApp` (no `shiny.App` class to subclass)
  - renderer-dependency discovery exists in **both**, by different mechanisms
    (see Renderer dependency discovery)
- the two servers ship no UI components at all — that is the point of the
  package, not an omission
