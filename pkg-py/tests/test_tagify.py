import json
import re

from htmltools import HTMLDependency, TagList
from shinyreact._spec import Node


def _render(node: Node) -> str:
    return str(TagList(node.tagify()))


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
    # The static mount carries no id attribute.
    div_m = re.search(r"<div[^>]*>", html)
    assert div_m
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
    # The "<" of the embedded </script> is escaped, so it cannot close the
    # inline-spec <script> early.
    assert "</script><script>x" not in html
    assert "\\u003c/script>" in html
