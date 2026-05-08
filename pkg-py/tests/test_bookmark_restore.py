import json
import re

from htmltools import HTMLDependency, TagList
from shiny.bookmark._restore_state import RestoreContext, RestoreInputSet
from shiny.bookmark._restore_state import restore_context as restore_context_cm
from shinyreact._bookmark import _read_restore_input_values, _restore_script_tag


def _render_dep_to_head(dep: HTMLDependency) -> str:
    """Render an HTMLDependency to the HTML it would inject into <head>."""
    rendered = TagList(dep).tagify().render()
    head_html = "".join(
        d.as_html_tags().get_html_string() for d in rendered["dependencies"]
    )
    return head_html + rendered["html"]


def test_read_restore_input_values_returns_underlying_dict() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello", "num": 42})
    assert _read_restore_input_values(ctx) == {"foo": "hello", "num": 42}


def test_read_restore_input_values_does_not_mark_pending() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    _read_restore_input_values(ctx)
    # No keys should be pending — we only inspected.
    assert ctx.input._pending == set()


def test_read_restore_input_values_empty() -> None:
    ctx = RestoreContext()
    # Default RestoreContext has empty RestoreInputSet
    assert _read_restore_input_values(ctx) == {}


def test_restore_script_tag_no_context_returns_none() -> None:
    # No active RestoreContext at all.
    assert _restore_script_tag() is None


def test_restore_script_tag_empty_input_returns_none() -> None:
    ctx = RestoreContext()  # default: empty RestoreInputSet
    with restore_context_cm(ctx):
        assert _restore_script_tag() is None


def test_restore_script_tag_emits_head_content_with_json() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello", "num": 42})
    with restore_context_cm(ctx):
        dep = _restore_script_tag()

    assert dep is not None
    assert isinstance(dep, HTMLDependency)
    head_html = _render_dep_to_head(dep)
    # The script body sets window.shinyreact._restore via JSON.parse.
    assert "window.shinyreact" in head_html
    assert "_restore" in head_html
    # Round-trip the embedded JSON: extract the JSON.parse('...') argument.
    match = re.search(r"JSON\.parse\('(.*)'\)", head_html)
    assert match is not None
    parsed = json.loads(match.group(1))
    assert parsed == {"foo": "hello", "num": 42}


def test_restore_script_tag_escapes_closing_script_tag() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "</script><script>alert(1)</script>"})
    with restore_context_cm(ctx):
        dep = _restore_script_tag()
    assert dep is not None
    head_html = _render_dep_to_head(dep)
    # The literal "</script>" sequence inside the JSON payload must be escaped
    # so the browser does not see it as ending the script. The escaping replaces
    # "</" with "<\/", so no unescaped "</script" appears INSIDE the JSON.parse call.
    json_start = head_html.index("JSON.parse('")
    # Allow only ONE actual </script> (the one closing our injected tag).
    assert head_html.count("</script>") == 1


def test_restore_script_tag_does_not_mark_pending() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        _restore_script_tag()
        # restore_input() inside the same context should still see "hello",
        # because _restore_script_tag did not mark "foo" as pending.
        from shiny.bookmark._restore_state import RestoreInputSet as _RIS  # noqa: F401
        from shiny.module import ResolvedId

        assert ctx.input.get(ResolvedId("foo")) == "hello"
