from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

import pytest
from htmltools import Tag
from shiny import render
from shinyreact import reactive_output, set_react_page
from shinyreact._page import _build_react_page_fn, _build_react_page_fn_discovered


def _render(page_fn: Callable[..., Tag], *args: Any) -> dict[str, Any]:
    return page_fn(*args).tagify().render()


def _render_with(page_fn: Callable[..., Tag], **kwargs: Any) -> dict[str, Any]:
    """Render a page_fn the way page_auto() calls it: options as kwargs."""
    return page_fn(**kwargs).tagify().render()


def test_build_page_fn_injects_shinyreact_dep(tmp_path: Path) -> None:
    """The page_fn always emits the shinyreact HTMLDependency."""
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")

    rendered = _render(_build_react_page_fn(index))
    dep_names = [d.name for d in rendered["dependencies"]]
    assert "shinyreact" in dep_names


def test_build_page_fn_discovers_renderer_deps(tmp_path: Path) -> None:
    """Deps from traditional Shiny renderers are auto-discovered."""
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")

    @render.data_frame
    def my_table() -> None:
        return None

    rendered = _render(_build_react_page_fn(index), my_table)
    dep_names = [d.name for d in rendered["dependencies"]]
    assert "shiny-data-frame-output" in dep_names


def test_build_page_fn_skips_non_renderer_args(tmp_path: Path) -> None:
    """Non-Renderer args (and renderers whose UI is not a Tag/TagList) are ignored."""
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")

    @reactive_output
    def greeting() -> str:
        return "hi"

    rendered = _render(_build_react_page_fn(index), greeting, "not a renderer", 42)
    assert "shinyreact" in [d.name for d in rendered["dependencies"]]


def test_build_page_fn_reads_index_html(tmp_path: Path) -> None:
    """The contents of index.html are inlined into the page body."""
    marker = "<!-- test-marker -->"
    index = tmp_path / "index.html"
    index.write_text(f"{marker}<div id='root'></div>")

    rendered = _render(_build_react_page_fn(index))
    assert marker in rendered["html"]


def test_build_page_fn_reads_index_html_once(tmp_path: Path) -> None:
    """index.html is read at construction time, not per page render.

    See issue #82 — re-reading from inside the page_fn closure would not
    actually help, because Shiny Express only invokes this closure once at
    app startup. The fix requires upstream Shiny support.
    """
    index = tmp_path / "index.html"
    index.write_text("<div>original</div>")

    page_fn = _build_react_page_fn(index)
    index.write_text("<div>changed</div>")

    rendered = _render(page_fn)
    assert "original" in rendered["html"]
    assert "changed" not in rendered["html"]


def test_set_react_page_resolves_path_relative_to_caller(tmp_path: Path) -> None:
    """set_react_page() resolves a relative path against the caller's directory."""
    www = tmp_path / "www"
    www.mkdir()
    marker = "<!-- caller-resolution -->"
    (www / "index.html").write_text(f"{marker}<div id='root'></div>")

    app_file = tmp_path / "app.py"
    app_file.write_text("from shinyreact import set_react_page\nset_react_page()\n")

    captured: dict[str, Callable[..., Tag]] = {}

    def fake_page_opts(*, page_fn: Callable[..., Tag], **_: Any) -> None:
        captured["page_fn"] = page_fn

    with patch("shinyreact._page.page_opts", fake_page_opts):
        exec(
            compile(app_file.read_text(), str(app_file), "exec"),
            {"__file__": str(app_file)},
        )

    rendered = _render(captured["page_fn"])
    assert marker in rendered["html"]


def test_set_react_page_accepts_path_object(tmp_path: Path) -> None:
    """set_react_page() accepts a pathlib.Path as well as a str."""
    (tmp_path / "custom.html").write_text("<div id='custom'></div>")

    captured: dict[str, Callable[..., Tag]] = {}

    def fake_page_opts(*, page_fn: Callable[..., Tag], **_: Any) -> None:
        captured["page_fn"] = page_fn

    with patch("shinyreact._page.page_opts", fake_page_opts):
        set_react_page(tmp_path / "custom.html")

    rendered = _render(captured["page_fn"])
    assert "<div id='custom'></div>" in rendered["html"]


