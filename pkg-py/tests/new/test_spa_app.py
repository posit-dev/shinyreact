from pathlib import Path

import shinyjson
from shiny import App


def test_spa_app_subclasses_shiny_app(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<html><body><div id='root'></div></body></html>"
    )

    def server(input, output, session):  # noqa: ARG001
        return None

    app = shinyjson.SpaApp(tmp_path, server)
    assert isinstance(app, App)


def test_spa_app_reads_index_html(tmp_path: Path) -> None:
    marker = "<!-- spa-app-test-marker -->"
    (tmp_path / "index.html").write_text(
        f"<html><body>{marker}<div id='root'></div></body></html>"
    )

    def server(input, output, session):  # noqa: ARG001
        return None

    app = shinyjson.SpaApp(tmp_path, server)
    rendered = str(app.ui)
    assert marker in rendered
