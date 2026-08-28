"""Fixture app whose server claims a protocol major the client cannot speak.

Rewriting the constant `_bookmark.py` reads is the only way to produce a
mismatched `#shinyreact-config` tag from a current server — the two versions
are pinned equal by a parity test. The client should paint the handshake
failure onto the page instead of just leaving it blank (#213).
"""

import shinyreact._bookmark as _bookmark
from shiny.express import render  # noqa: F401
from shinyreact import set_react_page

# Expected on screen: a red banner across the top naming both protocol
# versions (999.0 server, whatever the client speaks) and telling the reader
# to upgrade the older side. The app body itself never renders.
_bookmark.PROTOCOL_VERSION = "999.0"

set_react_page()
