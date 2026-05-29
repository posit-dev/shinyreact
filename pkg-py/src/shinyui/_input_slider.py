"""input_slider — class-based input_slider with typed update() and value() accessor."""

from __future__ import annotations

from typing import Any

from htmltools import Tagified

from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()


class input_slider(UiInput, Updatable):
    """Numeric slider input.

    Wire id: ``input.<id>()`` is the current slider value (a ``float``, or a
    ``(min, max)`` tuple if ``value`` was passed as a 2-tuple — i.e. a
    range-slider). The class accessor :meth:`value` returns the same.

    Example
    -------
    .. code-block:: python

        n = input_slider("n", "Sample size", 1, 1000, 100)

        # In server:
        @render.code
        def summary():
            return f"n = {n.value()}"

        # Push a new value from the server:
        n.update(value=500)
    """

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
        """Build a slider.

        Parameters
        ----------
        id
            Input id; available as ``input.<id>()`` server-side, or via
            :meth:`value`.
        label
            Display label.
        min, max
            Inclusive slider range.
        value
            Initial value. Pass a ``(low, high)`` tuple for a range slider.
        step
            Minimum delta between adjacent values; ``None`` lets shiny pick.
        ticks, animate, width, sep, pre, post, time_format, timezone, drag_range
            Forwarded verbatim to :func:`shiny.ui.input_slider`; see shiny's
            docs for semantics.
        """
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

    def tagify(self) -> Tagified:
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
        ).tagify()

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
