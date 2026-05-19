"""Semantic role classes — UiInput, UiOutput, UiLayout.

These are pure marker subclasses of :class:`UiComponent`. They indicate
the component's primary purpose (input control, output placeholder,
layout container) but carry no behavior of their own.

This is the structure-only sibling of ``shinyui._roles``. The shinyui
equivalents declare an abstract ``UiInput.value()`` and rely on
``HasInputValue`` for input-handler / bookmark registration; here all of
that is gone — these classes are bare markers.
"""

from __future__ import annotations

from ._base import UiComponent


class UiInput(UiComponent):
    """Marker: primarily a user-input control."""


class UiOutput(UiComponent):
    """Marker: primarily a server-rendered output."""


class UiLayout(UiComponent):
    """Marker: primarily a container."""
