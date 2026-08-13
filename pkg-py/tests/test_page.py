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
    (tmp_path / "main.js").write_text("// ...")
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
