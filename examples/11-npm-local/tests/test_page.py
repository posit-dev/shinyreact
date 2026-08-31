"""Pins this example's distinctive `(test)` leaf: the page ships no shinyreact JS.

The client runtime lives entirely in `www/ui.js`, bundled from the
`@posit/shinyreact` copy inside the installed shinyreact package. So the page
must carry this app's dependency and *only* this app's — no `shinyreact.js`,
and no `#shinyreact-config` tag (nothing on the page needs a protocol
handshake when one install owns both halves).

Mirrored in `tests/testthat/test-page.R` for `app.R`.

Run it from the app directory, the way a user of the app would::

    pytest
"""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from app import ui  # noqa: E402


def test_the_page_carries_only_this_apps_dependency():
    names = {dep.name for dep in ui.get_dependencies()}
    assert "npm-local" in names
    assert "shinyreact" not in names


def test_the_page_has_no_config_tag():
    assert "shinyreact-config" not in str(ui)
