from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable

from htmltools import HTML, TagList
from shiny import App
from shiny.session import Inputs, Outputs, Session

from ._output import _dep


class ReactApp(App):
    """A Shiny app that serves a custom React client from a directory of assets.

    Pairs a Shiny server (reactive computation only) with a built React client
    — typically an ``index.html`` produced from an ``index.tsx`` source. All
    files in the directory are served as static assets. The server function
    contains only reactive computation and business logic — no UI definitions.

    Args:
        server: The Shiny server function.
        static_dir: Path to the directory containing ``index.html`` and static
            assets. Defaults to ``./www`` relative to the file that constructs
            ``ReactApp`` (typically the app's ``app.py``).

    Example::

        from shinyreact import ReactApp

        def server(input, output, session):
            ...

        app = ReactApp(server)  # serves ./www/ next to this file
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
