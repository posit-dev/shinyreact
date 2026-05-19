"""shinyuiclassonly — class-per-component UI hierarchy, stripped of session machinery.

A smaller delta from existing shiny.ui behavior than shinyui: the class
hierarchy, AllowsChildren + parent-tag context stack, and Core/Express
overloads, with no session capture, no `.value()`/`.update()` accessors,
no input-handler or bookmark registration. Server code reads inputs via
`input.<id>()` and pushes updates via `shiny.ui.update_*` the usual way.

See docs/superpowers/specs/2026-05-19-shinyuiclassonly-design.md.
"""

from ._base import UiComponent
from ._card import card
from ._children import AllowsChildren
from ._ctx_tag import CtxTag
from ._roles import UiInput, UiLayout, UiOutput

__all__ = [
    "AllowsChildren",
    "CtxTag",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "card",
]
