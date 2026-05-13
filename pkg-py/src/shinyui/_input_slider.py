"""input_slider — class-based input_slider with typed update() and value() accessor."""

from __future__ import annotations

from typing import Any

from htmltools import Tag

from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()


class input_slider(UiInput, Updatable):  # noqa: N801
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
        self.label = label
        self.min = min
        self.max = max
        self._init_value = value  # avoid shadowing the value() accessor
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
        super().__init__(id=id)

    @reactive_calc_method
    def value(self) -> Any:
        return self._read_input()

    def tagify(self) -> Tag:
        # Delegating to shiny.ui — markup origin per the design spec.
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

    def update(
        self,
        *,
        value: Any = _MISSING,
        min: float = _MISSING,  # type: ignore[assignment]
        max: float = _MISSING,  # type: ignore[assignment]
        step: float = _MISSING,  # type: ignore[assignment]
        label: str = _MISSING,  # type: ignore[assignment]
    ) -> None:
        sess = self._require_session(for_op="update")
        msg: dict[str, Any] = {}
        if value is not _MISSING:
            msg["value"] = value
        if min is not _MISSING:
            msg["min"] = min
        if max is not _MISSING:
            msg["max"] = max
        if step is not _MISSING:
            msg["step"] = step
        if label is not _MISSING:
            msg["label"] = label
        sess.send_input_message(self.id, msg)
