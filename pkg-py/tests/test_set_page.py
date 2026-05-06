from pathlib import Path

from shiny.express._run import ExpressStubSession, run_express
from shiny.session._session import session_context


def test_page_injects_shinyreact_dep(tmp_path: Path) -> None:
    """set_page() includes the shinyreact HTMLDependency."""
    www = tmp_path / "www"
    www.mkdir()
    (www / "index.html").write_text("<div id='root'></div>")

    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from shiny.express import input\n"
        "from shinyreact import set_page, reactive_output\n"
        "set_page()\n"
        "@reactive_output\n"
        "def greeting(): return 'hi'\n"
    )

    stub = ExpressStubSession()
    with session_context(stub):
        ui = run_express(app_file, "test_pkg")

    tagified = ui.tagify()
    rendered = tagified.render()
    dep_names = [d.name for d in rendered["dependencies"]]
    assert "shinyreact" in dep_names


def test_page_discovers_renderer_deps(tmp_path: Path) -> None:
    """set_page() auto-discovers deps from traditional renderers."""
    www = tmp_path / "www"
    www.mkdir()
    (www / "index.html").write_text("<div id='root'></div>")

    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from shiny.express import input, render\n"
        "from shinyreact import set_page, reactive_output\n"
        "set_page()\n"
        "@reactive_output\n"
        "def greeting(): return 'hi'\n"
        "@render.data_frame\n"
        "def my_table(): return None\n"
    )

    stub = ExpressStubSession()
    with session_context(stub):
        ui = run_express(app_file, "test_pkg2")

    tagified = ui.tagify()
    rendered = tagified.render()
    dep_names = [d.name for d in rendered["dependencies"]]
    assert "shiny-data-frame-output" in dep_names


def test_page_reads_index_html(tmp_path: Path) -> None:
    """set_page() reads www/index.html and includes it in the page body."""
    www = tmp_path / "www"
    www.mkdir()
    marker = "<!-- test-marker -->"
    (www / "index.html").write_text(f"{marker}<div id='root'></div>")

    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from shiny.express import input\n"
        "from shinyreact import set_page, reactive_output\n"
        "set_page()\n"
        "@reactive_output\n"
        "def greeting(): return 'hi'\n"
    )

    stub = ExpressStubSession()
    with session_context(stub):
        ui = run_express(app_file, "test_pkg3")

    tagified = ui.tagify()
    rendered = tagified.render()
    assert marker in rendered["html"]


def test_page_custom_path(tmp_path: Path) -> None:
    """set_page() accepts a custom HTML file path."""
    (tmp_path / "custom.html").write_text("<div id='app'></div>")

    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from shiny.express import input\n"
        "from shinyreact import set_page, reactive_output\n"
        "set_page('custom.html')\n"
        "@reactive_output\n"
        "def greeting(): return 'hi'\n"
    )

    stub = ExpressStubSession()
    with session_context(stub):
        ui = run_express(app_file, "test_pkg4")

    tagified = ui.tagify()
    rendered = tagified.render()
    assert "<div id='app'></div>" in rendered["html"]
