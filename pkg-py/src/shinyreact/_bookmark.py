from __future__ import annotations

import json

from htmltools import HTML, HTMLDependency, head_content, tags
from shiny.bookmark._restore_state import (
    RestoreContext,
    get_current_restore_context,
)

from ._protocol import PROTOCOL_VERSION


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


def _current_restore_values() -> dict[str, object]:
    """Restored input values for the active request, or {} when none.

    Returns ``{}`` when no session/RestoreContext is active (outside an HTTP
    request) or when no bookmark query string was parsed.
    """
    try:
        ctx = get_current_restore_context()
    except RuntimeError:
        # No active session/RestoreContext available outside an HTTP request.
        return {}
    if ctx is None:
        return {}
    return _read_restore_input_values(ctx)


def _config_script_tag() -> HTMLDependency:
    """Head-injected ``#shinyreact-config`` JSON script tag.

    Always emitted by page entry points. Carries the wire-protocol version
    (asserted by the JS client at boot — see
    ``decisions/2026-08-17-js-distribution.md``) and, when a bookmark is being
    restored, the restored input values under ``restore``.

    The payload is plain JSON in a ``type="application/json"`` script tag —
    the browser never executes it as JavaScript, so no JS-string-literal
    escaping is needed. Exactly one property of the encoding matters:

    - Every ``<`` is emitted as ``\\u003c`` so the payload can never contain
      ``</script`` (which would terminate the surrounding tag) or ``<!--``.

    ``json.dumps`` also defaults to ``ensure_ascii=True``, so non-ASCII lands
    as ``\\uXXXX`` escapes — but nothing depends on that. U+2028 / U+2029 were
    a hazard only while the payload was a JS string literal (#183); inside a
    JSON tag they are inert, which is why R emits them literally and the tests
    in both languages assert a *round-trip* rather than an escape.

    The client reads it with ``JSON.parse``, which treats keys like
    ``__proto__`` and ``constructor`` as ordinary own properties.

    SECURITY
    --------
    Bookmarked input values appear in the rendered HTML page source. In
    URL bookmark mode the values are also already in the URL itself, so this
    tag adds no exposure. In server-stored bookmark mode (``?_state_id_=...``)
    the URL hides the values, but this tag re-exposes them in the page
    source. Anything that can read the HTML — browser extensions, logging
    proxies, screen captures, "View Source" — can read these values. Apps must
    not put credentials, tokens, PII, or other sensitive data into inputs that
    participate in bookmarking.
    """
    config: dict[str, object] = {"protocolVersion": PROTOCOL_VERSION}
    values = _current_restore_values()
    if values:
        config["restore"] = values

    payload = json.dumps(config).replace("<", "\\u003c")
    return head_content(
        tags.script(HTML(payload), type="application/json", id="shinyreact-config")
    )
