import re

import pytest
from htmltools import HTMLDependency, Tag
from shinyreact._page import page_bare


def test_page_bare_returns_tag():
    result = page_bare()
    assert isinstance(result, Tag)


def test_page_bare_with_title():
    result = page_bare(title="Test Page")
    rendered = str(result.tagify())
    assert "Test Page" in rendered


def test_page_bare_title_emitted_once():
    """Only `page_bootstrap()` emits <title> — no duplicate element (issue #186)."""
    rendered = str(page_bare(title="My Title").tagify())
    assert re.findall(r"<title>.*?</title>", rendered) == ["<title>My Title</title>"]


def test_page_bare_no_shinyreact_dep():
    result = page_bare()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyreact" not in dep_names


def test_page_react_dep_falls_back_to_cwd_without_file(tmp_path, monkeypatch):
    """page_react_dep() falls back to CWD when the caller has no __file__."""
    (tmp_path / "ui.js").write_text("// ...")
    monkeypatch.chdir(tmp_path)

    captured: dict[str, HTMLDependency] = {}
    src = (
        "from shinyreact._page import page_react_dep\n"
        "captured['dep'] = page_react_dep()\n"
    )
    exec(compile(src, "<test>", "exec"), {"captured": captured})

    dep = captured["dep"]
    assert isinstance(dep, HTMLDependency)
    # Source resolved to CWD, so dep_name is the CWD's basename.
    assert dep.name == tmp_path.name


def test_page_react_html_attaches_dep(tmp_path):
    from shinyreact import page_react_html

    index = tmp_path / "index.html"
    index.write_text('<div id="root"></div>')
    ui = page_react_html(index)
    deps = ui.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyreact" in dep_names


def test_page_react_html_includes_file_html(tmp_path):
    from shinyreact import page_react_html

    index = tmp_path / "index.html"
    index.write_text('<div id="root"></div>')
    ui = page_react_html(index)
    rendered = str(ui.tagify())
    assert 'id="root"' in rendered  # the user's own mount, from their file


def test_page_react_html_missing_file_raises(tmp_path):
    from shinyreact import page_react_html

    with pytest.raises(FileNotFoundError, match="not found"):
        page_react_html(tmp_path / "nope.html")


def test_page_react_html_falls_back_to_cwd_without_file(tmp_path, monkeypatch):
    """page_react_html() falls back to CWD when the caller has no __file__."""
    www = tmp_path / "www"
    www.mkdir()
    (www / "index.html").write_text('<div id="root"></div>')
    monkeypatch.chdir(tmp_path)

    captured: dict[str, object] = {}
    src = (
        "from shinyreact import page_react_html\n"
        "captured['ui'] = page_react_html()\n"  # relative default resolves to CWD
    )
    exec(compile(src, "<test>", "exec"), {"captured": captured})

    rendered = str(captured["ui"].tagify())
    assert 'id="root"' in rendered


def _make_react_app(tmp_path, name="myapp", css=True):
    """An app folder with the page_react() conventional assets."""
    www = tmp_path / name / "www"
    www.mkdir(parents=True)
    (www / "ui.js").write_text("// ui entry")
    if css:
        (www / "ui.css").write_text("body {}")
    return tmp_path / name


def _dep_tags_html(ui) -> str:
    rendered = ui.tagify().render()
    return (
        "".join(d.as_html_tags().get_html_string() for d in rendered["dependencies"])
        + rendered["html"]
    )


def test_page_react_attaches_bundle_app_dep_and_config(tmp_path):
    from shinyreact import page_react

    app_dir = _make_react_app(tmp_path)
    ui = page_react(src_dir=app_dir / "www")
    names = [d.name for d in ui.get_dependencies()]
    assert "shinyreact" in names
    assert "myapp" in names
    html = _dep_tags_html(ui)
    assert "ui.js" in html
    assert "ui.css" in html
    assert 'id="shinyreact-config"' in html


def test_page_react_title_defaults_to_app_folder_name(tmp_path):
    from shinyreact import page_react

    app_dir = _make_react_app(tmp_path)
    rendered = str(page_react(src_dir=app_dir / "www").tagify())
    assert re.findall(r"<title>.*?</title>", rendered) == ["<title>myapp</title>"]


def test_page_react_title_override(tmp_path):
    from shinyreact import page_react

    app_dir = _make_react_app(tmp_path)
    rendered = str(page_react(src_dir=app_dir / "www", title="Custom").tagify())
    assert re.findall(r"<title>.*?</title>", rendered) == ["<title>Custom</title>"]


def test_page_react_skips_missing_css(tmp_path):
    from shinyreact import page_react

    app_dir = _make_react_app(tmp_path, css=False)
    html = _dep_tags_html(page_react(src_dir=app_dir / "www"))
    assert "ui.js" in html
    assert "ui.css" not in html


def test_page_react_warns_on_missing_js(tmp_path):
    from shinyreact import page_react

    app_dir = tmp_path / "empty-app"
    (app_dir / "www").mkdir(parents=True)
    with pytest.warns(UserWarning, match="ui.js"):
        page_react(src_dir=app_dir / "www")


def test_page_react_includes_extra_dependencies(tmp_path):
    from shinyreact import page_react

    app_dir = _make_react_app(tmp_path)
    extra = HTMLDependency(
        name="extra-dep",
        version="1.0",
        source={"href": "/x"},
        script={"src": "x.js"},
    )
    ui = page_react(extra, src_dir=app_dir / "www")
    names = [d.name for d in ui.get_dependencies()]
    assert "extra-dep" in names


def test_page_react_defaults_resolve_against_cwd_without_caller_file(
    tmp_path, monkeypatch
):
    """With no src_dir and no caller __file__, www/ resolves against CWD."""
    app_dir = _make_react_app(tmp_path, name="cwd-app")
    monkeypatch.chdir(app_dir)

    captured: dict[str, Tag] = {}
    src = "from shinyreact import page_react\ncaptured['ui'] = page_react()\n"
    exec(compile(src, "<test>", "exec"), {"captured": captured})

    ui = captured["ui"]
    names = [d.name for d in ui.get_dependencies()]
    assert "cwd-app" in names
    rendered = str(ui.tagify())
    assert "<title>cwd-app</title>" in rendered
