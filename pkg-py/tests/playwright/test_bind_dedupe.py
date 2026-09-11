"""No two overlapping `bindAll` passes, in a real browser (#298, #299, #301).

`ShinyOutput` binds by passing its own *parent* as scope, so several of them
under one parent all scan the same subtree. Shiny's `bindOutputs()` is async
and marks an element `.shiny-bound-output` only after an `await`, so
overlapping passes each bind every sibling, and Shiny's duplicate-id
bookkeeping records one entry per pass — surfacing as a
`[shiny] Duplicate output IDs were found` console warning that no jsdom test
can reproduce (a mocked `bindAll` is synchronous, and marks nothing bound).

Keying on the scope element catches siblings sharing one parent; nested
parents are two different elements, and `bindAll` is descendants-only, so the
outer pass walks the inner scope's outputs too and both register them. The
fixture nests a parent inside the sibling container to cover that, including
an output mounting late under the nested parent — the case whose queued pass
has to wait for the overlapping *outer* pass as well as for its own scope's.

The other half of the contract is that deduping must not *lose* a binding:
a `ShinyOutput` mounting while a pass is already in flight cannot reuse it,
because that pass scanned the parent before the element existed. It would
bind nothing and report nothing — a silently dead output. The fixture forces
that ordering by holding each pass open for 250ms after its scan.
"""

import re

from playwright.sync_api import ConsoleMessage, Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

bind_dedupe_app = create_app_fixture("apps/bind_dedupe/app.py")

BOUND_OUTPUT = re.compile(r"\bshiny-bound-output\b")
ECHO = '{"a":9,"b":19,"letter":"a","nested":29,"nested_letter":"x"}'


def test_sibling_shiny_outputs_log_no_duplicate_id_warning(
    page: Page, bind_dedupe_app: ShinyAppProc
) -> None:
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(_text(msg)))

    page.goto(bind_dedupe_app.url)

    # Wait for every binding pass to have settled before reading the console:
    # the warning is emitted by the binding itself, so asserting earlier would
    # pass for the wrong reason.
    expect(page.locator("#echo-view")).to_have_text(ECHO)
    expect(page.locator("#widgets_late")).to_have_class(BOUND_OUTPUT)
    expect(page.locator("#widgets_nested_late")).to_have_class(BOUND_OUTPUT)

    # Shiny reports both duplicated ids ("Duplicate") and an id used as both
    # an input and an output ("Shared") through the same path.
    offending = [m for m in messages if "Duplicate" in m or "Shared" in m]
    assert offending == [], f"Shiny reported duplicate bindings: {offending}"


def test_shiny_output_mounting_during_a_pass_is_still_bound(
    page: Page, bind_dedupe_app: ShinyAppProc
) -> None:
    page.goto(bind_dedupe_app.url)

    # `widgets_late` mounts a commit after its two siblings, while the pass
    # they share is still in flight. Reusing that pass would leave it
    # unbound, so the server's markup would never arrive here.
    expect(page.locator("#widgets_late")).to_have_class(BOUND_OUTPUT)
    expect(page.locator("#widgets_late .selectize-input")).to_contain_text("a")

    # And the siblings that did share one pass are bound too.
    expect(page.locator("#widgets_a")).to_have_class(BOUND_OUTPUT)
    expect(page.locator("#widgets_b")).to_have_class(BOUND_OUTPUT)

    # All three widgets are live: their values reach the server.
    expect(page.locator("#echo-view")).to_have_text(ECHO)


def test_shiny_outputs_under_a_nested_parent_are_bound(
    page: Page, bind_dedupe_app: ShinyAppProc
) -> None:
    page.goto(bind_dedupe_app.url)

    # Serializing the nested scope behind the container's pass must not drop
    # it: both of these mount under a parent the container's own pass also
    # walks, and the late one under a scope whose pass was already queued.
    expect(page.locator("#widgets_nested")).to_have_class(BOUND_OUTPUT)
    expect(page.locator("#widgets_nested_late")).to_have_class(BOUND_OUTPUT)
    expect(page.locator("#widgets_nested_late .selectize-input")).to_contain_text("x")

    # Live, not merely bound: their values reach the server.
    expect(page.locator("#echo-view")).to_have_text(ECHO)


def _text(msg: ConsoleMessage) -> str:
    return f"{msg.type}: {msg.text}"
