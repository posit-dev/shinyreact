# Bookmarking and initial state — restoration design

Tracks: [#27](https://github.com/posit-dev/shinyreact/issues/27).

## Problem

Shiny's traditional bookmarking re-renders the UI function per request and
injects restored values into the HTML (e.g. `<input value="hello">`). In
shinyreact, the page HTML is either a `#root` div (`page_react`, `app.py`
pattern) or a static `index.html` (`set_react_page`, `ui.tsx` pattern) — neither
contains the input elements to inject into. The React client owns input state.
Today, bookmarked state is silently dropped on page load.

## Scope

In scope:

- **Restoration of input values only** — `RestoreContext.input` values reach
  React inputs as their initial values on first mount.
- **Both `app.py` and `ui.tsx` patterns** — `page_react()` and
  `set_react_page()` both gain restoration behaviour automatically.
- **Both bookmark modes** — URL-encoded (`?_inputs_&...`) and server-stored
  (`?_state_id_=...`) flow through the same mechanism, since Shiny converts
  both into a `RestoreContext` before HTML render.

Out of scope (this PR):

- **No save side.** Apps still trigger `session.do_bookmark()` themselves; we
  do not ship a `useShinyBookmark()` React hook.
- **No custom-value channel.** Shiny's `onBookmark`/`onRestore` callback
  payload (`RestoreContext.values`) is not exposed to React. Putting arbitrary
  app data into the page source is a separate decision and is intentionally
  not part of this design.
- **No Python callback hooks.** No `page_react(on_bookmark=..., on_restore=...)`
  parameters. Apps that need server-side bookmark callbacks use Shiny's
  existing app-level APIs.
- **End-to-end browser tests on a non-py-shiny harness.** Covered by the
  py-shiny Playwright integration in the testing section.

## Mechanism

At HTML render time, `page_react()` and `_react_page_fn()` (the function
`set_react_page()` installs) read the active `RestoreContext` and emit a
`<script>` tag in `<head>` that sets `window.shinyreact._restore` to a
`{id: value}` map of restored input values:

```html
<script>
  window.shinyreact = window.shinyreact || {};
  window.shinyreact._restore = JSON.parse('<escaped JSON>');
</script>
```

The shinyreact JS bundle's one-time `ensureShinyReactInitialized()` reads
that global, batch-seeds the input registry, then replaces the global with a
sentinel `{ _applied: true }`. `useShinyInput`, `useSetShinyInput`, and
`useShinyInputValue` all consult the registry first when seeding their
state — the existing branch wins automatically once the registry holds the
restored values, with no changes to those hooks themselves.

### Why HTML injection rather than a websocket round-trip

The original sketch in `DESIGN.md` proposed a server → client websocket
message of restored values during the `init` handshake. HTML injection is
simpler:

- **Synchronous.** Restored values are present at the very first React
  render. No flicker, no "default-then-restored" transition, no new init
  lifecycle state for app authors to think about.
- **No new message type.** The Shiny init protocol is unchanged.
- **Same path for both patterns.** `page_react` and `_react_page_fn` are
  both Shiny page functions that run per request and have access to the
  active `RestoreContext`.

The cost is that restored values appear in the rendered HTML. See the
**Security** section.

### Underscore prefix and stability

`window.shinyreact._restore` is documented as **internal** — apps must not
read it. The underscore prefix is the convention. The exposed surface is
the existing hooks (`useShinyInput`, etc.) which adopt restored values
transparently.

## JS-side adoption

Implemented in `ensureShinyReactInitialized()` (`js/src/shiny-react/use-shiny.ts`):

```ts
const restore = window.shinyreact?._restore;
if (restore && typeof restore === "object" && !restore._applied) {
  const reactRegistry = getReactRegistry();
  for (const [id, value] of Object.entries(restore)) {
    reactRegistry.inputs.add(id, value);  // seeds; does NOT send to Shiny
  }
}
window.shinyreact = window.shinyreact || {};
window.shinyreact._restore = { _applied: true };
```

Notes:

- **`add` not `setValue`.** The constructor stores the value without invoking
  `shinySetInputValueDebounced`. The send to Shiny happens at the existing
  path: when `useShinyInput`'s `useEffect` runs
  `inputRegistryEntry.setValue(inputRegistryEntry.getValue())` on first
  mount.
- **`pendingSubscribers` drained automatically.** `inputs.add(id, value)`
  fires queued read-only subscribers (`useShinyInputValue` consumers that
  mounted before the producer) with the restored value.
- **Sentinel after batch.** Replacing `_restore` with `{ _applied: true }`
  signals "restore was applied" in DevTools, distinct from "never set"
  (`undefined`) and "data still present" (object with input keys). Apps
  that try to read `_restore.foo` post-init see `undefined` — same outcome
  as before, plus a useful debugging signal.
- **Idempotent guard.** The `!restore._applied` check protects against
  re-entry. `ensureShinyReactInitialized()` itself short-circuits via its
  existing `shinyReactInitialized` flag, so this is belt-and-braces.
- **No changes to `useShinyInput` / `useSetShinyInput` / `useShinyInputValue`
  themselves.** Their existing registry-first lookup picks up the seeded
  values; `defaultValue` is ignored when `getOrCreate(id, default)` returns
  the existing entry.
- **Namespaced ids.** Restore keys are stored using their fully-namespaced
  form (matching what the server saw on the original session). The lookup
  at hook call time, which uses `applyNamespace(id, namespace)`, finds them
  naturally.

A small `bookmark.ts` (or extension to `utils.ts`) houses the
`applyRestoredValues()` helper so the batch logic is centralised and
testable. The function is called from `ensureShinyReactInitialized()` after
`initializeReactRegistry()`.

## Python emission

A single helper builds the script tag, used by both page functions
(`pkg-py/src/shinyreact/_bookmark.py`, or kept in `_page.py` if it's small
enough to not warrant a separate file):

```python
def _restore_script_tag() -> HTMLDependency | None:
    """Return a head-injected <script> carrying restored input values, or None.

    Reads the active Shiny RestoreContext set up by App._on_root_request_cb.
    Returns None when no bookmark query string was parsed (no values to ship).
    Reads values directly from the underlying input map — does NOT call
    restore_input(id, default), which would mark each value pending and let
    Shiny's normal "consumed on first flush" semantic claim them. We're only
    reporting the values to the client, not consuming them.

    SECURITY: bookmarked input values appear in the rendered HTML page source.
    URL bookmark mode: the values are also in the URL itself, so this script
    adds no exposure. Server-stored bookmark mode (?_state_id_=...): the URL
    hides the values, but this script re-exposes them in the page source.
    Anything that can read the HTML — browser extensions, logging proxies,
    screen captures, "View Source" — can read these values. Apps must not
    put credentials, tokens, PII, or other sensitive data into inputs that
    participate in bookmarking.
    """
    ctx = get_current_restore_context()
    if ctx is None:
        return None
    values = _read_restore_input_values(ctx)
    if not values:
        return None
    safe_json = json.dumps(values).replace("</", "<\\/")
    return head_content(tags.script(HTML(
        "window.shinyreact = window.shinyreact || {};"
        f"window.shinyreact._restore = JSON.parse('{safe_json}');"
    )))
```

`_read_restore_input_values(ctx)` is a small wrapper that reads the
underlying input map from `RestoreContext` without calling `restore_input()`.
The exact attribute access (current candidate: `ctx.input._values`) is
verified during implementation.

### Wiring

```python
def page_react(*args, title=None, lang="en"):
    return page_bare(
        _restore_script_tag(),  # head_content; <head>; non-defer
        _dep(),                 # bundle: defer; runs after parsing
        tags.div(id="root"),
        *args,
        title=title,
        lang=lang,
    )
```

```python
def _react_page_fn(*args):
    deps: list[HTMLDependency] = []
    for arg in args:
        if isinstance(arg, Renderer):
            ui = arg.auto_output_ui()
            if isinstance(ui, (Tag, TagList)):
                deps.extend(ui.get_dependencies())
    return cast(Tag, TagList(
        _restore_script_tag(),
        _dep(),
        *deps,
        HTML(index_html),
    ))
```

`page_bare` is **unchanged** — the escape hatch carries no automatic
behaviour.

### Order guarantee

Two complementary mechanisms ensure the restore script runs before the
shinyreact bundle:

1. The bundle's `HTMLDependency` is `script={"src": "shinyreact.js", "defer": ""}`,
   so it executes after HTML parsing completes.
2. The restore script is a plain `<script>` (no `defer`) hoisted into
   `<head>` via `head_content()`, so it executes synchronously during HTML
   parsing.

Even if a future change reordered head injection, the defer-vs-non-defer
distinction would keep the invariant. Both expectations are documented at
the call sites.

## Security

Bookmarked input values appear in the rendered HTML page source. The threat
model differs by mode:

- **URL mode.** Values are already in the URL the user navigated to.
  Re-emitting them in the HTML body adds no exposure. Anyone who has the
  URL has the values.
- **Server-stored mode.** The URL contains only an opaque `_state_id_`.
  Re-emitting the values in the HTML re-exposes them in the page source.
  Browser extensions, logging proxies, screen captures, view-source — all
  see the values.

Both modes are equally restorable, but apps using server-stored mode should
not assume the values are private once the page loads. **Sensitive data —
credentials, tokens, PII — must not be placed in inputs that participate in
bookmarking.** The same guidance applies to traditional Shiny apps using
URL bookmarking, but the server-stored mode visibility is a net change for
shinyreact users and warrants explicit documentation.

The security comment is co-located at:

- The script-emission site (`_restore_script_tag()` docstring).
- The batch-apply site (`applyRestoredValues()` in `bookmark.ts`).
- The public README/docs entry on bookmarking once written.

## Testing

### Python unit tests (`pkg-py/tests/test_bookmark_restore.py`)

1. `_restore_script_tag()` returns `None` when there's no active
   `RestoreContext`.
2. Returns `None` when `RestoreContext` exists but the input map is empty.
3. Returns a `head_content` wrapper containing a `<script>` whose body
   parses to the expected `{id: value}` map.
4. JSON escaping: input value contains `"</script>"` literal — rendered
   HTML must not contain the unescaped sequence.
5. Reading does not mark values pending: after `_restore_script_tag()`, a
   server-side `restore_input("foo", "default")` still returns the restored
   value (not "default") and only *then* marks it pending.
6. `page_react()` with active bookmark → rendered HTML has the restore
   script in `<head>` and the shinyreact `_dep()` bundle.
7. `page_react()` without bookmark → no `_restore` script in the rendered
   HTML.
8. `_build_react_page_fn()` (covering `set_react_page`) — same two cases.
9. URL bookmark mode and server-stored mode both produce the same
   script-tag shape — drive both via `RestoreContext.from_query_string`
   against an in-memory state store.

### JS unit tests (`js/src/shiny-react/__tests__/use-shiny-restore.test.tsx`)

1. `ensureShinyReactInitialized()` with `window.shinyreact._restore = {foo: "hello"}`
   seeds the registry entry and replaces `_restore` with `{ _applied: true }`.
2. With no `_restore` set, init runs without error and `_restore` ends up as
   `{ _applied: true }`.
3. Re-running `ensureShinyReactInitialized()` does not re-apply (`_applied`
   guard).
4. `useShinyInput("foo", "default")` mounts after restore-batch — initial
   render returns `"hello"`, not `"default"`.
5. `useSetShinyInput("foo", "default")` — registry entry holds `"hello"`;
   the setter still writes user-provided values normally.
6. `useShinyInputValue("foo")` mounts before any producer — `add(id, value)`
   drains `pendingSubscribers` and the consumer fires with `"hello"`.
7. Namespaced ids: `_restore = {"ns-foo": "hello"}` and
   `useShinyInput("foo", "default", { namespace: "ns" })` — initial value
   is `"hello"`.

### Playwright integration tests (py-shiny `shiny.playwright`)

A real running Shiny app under the existing pytest playwright tree exercises
the full flow. The test app reuses the public example from the next section
where possible to avoid duplicate fixtures.

- **URL mode**:
  - Launch the test app with `enable_bookmarking="url"`.
  - Navigate to `<base>/?_inputs_&txt=%22hello%22&num=42` (URL-encoded
    inputs).
  - Wait for `shiny:initialized`.
  - Assert the React-rendered DOM reflects the restored values (e.g., the
    text input shows "hello", an output bound to `input.txt` shows "HELLO").
- **Server-stored mode**:
  - Launch the test app with `enable_bookmarking="server"`.
  - Navigate to base, set inputs via Playwright, trigger `do_bookmark()`,
    capture the `_state_id_` from the resulting URL.
  - Reload at `<base>/?_state_id_=...`.
  - Assert restored React state — same DOM expectations as URL mode.
- **No bookmark**:
  - Plain navigation to `<base>/`.
  - Assert React renders with default values; assert
    `window.shinyreact._restore` evaluates to `{ _applied: true }` after
    init.

## Public example

`examples/app-py/13-bookmarking/` (next free number after the existing 01–12
directories — verify and bump if a new example lands first):

- `app.py` — uses `shiny.App(..., bookmark_store="url")` (or whatever the
  current Shiny API spelling is) with a small set of inputs (text, number,
  checkbox) wired through `shinyreact.Spec`. Includes a Shiny action button
  whose handler calls `session.do_bookmark()` so the user can produce a
  shareable URL.
- `bookmarking.tsx` (or `bookmarking.js` no-build, depending on the
  example's chosen build style — match the conventions of the surrounding
  `app-py/0X-*` examples) — a React client with `useShinyInput` for each
  input and outputs that echo the values, plus a "Bookmark this state"
  button that triggers the server's `do_bookmark`.
- `package.json` / `tsconfig.json` if the example uses a build step
  (matching existing `app-py` examples).
- `README.md` for the example: open the app, change inputs, click Bookmark,
  copy the URL, paste it in a new tab → React inputs initialise from the
  bookmark.

Only one example is shipped in this PR (the `app.py` pattern). The design
covers both patterns identically; a `ui.tsx` variant can be added later if
the docs need it.

## Files affected

- `pkg-py/src/shinyreact/_page.py` (or new `_bookmark.py`) —
  `_restore_script_tag()`, wiring into `page_react` and `_build_react_page_fn`.
- `js/src/shiny-react/use-shiny.ts` — call site in `ensureShinyReactInitialized()`.
- `js/src/shiny-react/bookmark.ts` (new) — `applyRestoredValues()` helper.
- `js/src/shiny-react/__tests__/use-shiny-restore.test.tsx` (new) — JS tests.
- `pkg-py/tests/test_bookmark_restore.py` (new) — Python unit tests.
- `pkg-py/tests/playwright/test_bookmark_restore.py` (new, path verified
  during implementation) — py-shiny Playwright integration tests.
- `examples/app-py/13-bookmarking/` (new) — public example.
- `pkg-py/src/shinyreact/www/shinyreact.js` and `js/dist/shinyreact.js` —
  rebuilt via `make update-dist`.
- `docs/features.md` — add a Bookmarking row.
- `docs/todos.md` — remove the bookmarking entry once shipped (or leave it
  pointing at any deferred work).

## Non-goals / explicit follow-ups

- **No save-side helper** (`useShinyBookmark()` etc.). Apps trigger
  `session.do_bookmark()` themselves.
- **No custom-value channel** (`RestoreContext.values`). Out of scope for
  the security reasons in §Security and the scope reasons in §Scope.
- **No `ui.tsx` example** in this PR — design covers it; example deferred
  unless docs demand it.
