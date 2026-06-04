import json
import re

from htmltools import HTMLDependency, TagList, tags
from shinyreact._spec import Node, script_safe_json


def _render(node: Node) -> str:
    return str(TagList(node.tagify()))


def test_script_safe_json_escapes_dangerous_chars_losslessly():
    # Every character that is dangerous inside an HTML <script> element or
    # illegal unescaped in a JS string literal must be \\uXXXX-escaped, and the
    # result must JSON.parse (json.loads) back to the original.
    raw = "</script><!-- -->    a & b"
    out = script_safe_json({"x": raw})
    # No raw dangerous character survives in the serialized text.
    for char in ("<", ">", "&", " ", " "):
        assert char not in out, f"{char!r} should have been escaped"
    # The escape is lossless.
    assert json.loads(out) == {"x": raw}


def test_script_safe_json_uses_unicode_escapes():
    out = script_safe_json("</script>")
    assert out == '"\\u003c/script\\u003e"'


def test_tagify_returns_fully_tagified_value_when_nested_in_a_tag():
    # htmltools requires `.tagify()` to return a fully-tagified value; when a
    # parent Tag tagifies its children it raises TypeError otherwise. This is
    # the path exercised by `page_react(tags.div(Node(...)))`.
    ui = tags.div(Node(type="Badge", props={"text": "x"}), id="chrome")
    html = str(ui.tagify())  # must not raise
    assert 'class="shinyreact-static"' in html


def test_tagify_emits_static_mount_with_child_script():
    node = Node(type="Chart", props={"data": [1, 2]})
    html = _render(node)

    # A static mount div (distinct class) containing a JSON script.
    assert 'class="shinyreact-static"' in html
    script_m = re.search(
        r'<script type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert script_m, html
    payload = json.loads(script_m.group(1))
    assert payload == {
        "type": "react",
        "name": "Chart",
        "props": {"data": [1, 2]},
        "children": [],
    }


def test_tagify_mount_has_no_id_and_is_not_an_output():
    html = _render(Node(type="Chart"))
    assert "shinyreact-output" not in html
    # The static mount div specifically carries no id attribute.
    div_m = re.search(r'<div[^>]*class="shinyreact-static"[^>]*>', html)
    assert div_m, html
    assert " id=" not in div_m.group(0)


def test_tagify_includes_harvested_dependency():
    dep = HTMLDependency(name="mydep", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep, "hello"])
    deps = node.tagify().get_dependencies()
    names = {d.name for d in deps}
    # Both shinyreact's own dep and the harvested one are present.
    assert "shinyreact" in names
    assert "mydep" in names


def test_tagify_escapes_script_breakout():
    from htmltools import HTML

    node = Node(type="Card", props={}, children=[HTML("</script><script>x</script>")])
    html = _render(node)
    # The breakout payload's "</script>" is escaped, so it cannot close the
    # inline-spec <script> early — only the wrapper's real closing tag remains.
    assert "</script><script>x" not in html
    # The inline script's content round-trips back to the original wire node.
    script_m = re.search(
        r'<script type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert script_m, html
    payload = json.loads(script_m.group(1))
    assert payload == {
        "type": "react",
        "name": "Card",
        "props": {},
        "children": [{"type": "html", "html": "</script><script>x</script>"}],
    }
