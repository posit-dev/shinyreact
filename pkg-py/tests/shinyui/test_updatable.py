from __future__ import annotations

import pytest
from htmltools import tags
from shinyui._base import UiComponent
from shinyui._updatable import Updatable


class _AbstractStub(UiComponent, Updatable):
    """Does NOT implement update() — should remain abstract."""

    def tagify(self):
        return tags.div()


class _Concrete(UiComponent, Updatable):
    last_kwargs: dict | None = None

    def tagify(self):
        return tags.div()

    def update(self, *, value: int | None = None) -> None:
        type(self).last_kwargs = {"value": value}


def test_abstract_class_cannot_instantiate():
    with pytest.raises(TypeError):
        _AbstractStub()  # type: ignore[abstract]


def test_concrete_class_instantiates():
    c = _Concrete()
    assert c is not None


def test_update_callable_on_concrete():
    c = _Concrete()
    c.update(value=42)
    assert _Concrete.last_kwargs == {"value": 42}
