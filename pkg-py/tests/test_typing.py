"""The public API as a *caller* sees it, checked by pyright rather than pytest.

These functions assert nothing meaningful at runtime -- they barely run. Their
job is to fail `make py-check-types` if a signature stops accepting the values
user code actually produces, which no runtime test can catch: an over-narrow
annotation still passes every assertion in the rest of the suite.

Return types are written out deliberately. An unannotated
`def f(): return {"a": 1}` would be inferred, and inference against the
parameter type is exactly what hides this class of bug.

Not covered here, deliberately: the JSON payload types of `reactive_output`
and `send_message`. `Jsonifiable` spells its containers as `dict` and `list`,
both invariant in their element types, so a render function returning
`dict[str, int]` is not assignable to it -- the most ordinary thing a
`reactive_output` does. That is an upstream bug (py-shiny#2497), suppressed at
each call site with a `# pyright: ignore[reportArgumentType]` naming the issue;
grep `2497` to find them all when it lands.
"""

from __future__ import annotations

from pathlib import Path

from shiny import App, Inputs, Outputs, Session
from shinyreact import ReactApp, page_react_html


def html_document_is_accepted_as_app_ui(index: Path) -> App:
    """`page_react_html()` returns what `App(ui=)` accepts.

    `App(ui=)` takes py-shiny's `PageHtmlDocument`, not its wider
    `HTMLTextDocument` base, so declaring the base here would make the
    documented plain-`shiny.App` path fail to type-check.
    """

    def server(i: Inputs, o: Outputs, s: Session) -> None: ...

    return App(page_react_html(index), server)


def html_document_is_accepted_as_react_app_ui(index: Path) -> App:
    """The same document through `ReactApp(ui=)`, which also mounts its dir."""

    def server(i: Inputs, o: Outputs, s: Session) -> None: ...

    return ReactApp(server, ui=page_react_html(index))


def test_module_type_checks() -> None:
    """A pytest anchor, so the file is not mistaken for dead code.

    The real assertion is that pyright reports no error for this module; see
    `[tool.pyright] include` in `pyproject.toml`.
    """
    assert callable(html_document_is_accepted_as_app_ui)
