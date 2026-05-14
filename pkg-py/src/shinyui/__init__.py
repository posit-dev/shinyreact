"""shinyui — prototype class-per-component UI hierarchy.

See docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md.
"""

from ._accordion import accordion
from ._accordion_panel import accordion_panel
from ._base import UiComponent
from ._bookmark import lookup_component
from ._card import card
from ._children import AllowsChildren
from ._input_action_button import input_action_button
from ._input_select import input_select
from ._input_slider import input_slider
from ._input_value import HasInputValue
from ._output_code import output_code
from ._output_plot import output_plot
from ._roles import UiInput, UiLayout, UiOutput
from ._updatable import Updatable

__all__ = [
    "AllowsChildren",
    "HasInputValue",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "Updatable",
    "accordion",
    "accordion_panel",
    "card",
    "input_action_button",
    "input_select",
    "input_slider",
    "lookup_component",
    "output_code",
    "output_plot",
]
