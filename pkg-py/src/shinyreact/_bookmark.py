from __future__ import annotations

import json

from htmltools import HTML, HTMLDependency, head_content, tags
from shiny.bookmark._restore_state import (
    RestoreContext,
    get_current_restore_context,
)


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


def _restore_script_tag() -> HTMLDependency | None:
    """Return a head-injected <script> carrying restored input values, or None.

    Reads the active Shiny ``RestoreContext`` set up during the HTTP request
    that loaded the page. Returns ``None`` when no bookmark query string was
    parsed or the context's input map is empty.

    SECURITY
    --------
    Bookmarked input values appear in the rendered HTML page source. In
    URL bookmark mode the values are also already in the URL itself, so this
    script adds no exposure. In server-stored bookmark mode (``?_state_id_=...``)
    the URL hides the values, but this script re-exposes them in the page
    source. Anything that can read the HTML — browser extensions, logging
    proxies, screen captures, "View Source" — can read these values. Apps must
    not put credentials, tokens, PII, or other sensitive data into inputs that
    participate in bookmarking.
    """
    try:
        ctx = get_current_restore_context()
    except RuntimeError:
        # No active session/RestoreContext available outside an HTTP request.
        return None
    if ctx is None:
        return None
    values = _read_restore_input_values(ctx)
    if not values:
        return None

    # Wrap the JSON in JSON.parse(<js-string-literal>) so values whose
    # keys happen to be "__proto__" or "constructor" survive intact.
    # A bare JS object literal ``{"__proto__": ...}`` treats "__proto__"
    # as the prototype setter rather than a data property; JSON.parse
    # creates them as ordinary own properties.
    #
    # Two layers of escaping:
    #   1. Inside the JSON payload: replace "</" with "<\\/" so the
    #      embedded JSON can't prematurely close the surrounding <script>
    #      tag.
    #   2. Outside, wrapping the JSON as a JS string literal: a second
    #      json.dumps double-encodes (quotes + escapes) the JSON text so
    #      it parses as a normal JS string — avoiding the trap where
    #      raw \\n / single-quote characters in JSON would be interpreted
    #      by the JS parser before JSON.parse sees them.
    #
    # ``json.dumps`` defaults to ensure_ascii=True, so non-ASCII
    # (including the JS-only-illegal U+2028 / U+2029) is emitted as
    # \\uXXXX escapes — safe in both layers.
    json_payload = json.dumps(values).replace("</", "<\\/")
    js_string_literal = json.dumps(json_payload)
    js = (
        "window.shinyreact = window.shinyreact || {};"
        f"window.shinyreact._restore = JSON.parse({js_string_literal});"
    )
    return head_content(tags.script(HTML(js)))
