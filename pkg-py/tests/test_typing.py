"""The public API as a *caller* sees it, checked by pyright rather than pytest.

These functions assert nothing at runtime -- they barely run. Their job is to
fail `make py-check-types` if a signature stops accepting the values user code
actually produces, which no runtime test can catch: an over-narrow annotation
still passes every assertion in `test_reactive_output.py`.

Each return type below is written out deliberately. An unannotated
`def f(): return {"a": 1}` would be inferred, and inference is exactly what
hides the bug: `dict[str, int]` is not assignable to `dict[str, Jsonifiable]`
because `dict` is invariant in its value type, so the most ordinary thing a
`reactive_output` does used to be a type error at every call site (every
example app included). `Mapping` / `Sequence` are covariant, hence
`shinyreact._json.JsonValue`.
"""

from __future__ import annotations

from pathlib import Path

from shiny import App, Inputs, Outputs, Session
from shinyreact import ReactApp, page_react_html, reactive_output, send_message


@reactive_output
def dict_of_int() -> dict[str, int]:
    return {"a": 1}


@reactive_output
def dict_of_list() -> dict[str, list[float]]:
    return {"breaks": [1.0, 2.0]}


@reactive_output
def nested_dict() -> dict[str, dict[str, list[str]]]:
    return {"cols": {"A": ["Apple"]}}


@reactive_output
def list_of_dict() -> list[dict[str, str]]:
    return [{"name": "a"}]


@reactive_output
def plain_str() -> str:
    return "hello"


@reactive_output
def plain_none() -> None:
    return None


async def send_typed_values(session: Session, counts: dict[str, int]) -> None:
    """`send_message()` takes the same JSON values `reactive_output` returns.

    A dict *literal* would be inferred against the parameter type and pass
    either way; a `dict[str, int]` variable is what catches the invariance.
    """
    await send_message(session, "counts", counts)
    await send_message(session, "names", ["a", "b"])


def html_document_is_accepted_as_app_ui(index: Path) -> App:
    """`page_react_html()` returns what `App(ui=)` accepts.

    `App(ui=)` takes py-shiny's `PageHtmlDocument`, not its wider
    `HTMLTextDocument` base, so declaring the base here would make the
    documented plain-`shiny.App` path fail to type-check.
    """

    def server(i: Inputs, o: Outputs, s: Session) -> None: ...

    return App(page_react_html(index), server)


def react_app_is_a_shiny_app(index: Path) -> App:
    def server(i: Inputs, o: Outputs, s: Session) -> None: ...

    return ReactApp(server, ui=page_react_html(index))


def test_module_type_checks() -> None:
    """A pytest anchor, so the file is not mistaken for dead code.

    The real assertion is that pyright reports no error for this module; see
    `[tool.pyright] include` in `pyproject.toml`.
    """
    assert dict_of_int.auto_output_ui() is None
