from __future__ import annotations

import pytest
import shinyui as sui


def _maker(cls):
    """Build a representative instance of `cls` with whatever args its factory needs."""
    if cls is sui.input_slider:
        return sui.input_slider("n", "N", 1, 10, 5)
    if cls is sui.input_select:
        return sui.input_select("c", "C", {"a": "A"})
    if cls is sui.output_code:
        return sui.output_code("o")
    if cls is sui.output_plot:
        return sui.output_plot("p")
    if cls is sui.card:
        return sui.card("b", id="m")
    if cls is sui.accordion:
        return sui.accordion(sui.accordion_panel("A"), id="acc")
    if cls is sui.accordion_panel:
        return sui.accordion_panel("X", "y")
    raise AssertionError(f"no maker for {cls}")


ALL_CLASSES = [
    sui.input_slider,
    sui.input_select,
    sui.output_code,
    sui.output_plot,
    sui.card,
    sui.accordion,
    sui.accordion_panel,
]


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_is_uicomponent(cls):
    assert isinstance(_maker(cls), sui.UiComponent)


@pytest.mark.parametrize(
    "cls,expected",
    [
        (sui.input_slider, {sui.UiInput, sui.HasInputValue, sui.Updatable}),
        (sui.input_select, {sui.UiInput, sui.HasInputValue, sui.Updatable}),
        (sui.output_code, {sui.UiOutput}),
        (sui.output_plot, {sui.UiOutput}),
        (
            sui.card,
            {sui.UiLayout, sui.AllowsChildren, sui.HasInputValue, sui.Updatable},
        ),
        (
            sui.accordion,
            {sui.UiLayout, sui.AllowsChildren, sui.HasInputValue, sui.Updatable},
        ),
        (sui.accordion_panel, {sui.UiLayout, sui.AllowsChildren}),
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
        (sui.input_slider, False),
        (sui.input_select, False),
        (sui.output_code, False),
        (sui.output_plot, False),
        (sui.card, True),
        (sui.accordion, True),
        (sui.accordion_panel, True),
    ],
)
def test_with_block_protocol(cls, allows_children):
    inst = _maker(cls)
    if allows_children:
        with inst as ctx:
            assert ctx is inst
    else:
        with pytest.raises(TypeError, match=r"context manager protocol"):
            with inst:  # noqa: B017  intentional protocol-violation check
                pass
