from __future__ import annotations

from htmltools import tags
from shinyui._base import UiComponent
from shinyui._input_value import HasInputValue
from shinyui._roles import UiInput, UiLayout, UiOutput


class _MyInput(UiInput):
    def tagify(self):
        return tags.div(id=self.id)


class _MyOutput(UiOutput):
    def __init__(self, id: str) -> None:
        self.id = id
        super().__init__()

    def tagify(self):
        return tags.div(id=self.id)


class _MyLayout(UiLayout):
    def tagify(self):
        return tags.div()


def test_uiinput_inherits_uicomponent_and_hasinputvalue():
    inst = _MyInput(id="x")
    assert isinstance(inst, UiComponent)
    assert isinstance(inst, HasInputValue)


def test_uioutput_has_id_attribute():
    inst = _MyOutput(id="y")
    assert inst.id == "y"


def test_uilayout_does_not_have_hasinputvalue_by_default():
    inst = _MyLayout()
    assert not isinstance(inst, HasInputValue)
