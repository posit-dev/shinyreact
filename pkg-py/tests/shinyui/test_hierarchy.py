from __future__ import annotations

import pytest
import shinyui as sui


def _maker(cls):
    """Build a representative instance of `cls` with whatever args its factory needs."""
    if cls is sui.UiInputSlider:
        return sui.input_slider("n", "N", 1, 10, 5)
    if cls is sui.UiInputSelect:
        return sui.input_select("c", "C", {"a": "A"})
    if cls is sui.UiOutputCode:
        return sui.output_code("o")
    if cls is sui.UiOutputPlot:
        return sui.output_plot("p")
    if cls is sui.UiCard:
        return sui.card("b", id="m")
    if cls is sui.UiAccordion:
        return sui.accordion(sui.accordion_panel("A"), id="acc")
    if cls is sui.UiAccordionPanel:
        return sui.accordion_panel("X", "y")
    raise AssertionError(f"no maker for {cls}")


ALL_CLASSES = [
    sui.UiInputSlider,
    sui.UiInputSelect,
    sui.UiOutputCode,
    sui.UiOutputPlot,
    sui.UiCard,
    sui.UiAccordion,
    sui.UiAccordionPanel,
]


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_is_uicomponent(cls):
    assert isinstance(_maker(cls), sui.UiComponent)


@pytest.mark.parametrize(
    "cls,expected",
    [
        (sui.UiInputSlider, {sui.UiInput, sui.HasInputValue, sui.Updatable}),
        (sui.UiInputSelect, {sui.UiInput, sui.HasInputValue, sui.Updatable}),
        (sui.UiOutputCode, {sui.UiOutput}),
        (sui.UiOutputPlot, {sui.UiOutput}),
        (
            sui.UiCard,
            {sui.UiLayout, sui.AllowsChildren, sui.HasInputValue, sui.Updatable},
        ),
        (
            sui.UiAccordion,
            {sui.UiLayout, sui.AllowsChildren, sui.HasInputValue, sui.Updatable},
        ),
        (sui.UiAccordionPanel, {sui.UiLayout, sui.AllowsChildren}),
    ],
)
def test_expected_bases(cls, expected):
    inst = _maker(cls)
    for base in expected:
        assert isinstance(inst, base), (
            f"{cls.__name__} should be instance of {base.__name__}"
        )


@pytest.mark.parametrize(
    "cls,allows_children",
    [
        (sui.UiInputSlider, False),
        (sui.UiInputSelect, False),
        (sui.UiOutputCode, False),
        (sui.UiOutputPlot, False),
        (sui.UiCard, True),
        (sui.UiAccordion, True),
        (sui.UiAccordionPanel, True),
    ],
)
def test_with_block_protocol(cls, allows_children):
    inst = _maker(cls)
    if allows_children:
        with inst as ctx:
            assert ctx is inst
    else:
        with pytest.raises(TypeError, match=f"{cls.__name__} does not accept children"):
            inst.__enter__()
