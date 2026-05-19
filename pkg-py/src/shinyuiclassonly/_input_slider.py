"""input_slider — class-based numeric slider, structure-only.

Structure-only sibling of ``shinyui.input_slider``. Same ``tagify()``
delegation to ``shiny.ui.input_slider``. The ``value()`` accessor and
``update()`` method are dropped — read via ``input.<id>()`` and push
via ``shiny.ui.update_slider`` from the server.
"""

from __future__ import annotations

from typing import Any

from htmltools import Tag

from ._roles import UiInput


class input_slider(UiInput):
    """Numeric slider input."""

    def __init__(
        self,
        id: str,
        label: str,
        min: float,
        max: float,
        value: float | tuple[float, float],
        *,
        step: float | None = None,
        ticks: bool = False,
        animate: bool | Any = False,
        width: str | None = None,
        sep: str = ",",
        pre: str | None = None,
        post: str | None = None,
        time_format: str | None = None,
        timezone: str | None = None,
        drag_range: bool = True,
    ) -> None:
        self.id = id
        self.label = label
        self.min = min
        self.max = max
        self._init_value = value
        self.step = step
        self.ticks = ticks
        self.animate = animate
        self.width = width
        self.sep = sep
        self.pre = pre
        self.post = post
        self.time_format = time_format
        self.timezone = timezone
        self.drag_range = drag_range

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.input_slider(
            self.id,
            self.label,
            self.min,
            self.max,
            self._init_value,
            step=self.step,
            ticks=self.ticks,
            animate=self.animate,
            width=self.width,
            sep=self.sep,
            pre=self.pre,
            post=self.post,
            time_format=self.time_format,
            timezone=self.timezone,
            drag_range=self.drag_range,
        )
