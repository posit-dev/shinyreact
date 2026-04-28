from __future__ import annotations

from pathlib import Path
from typing import Callable

from htmltools import HTML, TagList
from shiny import App
from shiny.session import Inputs, Outputs, Session


class SpaApp(App):
    """A Shiny app that serves a static SPA from a ``www/`` directory.

    The ``www/`` directory must contain an ``index.html`` file. All files in
    ``www/`` are served as static assets. The server function contains only
    reactive computation and business logic — no UI definitions.

    Args:
        www_dir: Path to the directory containing ``index.html`` and static
            assets. Typically ``Path(__file__).parent / "www"``.
        server: The Shiny server function.
    """

    # In the final design, index.html should be a fully self-contained HTML
    # file (with its own <html>, <head>, <body>) served as-is. For this POC,
    # it is a stub: Shiny still needs to process it and inject its own runtime
    # scripts because the Shiny JS client is not yet installable from npm.
    def __init__(
        self,
        www_dir: str | Path,
        server: Callable[[Inputs, Outputs, Session], None],
        **kwargs: object,
    ) -> None:
        www_dir = Path(www_dir)
        ui = TagList(HTML((www_dir / "index.html").read_text()))
        super().__init__(ui, server, static_assets=www_dir, **kwargs)