def test_set_react_page_custom_relative_path(tmp_path: Path) -> None:
    """A custom relative path is resolved against the caller's directory."""
    (tmp_path / "custom.html").write_text("<div id='app'></div>")

    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from shinyreact import set_react_page\nset_react_page('custom.html')\n"
    )

    captured: dict[str, Callable[..., Tag]] = {}

    def fake_page_opts(*, page_fn: Callable[..., Tag], **_: Any) -> None:
        captured["page_fn"] = page_fn

    with patch("shinyreact._page.page_opts", fake_page_opts):
        exec(
            compile(app_file.read_text(), str(app_file), "exec"),
            {"__file__": str(app_file)},
        )

    rendered = _render(captured["page_fn"])
    assert "<div id='app'></div>" in rendered["html"]


def test_set_react_page_falls_back_to_cwd_when_caller_has_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative path with no caller __file__ resolves against the CWD."""
    (tmp_path / "cwd.html").write_text("<div id='cwd'></div>")
    monkeypatch.chdir(tmp_path)

    captured: dict[str, Callable[..., Tag]] = {}

    def fake_page_opts(*, page_fn: Callable[..., Tag], **_: Any) -> None:
        captured["page_fn"] = page_fn

    with patch("shinyreact._page.page_opts", fake_page_opts):
        # Caller frame has no __file__ — relative path resolves against CWD.
        exec(
            compile(
                "from shinyreact import set_react_page\nset_react_page('cwd.html')\n",
                "<test>",
                "exec",
            ),
            {},
        )

    rendered = _render(captured["page_fn"])
    assert "<div id='cwd'></div>" in rendered["html"]


def test_set_react_page_absolute_path_works_without_caller_file(tmp_path: Path) -> None:
    """An absolute path bypasses caller-dir resolution and works without __file__."""
    (tmp_path / "abs.html").write_text("<div id='abs'></div>")

    captured: dict[str, Callable[..., Tag]] = {}

    def fake_page_opts(*, page_fn: Callable[..., Tag], **_: Any) -> None:
        captured["page_fn"] = page_fn

    with patch("shinyreact._page.page_opts", fake_page_opts):
        # Caller frame has no __file__ — but absolute path doesn't need it.
        exec(
            compile(
                f"from shinyreact import set_react_page\n"
                f"set_react_page(r'{tmp_path / 'abs.html'}')\n",
                "<test>",
                "exec",
            ),
            {},
        )

    rendered = _render(captured["page_fn"])
    assert "<div id='abs'></div>" in rendered["html"]


def test_build_page_fn_discovered_serves_conventional_assets(tmp_path: Path) -> None:
    """The no-index.html mode serves www/ui.js + ui.css with the app-dir title."""
    from shinyreact._page import _build_react_page_fn_discovered

    www = tmp_path / "www"
    www.mkdir()
    (www / "ui.js").write_text("// entry")
    (www / "ui.css").write_text("body {}")

    rendered = _render(_build_react_page_fn_discovered(tmp_path))
    deps_html = "".join(
        d.as_html_tags().get_html_string() for d in rendered["dependencies"]
    )
    dep_names = [d.name for d in rendered["dependencies"]]
    assert "shinyreact" in dep_names
    assert tmp_path.name in dep_names
    assert "ui.js" in deps_html
    assert "ui.css" in deps_html
    assert f"<title>{tmp_path.name}</title>" in rendered["html"]


def test_set_react_page_none_prefers_index_html(tmp_path: Path) -> None:
    """With no path, www/index.html wins over ui.js discovery when present."""
    www = tmp_path / "www"
    www.mkdir()
    (www / "index.html").write_text("<div id='from-index'></div>")
    (www / "ui.js").write_text("// entry")

    app_file = tmp_path / "app.py"
    app_file.write_text("from shinyreact import set_react_page\nset_react_page()\n")

    captured: dict[str, Callable[..., Tag]] = {}

    def fake_page_opts(*, page_fn: Callable[..., Tag], **_: Any) -> None:
        captured["page_fn"] = page_fn

    with patch("shinyreact._page.page_opts", fake_page_opts):
        exec(
            compile(app_file.read_text(), str(app_file), "exec"),
            {"__file__": str(app_file)},
        )

    rendered = _render(captured["page_fn"])
    assert "from-index" in rendered["html"]


def test_set_react_page_none_falls_back_to_discovery(tmp_path: Path) -> None:
    """With no path and no www/index.html, ui.js discovery kicks in."""
    www = tmp_path / "www"
    www.mkdir()
    (www / "ui.js").write_text("// entry")

    app_file = tmp_path / "app.py"
    app_file.write_text("from shinyreact import set_react_page\nset_react_page()\n")

    captured: dict[str, Callable[..., Tag]] = {}

    def fake_page_opts(*, page_fn: Callable[..., Tag], **_: Any) -> None:
        captured["page_fn"] = page_fn

    with patch("shinyreact._page.page_opts", fake_page_opts):
        exec(
            compile(app_file.read_text(), str(app_file), "exec"),
            {"__file__": str(app_file)},
        )

    rendered = _render(captured["page_fn"])
    dep_names = [d.name for d in rendered["dependencies"]]
    assert tmp_path.name in dep_names
    assert f"<title>{tmp_path.name}</title>" in rendered["html"]


def test_set_react_page_explicit_missing_path_raises(tmp_path: Path) -> None:
    # An explicitly passed path must exist. `test_set_react_page.py` had no
    # pytest.raises at all, so nothing pinned this branch.
    missing = tmp_path / "nope.html"
    with pytest.raises(FileNotFoundError, match=str(missing)):
        _build_react_page_fn(missing)


def test_page_opts_title_reaches_the_discovered_page(tmp_path: Path) -> None:
    # page_opts() records its arguments and page_auto() splats them into the
    # resolved page_fn — ours. Taking only *args meant `page_opts(title=...)`
    # plus `set_react_page()` died at app startup with
    # "unexpected keyword argument 'title'" from inside a private local.
    www = tmp_path / "www"
    www.mkdir()
    (www / "ui.js").write_text("// ui")

    page_fn = _build_react_page_fn_discovered(tmp_path)
    rendered = _render_with(page_fn, title="My React App")
    assert "<title>My React App</title>" in rendered["html"]


def test_page_opts_title_defaults_to_the_app_folder(tmp_path: Path) -> None:
    # No page_opts(title=) → the folder name, as before.
    www = tmp_path / "www"
    www.mkdir()
    (www / "ui.js").write_text("// ui")

    rendered = _render_with(_build_react_page_fn_discovered(tmp_path))
    assert f"<title>{tmp_path.name}</title>" in rendered["html"]


def test_page_opts_lang_reaches_the_discovered_page(tmp_path: Path) -> None:
    www = tmp_path / "www"
    www.mkdir()
    (www / "ui.js").write_text("// ui")

    rendered = _render_with(_build_react_page_fn_discovered(tmp_path), lang="fr")
    assert 'lang="fr"' in rendered["html"]


def test_unsupported_page_opts_names_itself(tmp_path: Path) -> None:
    # A bare React page has no Bootstrap layout, so `fillable` cannot be
    # honored. Say so, rather than raising from inside a private local.
    www = tmp_path / "www"
    www.mkdir()
    (www / "ui.js").write_text("// ui")

    page_fn = _build_react_page_fn_discovered(tmp_path)
    with pytest.raises(TypeError, match=r"page_opts\(fillable=\.\.\.\)"):
        page_fn(fillable=True)


def test_page_opts_rejected_in_html_file_mode(tmp_path: Path) -> None:
    # The HTML-file mode emits no page tag of its own, so there is nothing for
    # title/lang/theme to land on.
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")

    page_fn = _build_react_page_fn(index)
    with pytest.raises(TypeError, match="HTML-file mode"):
        page_fn(title="nope")
