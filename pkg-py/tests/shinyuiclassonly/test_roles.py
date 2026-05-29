from __future__ import annotations

from htmltools import tags
from shinyuiclassonly._base import UiComponent
from shinyuiclassonly._roles import UiInput, UiLayout, UiOutput


class _MyInput(UiInput):
    def tagify(self):
        return tags.div()


class _MyOutput(UiOutput):
    def tagify(self):
        return tags.div()


class _MyLayout(UiLayout):
    def tagify(self):
        return tags.div()


def test_roles_are_uicomponent_subclasses():
    assert issubclass(UiInput, UiComponent)
    assert issubclass(UiOutput, UiComponent)
    assert issubclass(UiLayout, UiComponent)


def test_roles_have_no_extra_abstract_methods():
    """UiInput has no abstract value() method (delta vs. shinyui)."""
    _MyInput()
    _MyOutput()
    _MyLayout()


def test_role_inheritance_independent():
    """Roles are sibling categories, not a chain."""
    assert not issubclass(UiInput, UiOutput)
    assert not issubclass(UiOutput, UiLayout)
    assert not issubclass(UiLayout, UiInput)
