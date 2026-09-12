from __future__ import annotations

from typing import Mapping, Sequence, Union

JsonValue = Union[
    str,
    int,
    float,
    bool,
    None,
    Sequence["JsonValue"],
    Mapping[str, "JsonValue"],
]
"""Any JSON-serializable value, as accepted from user code.

Shiny's ``Jsonifiable`` spells its containers as ``list`` and ``dict``, both of
which are **invariant** in their element types. That makes the natural thing a
caller writes -- a function returning ``dict[str, int]``, or a
``dict[str, str]`` variable -- unassignable to it, so the most common
``reactive_output`` and ``send_message`` payloads fail to type-check for no
runtime reason.

``Sequence`` and ``Mapping`` are covariant in their element types, so this
alias accepts exactly the values ``Jsonifiable`` describes without forcing
every call site to annotate its own return type as ``Jsonifiable``. Use it on
the way *in*, from user code; ``Jsonifiable`` stays the type on the way *out*,
to Shiny.
"""
