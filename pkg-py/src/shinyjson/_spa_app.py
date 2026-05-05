from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable

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
    """A Shiny app that serves a static SPA from a directory of assets.

    The directory must contain an ``index.html`` file. All files in it are
    served as static assets. The server function contains only reactive
    computation and business logic — no UI definitions.

    Args:
        server: The Shiny server function.
        static_dir: Path to the directory containing ``index.html`` and static
            assets. Defaults to ``./www`` relative to the file that constructs
            ``SpaApp`` (typically the app's ``app.py``).

    Example::

        from shinyjson import SpaApp

        def server(input, output, session):
            ...

        app = SpaApp(server)  # serves ./www/ next to this file
    """

    def __init__(
        self,
        server: Callable[[Inputs, Outputs, Session], None],
        *,
        static_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        if static_dir is None:
            caller_file = inspect.stack()[1].filename
            static_dir = Path(caller_file).parent / "www"
        static_dir = Path(static_dir)
        ui = TagList(
            _dep(),
            HTML((static_dir / "index.html").read_text()),
        )
        super().__init__(ui, server, static_assets=static_dir, **kwargs)
