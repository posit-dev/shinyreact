# The wire-protocol version this server speaks.
#
# Rendered into every page via the `#shinyreact-config` JSON script tag (see
# bookmark.R); the JS client asserts the major versions match at boot. The
# protocol covers every shape that crosses the client/server boundary;
# protocol/surface.json enumerates them and a test in each language enforces
# it. Only changes an existing peer would misinterpret bump this version —
# additive shapes do not (see protocol/README.md) — so client and server
# package releases do not need to be in lockstep.
#
# Decided in decisions/2026-08-17-js-distribution.md. Mirrors
# `PROTOCOL_VERSION` in pkg-js/src/shiny-react/config.ts and
# pkg-py/src/shinyreact/_protocol.py; a parity test in each language asserts
# all three match.

#' @keywords internal
.protocol_version <- "1.0"
