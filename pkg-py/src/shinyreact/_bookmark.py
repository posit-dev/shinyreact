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

    # Escape "</" so the JSON cannot terminate the surrounding <script> tag.
    safe_json = json.dumps(values).replace("</", "<\\/")
    js = (
        "window.shinyreact = window.shinyreact || {};"
        f"window.shinyreact._restore = JSON.parse('{safe_json}');"
    )
    return head_content(tags.script(HTML(js)))
