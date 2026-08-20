"""shinyreact.App: full-document UI support (workaround for py-shiny#2462)."""

from pathlib import Path

import pytest
from htmltools import TagList, div
from shinyreact import App, page_react_html
from starlette.testclient import TestClient


def _write_react_app(tmp_path: Path) -> Path:
    www = tmp_path / "www"
    www.mkdir()
    (www / "index.html").write_text(
        "<!DOCTYPE html><html><head><title>T</title>{{ headContent() }}</head>"
        '<body><script src="ui.js" defer></script></body></html>'
    )
    (www / "ui.js").write_text("// ui entry")
    return www / "index.html"


def _server(input, output, session) -> None:  # pragma: no cover - trivial
    pass


def test_app_serves_full_document(tmp_path: Path) -> None:
    app = App(page_react_html(_write_react_app(tmp_path)), _server)
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    # Single document: the user's, not a wrapper.
    assert r.text.count("<html") == 1
    assert "<title>T</title>" in r.text
    assert "shinyreact.js" in r.text
    assert 'id="shinyreact-config"' in r.text


def test_app_registers_dependency_routes(tmp_path: Path) -> None:
    import re

    app = App(page_react_html(_write_react_app(tmp_path)), _server)
    client = TestClient(app)
    html = client.get("/").text
    match = re.search(r'src="(lib/[^"]*shinyreact[^"]*\.js)"', html)
    assert match is not None, html
    assert client.get("/" + match.group(1)).status_code == 200


def test_app_auto_mounts_document_dir(tmp_path: Path) -> None:
    # The document references ui.js next to it; shinyreact.App mounts the
    # document's directory so it is served without a static_assets= argument.
    app = App(page_react_html(_write_react_app(tmp_path)), _server)
    client = TestClient(app)
    assert client.get("/ui.js").status_code == 200


def test_app_passes_plain_ui_through(tmp_path: Path) -> None:
    # Non-document UIs behave exactly like shiny.App.
    app = App(TagList(div("plain", id="plain-ui")), _server)
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert 'id="plain-ui"' in r.text


def test_app_rejects_bookmark_store_with_document(tmp_path: Path) -> None:
    with pytest.raises(NotImplementedError, match="page_react"):
        App(
            page_react_html(_write_react_app(tmp_path)),
            _server,
            bookmark_store="url",
        )
