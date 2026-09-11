"""Pins this example's distinctive `(test)` leaf: the page ships no shinyreact JS.

The client runtime lives entirely in `www/ui.js`, bundled from
`@posit-dev/shinyreact`. So the page must carry this app's dependency and
*only* this app's — no `shinyreact.js`, and no `#shinyreact-config` tag, which
`page_bare()` is alone in never emitting.

Mirrored in `tests/testthat/test-page.R` for `app.R`. Like that file, it
rebuilds `app.py`'s two-line ui against an empty asset directory rather than
importing the app: the claim is about how the page is composed, not about what
`www/` holds, and importing `app.py` would trigger its build-on-first-run.

Run it from the app directory, the way a user of the app would::

    pytest
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shinyreact import page_bare, page_react_dep


@pytest.fixture
def ui(tmp_path: Path):
    # page_react_dep() requires the directory to exist, and only warns about
    # the missing ui.js inside it.
    (tmp_path / "www").mkdir()
    with pytest.warns(UserWarning, match="JS entry point not found"):
        return page_bare(
            page_react_dep(src_dir=tmp_path / "www", name="npm-local"),
            title="Old Faithful",
        )


def test_the_page_carries_only_this_apps_dependency(ui):
    names = {dep.name for dep in ui.get_dependencies()}
    assert "npm-local" in names
    assert "shinyreact" not in names


def test_the_page_has_no_config_tag(ui):
    assert "shinyreact-config" not in str(ui)
