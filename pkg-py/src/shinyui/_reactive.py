"""reactive_calc_method — per-instance @reactive.calc decorator.

Inspired by Shiny's
``shiny.render._data_frame_utils._reactive_method.reactive_calc_method``.
We hand-roll a small local equivalent to avoid coupling to a Shiny private
import. Stage B in py-shiny may extract the decorator to a public helper.

Session-awareness
-----------------
shinyui components are often constructed at module level, so the same
instance is reused across many WebSocket sessions. A ``@reactive.calc`` is
bound to whichever session was active when it was created and is destroyed
when that session ends. If we cache one calc per instance (instance-keyed
only), the second session sees a destroyed calc → ``DestroyedReactiveError``
→ session-wide crash → "grey overlay" in the browser.

The cache is keyed by the **current session** so each session gets a fresh
``@reactive.calc``. Two cleanup paths run together:

1. **Proactive:** when the captured session ends, the ``on_ended`` callback
   below clears the cached attribute on the instance. This drops the strong
   reference to the dead session promptly, before any subsequent accessor
   call.
2. **Lazy fallback:** if for any reason the ``on_ended`` callback hasn't
   fired yet (or the cache survived for another reason), the wrapper also
   detects a session mismatch at call time and rebuilds the calc.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from shiny import reactive
from shiny.session import get_current_session

T = TypeVar("T")


def reactive_calc_method(fn: Callable[[Any], T]) -> Callable[[Any], T]:
    # Single calc-cache slot per instance, stored as an instance attribute.
    # Holds a tuple (session_obj, calc) so we can detect cross-session reuse.
    attr_name = f"_rcm_calc_{fn.__name__}_{id(fn):x}"

    def wrapper(self: Any) -> T:
        sess = get_current_session()
        cached = getattr(self, attr_name, None)
        if cached is None or cached[0] is not sess:

            @reactive.calc
            def _calc() -> T:
                return fn(self)

            setattr(self, attr_name, (sess, _calc))
            if sess is not None:
                # Proactively drop the cached slot for this session when the
                # session ends. Avoids holding a strong reference to the dead
                # session via this attribute until the next accessor call
                # would otherwise overwrite it.
                def _evict(_sess=sess) -> None:
                    current = getattr(self, attr_name, None)
                    if current is not None and current[0] is _sess:
                        try:
                            delattr(self, attr_name)
                        except AttributeError:
                            pass

                sess.on_ended(_evict)
            return _calc()
        return cached[1]()

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper
