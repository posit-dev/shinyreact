from __future__ import annotations

from pathlib import Path
from typing import Callable

from htmltools import HTML, HTMLDependency, TagList
from shiny import App
from shiny.session import Inputs, Outputs, Session


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyjson",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyjson.js", "defer": ""},
        stylesheet={"href": "shinyjson.css"},
    )


class SpaApp(App):
    """A Shiny app that serves a static SPA from a ``www/`` directory.

    The ``www_dir`` must contain an ``index.html`` file. All files in
    ``www_dir`` are served as static assets. The server function contains only
    reactive computation and business logic — no UI definitions.

    Args:
        www_dir: Path to the directory containing ``index.html`` and static
            assets. Typically ``Path(__file__).parent / "www"``.
        server: The Shiny server function.
    """

    def __init__(
        self,
        www_dir: str | Path,
        server: Callable[[Inputs, Outputs, Session], None],
        **kwargs: object,
    ) -> None:
        www_dir = Path(www_dir)
        ui = TagList(
            _dep(),
            HTML((www_dir / "index.html").read_text()),
        )
        super().__init__(ui, server, static_assets=www_dir, **kwargs)
