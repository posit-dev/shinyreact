"""Core-mode automatic output dependency discovery (#220).

Mirrors R's pkg-r/tests/testthat/test-dep-discovery.R. The Express-mode
counterpart (inline harvest at page-generation time) is in
test_page_dep_harvest.py; Core-mode pages render before server() runs, so deps
must be pushed after each flush instead.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from htmltools import HTMLDependency, TagChild, TagList, div
from shiny.express._stub_session import ExpressStubSession
from shiny.input_handler import input_handlers
from shiny.render.renderer import Renderer
from shiny.session import session_context
from shinyreact._dep_discovery import install_dep_discovery


class _FakeSession(ExpressStubSession):
    """ExpressStubSession + the slice discovery touches: flush callbacks,
    custom messages, and a real (route-less) _process_ui."""

    def __init__(self) -> None:
        super().__init__()
        self.flush_callbacks: list[Callable[[], Any]] = []
        self.messages: list[tuple[str, Any]] = []

    def on_flushed(self, fn, once: bool = True):  # type: ignore[override]
        self.flush_callbacks.append(fn)
        return lambda: None

    def _process_ui(self, ui: TagChild):  # type: ignore[override]
        deps = TagList(ui).render()["dependencies"]
        return {"deps": [d.as_dict(lib_prefix="lib") for d in deps], "html": ""}

    async def send_custom_message(self, type: str, message: Any) -> None:
        self.messages.append((type, message))

    def flush(self) -> None:
        for fn in self.flush_callbacks:
            asyncio.run(fn())


def _fake_dep(name: str, version: str = "1.0.0") -> HTMLDependency:
    return HTMLDependency(name, version, source={"href": name}, script={"src": "x.js"})


def _define_output(
    session: _FakeSession, name: str, dep: HTMLDependency | None
) -> None:
    class render_widget(Renderer[str]):  # noqa: N801
        def auto_output_ui(self):
            return div(dep, id=self.output_id) if dep is not None else None

        async def transform(self, value: str) -> str:  # pragma: no cover
            return value

    def value_fn() -> str:  # pragma: no cover - never rendered
        return "value"

    value_fn.__name__ = name  # the output id comes from the function name
    with session_context(session):
        render_widget(value_fn)


def _sent_dep_names(message: Any) -> list[str]:
    return [dep["name"] for dep in message]


def test_discovery_pushes_new_output_deps_once_per_flush() -> None:
    session = _FakeSession()
    assert install_dep_discovery(session) is True

    _define_output(session, "plot1", _fake_dep("fake-binding"))
    session.flush()
    assert len(session.messages) == 1
    assert session.messages[0][0] == "shinyreact-deps"
    assert _sent_dep_names(session.messages[0][1]) == ["fake-binding"]

    # No new outputs => no message on later flushes.
    session.flush()
    assert len(session.messages) == 1


def test_discovery_covers_late_outputs_without_resends() -> None:
    session = _FakeSession()
    install_dep_discovery(session)

    _define_output(session, "a", _fake_dep("binding-a"))
    session.flush()

    # A late-mounted output (e.g. a module server inside an observer): its new
    # dep is pushed, the already-sent one is not.
    _define_output(session, "b", _fake_dep("binding-a"))
    _define_output(session, "c", _fake_dep("binding-c"))
    session.flush()

    assert len(session.messages) == 2
    assert _sent_dep_names(session.messages[1][1]) == ["binding-c"]


def test_dep_less_outputs_push_nothing() -> None:
    session = _FakeSession()
    install_dep_discovery(session)
    _define_output(session, "txt", None)
    session.flush()
    assert session.messages == []


def test_install_is_idempotent_per_session() -> None:
    session = _FakeSession()
    assert install_dep_discovery(session) is True
    assert install_dep_discovery(session) is False
    _define_output(session, "a", _fake_dep("binding-a"))
    session.flush()
    assert len(session.messages) == 1


def test_install_no_ops_without_a_real_session() -> None:
    assert install_dep_discovery(None) is False
    assert install_dep_discovery(object()) is False  # type: ignore[arg-type]


def test_init_handler_installs_discovery() -> None:
    session = _FakeSession()
    assert input_handlers["shinyreact.init"](1, "x", session) == 1
    assert session.flush_callbacks != []


def test_value_handlers_do_not_install_discovery() -> None:
    session = _FakeSession()
    input_handlers["shinyreact.default"]([], "x", session)
    input_handlers["shinyreact.asis"](1, "x", session)
    assert session.flush_callbacks == []
