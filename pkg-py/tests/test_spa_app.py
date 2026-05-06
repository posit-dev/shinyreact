from pathlib import Path

import shinyreact
from shiny import App


def test_spa_app_subclasses_shiny_app(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<html><body><div id='root'></div></body></html>"
    )

    def server(input, output, session):  # noqa: ARG001
        return None

    app = shinyreact.SpaApp(server, static_dir=tmp_path)
    assert isinstance(app, App)


def test_spa_app_reads_index_html(tmp_path: Path) -> None:
    marker = "<!-- spa-app-test-marker -->"
    (tmp_path / "index.html").write_text(
        f"<html><body>{marker}<div id='root'></div></body></html>"
    )

    def server(input, output, session):  # noqa: ARG001
        return None

    app = shinyreact.SpaApp(server, static_dir=tmp_path)
    rendered = str(app.ui)
    assert marker in rendered


def test_spa_app_defaults_to_www_next_to_caller(tmp_path: Path) -> None:
    """When static_dir is omitted, SpaApp resolves ./www relative to the caller."""
    www = tmp_path / "www"
    www.mkdir()
    marker = "<!-- spa-app-default-test-marker -->"
    (www / "index.html").write_text(
        f"<html><body>{marker}<div id='root'></div></body></html>"
    )

    # Write a tiny "app file" that constructs SpaApp without static_dir.
    app_file = tmp_path / "app.py"
    app_file.write_text(
        "import shinyreact\n"
        "def server(input, output, session): return None\n"
        "app = shinyreact.SpaApp(server)\n"
    )

    # Execute it as if shiny were running it: the caller frame's __file__
    # must be the app_file path so SpaApp's auto-derive resolves ./www there.
    namespace: dict = {"__file__": str(app_file)}
    exec(compile(app_file.read_text(), str(app_file), "exec"), namespace)

    rendered = str(namespace["app"].ui)
    assert marker in rendered
