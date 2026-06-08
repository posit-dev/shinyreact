"""Semantic role classes — UiInput, UiOutput, UiLayout.

These are markers indicating the component's primary purpose. State-bearing
and child-bearing capabilities are provided by orthogonal mixins
(HasInputValue, Updatable, AllowsChildren).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from ._base import UiComponent
from ._input_value import HasInputValue


class UiInput(UiComponent, HasInputValue):
    """Primarily a user-input control.

    Concrete subclasses MUST implement :meth:`value` returning the current
    server-readable value for the input. Reads happen reactively against the
    active session.
    """

    @abstractmethod
    def value(self) -> Any: ...


class UiOutput(UiComponent):
    """Primarily a server-rendered output.

    Carries its own `id` attribute (set by subclasses' __init__); does NOT
    inherit HasInputValue (no bookmark serializer, no id->instance map).
    Subclasses that expose read-only signals add accessors directly.
    """


class UiLayout(UiComponent):
    """Primarily a container.

    No id by itself; layouts that expose state add HasInputValue + Updatable.
    """
