"""shinyreact.ReactApp: discovered UI + full documents via ui.PageDocument."""

import re
from pathlib import Path

from htmltools import TagList, div
from shinyreact import ReactApp, page_react_html
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


def _write_react_assets(tmp_path: Path) -> Path:
    # page_react()-style app: conventional assets, no index.html.
    www = tmp_path / "www"
    www.mkdir()
    (www / "ui.js").write_text("// ui entry")
    return www


def _server(input, output, session) -> None:  # pragma: no cover - trivial
    pass


def _make_app_from_cwd(tmp_path, monkeypatch, **kwargs) -> ReactApp:
    """Construct ReactApp(server) as an app whose dir is tmp_path.

    Discovery reads the calling frame's __file__; exec'd code has none, so it
    falls back to CWD — the same convention page_react() tests use.
    """
    monkeypatch.chdir(tmp_path)
    captured: dict[str, ReactApp] = {}
    src = (
        "from shinyreact import ReactApp\n"
        "captured['app'] = ReactApp(server, **kwargs)\n"
    )
    exec(
        compile(src, "<test>", "exec"),
        {"captured": captured, "server": _server, "kwargs": kwargs},
    )
    return captured["app"]


def test_app_serves_full_document(tmp_path: Path) -> None:
    app = ReactApp(_server, ui=page_react_html(_write_react_app(tmp_path)))
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    # Single document: the user's, not a wrapper.
    assert r.text.count("<html") == 1
    assert "<title>T</title>" in r.text
    assert "shinyreact.js" in r.text
    assert 'id="shinyreact-config"' in r.text


def test_app_registers_dependency_routes(tmp_path: Path) -> None:
    app = ReactApp(_server, ui=page_react_html(_write_react_app(tmp_path)))
    client = TestClient(app)
    html = client.get("/").text
    match = re.search(r'src="(lib/[^"]*shinyreact[^"]*\.js)"', html)
    assert match is not None, html
    assert client.get("/" + match.group(1)).status_code == 200


def test_app_auto_mounts_document_dir(tmp_path: Path) -> None:
    # The document references ui.js next to it; ReactApp mounts the
    # document's directory so it is served without a static_assets= argument.
    app = ReactApp(_server, ui=page_react_html(_write_react_app(tmp_path)))
    client = TestClient(app)
    assert client.get("/ui.js").status_code == 200


def test_app_passes_plain_ui_through(tmp_path: Path) -> None:
    # Non-document UIs behave exactly like shiny.App.
    app = ReactApp(_server, ui=TagList(div("plain", id="plain-ui")))
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert 'id="plain-ui"' in r.text


def test_app_discovers_index_html(tmp_path: Path, monkeypatch) -> None:
    # ReactApp(server) with www/index.html present: page_react_html mode,
    # document served as-is and its sibling assets auto-mounted.
    _write_react_app(tmp_path)
    app = _make_app_from_cwd(tmp_path, monkeypatch)
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.text.count("<html") == 1
    assert "<title>T</title>" in r.text
    assert 'id="shinyreact-config"' in r.text
    assert client.get("/ui.js").status_code == 200


def test_app_discovers_ui_js(tmp_path: Path, monkeypatch) -> None:
    # ReactApp(server) with only www/ui.js: page_react mode — the dependency
    # serves the assets, no static mount involved.
    _write_react_assets(tmp_path)
    app = _make_app_from_cwd(tmp_path, monkeypatch)
    client = TestClient(app)
    html = client.get("/").text
    match = re.search(r'src="(lib/[^"]*/ui\.js)"', html)
    assert match is not None, html
    assert client.get("/" + match.group(1)).status_code == 200
    # Title defaults to the app folder name (page_react convention).
    assert f"<title>{tmp_path.name}</title>" in html


def test_app_discovered_ui_supports_bookmarking(tmp_path: Path, monkeypatch) -> None:
    # The discovered UI is a function of the request, so a bookmark query
    # string renders the restore payload with zero extra wiring.
    _write_react_assets(tmp_path)
    app = _make_app_from_cwd(tmp_path, monkeypatch, bookmark_store="url")
    client = TestClient(app)
    r = client.get('/?_inputs_&txt="hi"')
    assert r.status_code == 200
    match = re.search(
        r'id="shinyreact-config">([^<]*)</script>',
        r.text,
    )
    assert match is not None, r.text
    assert '"restore"' in match.group(1)
    assert '"hi"' in match.group(1)


def test_app_bookmark_store_works_with_ui_function(tmp_path: Path) -> None:
    # An explicit per-request UI function still works (py-shiny#2475 renders
    # it through the same path).
    index = _write_react_app(tmp_path)
    app = ReactApp(
        _server,
        ui=lambda request: page_react_html(index),
        bookmark_store="url",
        static_assets={"/": index.parent},
    )
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.text.count("<html") == 1
    assert 'id="shinyreact-config"' in r.text
