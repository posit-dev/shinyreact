"""shinyui — prototype class-per-component UI hierarchy.

See docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md.
"""

from ._accordion import UiAccordion, accordion
from ._accordion_panel import UiAccordionPanel, accordion_panel
from ._base import UiComponent
from ._card import UiCard, card
from ._children import AllowsChildren
from ._input_select import UiInputSelect, input_select
from ._input_slider import UiInputSlider, input_slider
from ._input_value import HasInputValue
from ._output_code import UiOutputCode, output_code
from ._output_plot import UiOutputPlot, output_plot
from ._roles import UiInput, UiLayout, UiOutput
from ._updatable import Updatable

__all__ = [
    "AllowsChildren",
    "HasInputValue",
    "UiAccordion",
    "UiAccordionPanel",
    "UiCard",
    "UiComponent",
    "UiInput",
    "UiInputSelect",
    "UiInputSlider",
    "UiLayout",
    "UiOutput",
    "UiOutputCode",
    "UiOutputPlot",
    "Updatable",
    "accordion",
    "accordion_panel",
    "card",
    "input_select",
    "input_slider",
    "output_code",
    "output_plot",
]
