"""End-to-end dispatch of the `:shinyreact.default` / `:shinyreact.asis` wire suffix.

`test_input_handler.py` looks the handlers up in the `input_handlers` registry and
calls them directly, which never exercises the suffix-splitting path that puts them
to work. R covers the equivalent through `shiny:::applyInputHandler` in
`pkg-r/tests/testthat/test-input-handler.R`; this is the Python counterpart (#185).

The splitter lives in `AppSession._manage_inputs`, so we drive that method with a
minimal stand-in for `self` — enough to record what lands in `input` without
standing up a whole app.
"""

from __future__ import annotations

from typing import Any

import shinyreact  # noqa: F401  (import registers the handlers)
from shiny.session._session import AppSession


class _FakeInputValue:
    def __init__(self) -> None:
        self.value: Any = None
        self.force: bool | None = None

    def _set(self, value: Any, force: bool = False) -> None:
        self.value = value
        self.force = force


class _FakeInputs:
    def __init__(self) -> None:
        self.values: dict[str, _FakeInputValue] = {}

    def __getitem__(self, key: str) -> _FakeInputValue:
        return self.values.setdefault(key, _FakeInputValue())


class _FakeOutputs:
    def _manage_hidden(self) -> None:
        pass


class _FakeSession:
    def __init__(self) -> None:
        self.input = _FakeInputs()
        self.output = _FakeOutputs()


def _manage(data: dict[str, object]) -> _FakeInputs:
    session = _FakeSession()
    # Unbound call: exercises the real ":type" splitting and handler dispatch.
    AppSession._manage_inputs(session, data)  # type: ignore[arg-type]
    return session.input


def test_default_suffix_dispatches_and_strips_the_type() -> None:
    records = [{"name": "a", "size": 1}, {"name": "b", "size": 2}]
    inputs = _manage({"files:shinyreact.default": records})

    # The id the server sees has no ":type" suffix.
    assert list(inputs.values) == ["files"]
    assert inputs["files"].value == records


def test_asis_suffix_dispatches_and_strips_the_type() -> None:
    inputs = _manage({"coords:shinyreact.asis": [[1, 2], [3, 4]]})

    assert list(inputs.values) == ["coords"]
    assert inputs["coords"].value == [[1, 2], [3, 4]]


def test_untyped_id_bypasses_handler_dispatch() -> None:
    inputs = _manage({"n": 42})

    assert list(inputs.values) == ["n"]
    assert inputs["n"].value == 42


def test_namespaced_id_keeps_its_module_prefix() -> None:
    inputs = _manage({"mod-files:shinyreact.default": [{"a": 1}]})

    assert list(inputs.values) == ["mod-files"]
    assert inputs["mod-files"].value == [{"a": 1}]


def test_values_are_set_with_force() -> None:
    # Every wire value must recalculate dependents, matching R Shiny's
    # dedupe=FALSE behavior; a handled value must not lose that.
    inputs = _manage({"files:shinyreact.default": [{"a": 1}]})

    assert inputs["files"].force is True
