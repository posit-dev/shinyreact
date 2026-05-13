"""reactive_calc_method — per-instance @reactive.calc decorator.

Inspired by Shiny's
``shiny.render._data_frame_utils._reactive_method.reactive_calc_method``.
We hand-roll a small local equivalent (~15 lines) to avoid coupling to a Shiny
private import. Stage B in py-shiny may extract the decorator to a public helper.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar
from weakref import WeakKeyDictionary

from shiny import reactive

T = TypeVar("T")


def reactive_calc_method(fn: Callable[[Any], T]) -> Callable[[Any], T]:
    cache: WeakKeyDictionary[Any, Any] = WeakKeyDictionary()

    def wrapper(self: Any) -> T:
        calc = cache.get(self)
        if calc is None:

            @reactive.calc
            def _calc() -> T:
                return fn(self)

            calc = _calc
            cache[self] = calc
        return calc()

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper
