from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from htmltools import Tag
from shiny import render
from shinyreact import reactive_output, set_react_page
from shinyreact._page import _build_react_page_fn


def _render(page_fn: Callable[..., Tag], *args: Any) -> dict[str, Any]:
    return page_fn(*args).tagify().render()


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
    """index.html is read at construction time, not per page render."""
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
