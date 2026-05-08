from __future__ import annotations

from shiny.bookmark._restore_state import RestoreContext


def _read_restore_input_values(ctx: RestoreContext) -> dict[str, object]:
    """Return the underlying input value map from a RestoreContext.

    Reads ``ctx.input.as_dict()`` directly. Does NOT call ``RestoreInputSet.get()``
    or the public ``restore_input(id, default)`` helper — those mark each value
    as pending and Shiny's normal flow would mark them used on the first flush,
    making the value unavailable to subsequent ``restore_input`` callers in the
    same render. We only want to *report* the values to the client; consumption
    semantics are unchanged.
    """
    return ctx.input.as_dict()
