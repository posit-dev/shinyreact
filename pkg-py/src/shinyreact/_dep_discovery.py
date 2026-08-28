"""Automatic renderer HTML-dependency discovery for Core mode (#146, #203, #220).

Express's ``set_react_page()`` can inline renderer dependencies into the page
head because the page function runs after the renderers mount. A Core-mode page
(:func:`page_react`, :func:`page_react_html`) is built before ``server()`` runs,
so there is nothing to inline. Instead — the same design R uses
(``pkg-r/R/dep-discovery.R``) — after every reactive flush we diff the session's
registered outputs, extract each new output's UI, and push any not-yet-sent
dependencies to the client as a ``shinyreact-deps`` custom message. The JS
bundle loads them and re-runs ``Shiny.bindAll()``.

Diffing on *every* flush (not just the first) also covers outputs registered
after startup — e.g. a module server mounted inside an observer.

The hook: the JS bundle sends one ``.shinyreact_init`` ping (type
``shinyreact.init``) after Shiny initializes; that type's input handler
(``_input_handler.py``) calls :func:`install_dep_discovery`. Every session gets
exactly one ping, whether or not the app has any other inputs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from htmltools import HTMLDependency, Tag, TagList

if TYPE_CHECKING:
    from shiny.session import Session

_INSTALLED_FLAG = "_shinyreact_dep_discovery"


def install_dep_discovery(session: Session | None) -> bool:
    """Install the per-session flush hook. Returns whether it was installed."""
    if session is None:
        return False
    # `_outputs` and `on_flushed` are missing on mock/express-stub sessions;
    # discovery no-ops there rather than raising.
    outputs = getattr(getattr(session, "output", None), "_outputs", None)
    if outputs is None or not callable(getattr(session, "on_flushed", None)):
        return False
    # Two copies of the JS bundle on one page send two pings; install once.
    # (py-shiny has no `session$userData` equivalent, so: an attribute.)
    if getattr(session, _INSTALLED_FLAG, False):
        return False
    setattr(session, _INSTALLED_FLAG, True)

    seen_outputs: set[str] = set()
    sent_deps: set[str] = set()

    async def push_new_output_deps() -> None:
        new_names = [name for name in outputs if name not in seen_outputs]
        if not new_names:
            return
        seen_outputs.update(new_names)

        deps: list[HTMLDependency] = []
        for name in new_names:
            ui = outputs[name].renderer.auto_output_ui()
            if isinstance(ui, (Tag, TagList)):
                deps.extend(ui.tagify().get_dependencies())
        deps = [d for d in deps if f"{d.name}@{d.version}" not in sent_deps]
        if not deps:
            return
        sent_deps.update(f"{d.name}@{d.version}" for d in deps)

        # `_process_ui()` registers each dep's resource route with the app and
        # returns the client-side JSON (Python's `createWebDependency()`). The
        # client skips deps already on the page, so overlap is harmless.
        payload = session._process_ui(TagList(*deps))["deps"]
        await session.send_custom_message(
            "shinyreact-deps", cast("dict[str, object]", payload)
        )

    session.on_flushed(cast(Any, push_new_output_deps), once=False)
    return True
