"""The wire-protocol version this server speaks.

Rendered into every page via the ``#shinyreact-config`` JSON script tag
(see ``_bookmark.py``); the JS client asserts the major versions match at
boot. The protocol covers the shapes that cross the client/server boundary —
the ``#shinyreact-config`` payload itself, the ``shinyReactMessage`` custom
message, and the ``shinyreact.default`` / ``shinyreact.asis`` input-handler
contract — and only bumps when one of those changes, so client and server
package releases do not need to be in lockstep.

Decided in ``decisions/2026-08-17-js-distribution.md``. Mirrors
``PROTOCOL_VERSION`` in ``pkg-js/src/shiny-react/config.ts`` and
``pkg-r/R/protocol.R``; a parity test in each language asserts all three
match.
"""

PROTOCOL_VERSION = "1.0"
