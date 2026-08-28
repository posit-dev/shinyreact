# The shinyreact wire protocol

**Protocol version: `1.0`**

This document is the versioned contract between a shinyreact server (the
Python or R package) and a shinyreact client (the IIFE bundle or the
`@posit/shinyreact` npm package). Its version — not any package version — is
what the client asserts at boot, so client and server packages can release
independently as long as they speak the same protocol major version. Decided
in `decisions/2026-08-17-js-distribution.md`.

The version is declared in three places, pinned equal by a parity test in
each language:

- `pkg-js/src/shiny-react/config.ts` — `PROTOCOL_VERSION`
- `pkg-py/src/shinyreact/_protocol.py` — `PROTOCOL_VERSION`
- `pkg-r/R/protocol.R` — `.protocol_version`

## Versioning policy

- **Major bump** — any change an existing peer would misinterpret: renaming
  or restructuring a payload member, changing a member's type, changing
  escaping rules, removing a message.
- **Additive, ignorable changes do not bump** — a new optional payload
  member, a new message type, a new input-handler name. A client or server
  must tolerate unknown members and unknown message types from a same-major
  peer, so neither side can act on the minor anyway: nothing reads it, and no
  peer changes behavior when it moves. The record of what is on the wire is
  [`surface.json`](surface.json), which is enforced; the minor is not.
  (Bumping it for a notable addition is allowed, never required.)
- The client's handshake accepts any same-major server version and throws on
  a major mismatch, naming both versions (see
  `assertProtocolCompatible()`).

Shared fixtures live in [`fixtures/`](fixtures/); each language has a test
that round-trips them through its emit/parse path (grep for the fixture
filename to find them).

### The surface manifest

[`surface.json`](surface.json) enumerates the whole boundary — custom message
types, input-handler names, input ids, DOM ids — beside the protocol version.
All three suites assert their live surface against it (`test_protocol_surface.py`,
`test-protocol-surface.R`, `protocol-surface.test.ts`): the JS suite scans
`pkg-js/src`, and the Python and R suites read shiny's input-handler registry
after loading the package. A new message type or handler name therefore fails a
test until it is listed, next to the version, where the bump question above is
impossible to miss.

This exists because the surface grew unnoticed: #221 added the
`shinyreact.init` handler (with its `.shinyreact_init` ping) and the
`shinyreact-deps` message while the version stayed at `1.0`. Those additions
stand at `1.0` — they are additive and ignorable, which per the policy above
is not a bump — and the manifest, not the version, is now what records them
([#232](https://github.com/posit-dev/shinyreact/issues/232)).

## 1. The `#shinyreact-config` script tag

Every page entry point renders, in `<head>`:

```html
<script type="application/json" id="shinyreact-config">{"protocolVersion": "1.0", "restore": {...}}</script>
```

| Member | Type | Presence | Meaning |
|---|---|---|---|
| `protocolVersion` | string, `MAJOR.MINOR` | always | The protocol version the server speaks |
| `restore` | object: input id → JSON value | only while restoring a bookmark | Bookmark-restored input values, seeded into `useShinyInput` before first render |

Encoding rules (both server languages):

- The payload is plain JSON — it is *data*, never parsed as JavaScript.
- Every `<` **must** be emitted as the JSON escape `\u003c`, so the payload
  can never contain `</script` (which would terminate the tag) or `<!--`.
  No other escaping is required; U+2028/U+2029 may appear raw.
- Restore keys with names like `__proto__` are ordinary members; the client
  reads the payload with `JSON.parse`, which treats them as own properties.

The client reads the tag via `document.getElementById("shinyreact-config")`.
A missing tag means "no shinyreact server rendered this page" (tolerated by
the IIFE bundle, which ships inside the server package and cannot skew).
This tag replaced the pre-1.0 inline script that assigned
`window.shinyreact._restore`; that global is no longer read.

## 2. The `shinyReactMessage` custom message

Server → client, over Shiny's custom-message channel:

```jsonc
// session.send_custom_message("shinyReactMessage", ...)
{ "id": "<resolved-id>", "data": <any JSON value> }
```

| Member | Type | Meaning |
|---|---|---|
| `id` | string | The message id, namespaced by the server's module context (`resolve_id`) — every module-resolved string in this protocol (input, output, message) is an `id` |
| `data` | any JSON | Delivered as-is to `useShinyMessageHandler(id, handler)` |

## 3. Input-handler suffixes

Untyped `useShinyInput` values are sent with the wire id suffix
`:shinyreact.default`; opting into pass-through uses `:shinyreact.asis`.
Both handlers are registered by the Python and R packages. The
`shinyreact.default` contract (deliberate R flattening divergence included)
is specified in `CLAUDE.md` ("The `shinyreact.default` input handler") and
`decisions/2026-08-13-r-python-parity.md`.

A `type` option on the hook replaces the suffix with `:<type>`; the handler
name is then a server-side contract owned by whoever registered it.

## 4. Handshake semantics

At first hook mount the client reads the config tag and compares major
versions:

- same major → proceed (minor differences are additive by policy above);
- different major → throw, naming both versions and which side to upgrade;
- tag absent → the IIFE bundle proceeds (it cannot skew); the
  `@posit/shinyreact` npm build treats absence as an error, since an
  independently-installed client meeting a tag-less page means the server
  predates the protocol.
