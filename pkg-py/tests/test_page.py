from htmltools import HTMLDependency, Tag
from shinyreact._page import page_bare, page_react


def test_page_bare_returns_tag():
    result = page_bare()
    assert isinstance(result, Tag)


def test_page_bare_with_title():
    result = page_bare(title="Test Page")
    rendered = str(result.tagify())
    assert "Test Page" in rendered


def test_page_bare_no_shinyreact_dep():
    result = page_bare()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyreact" not in dep_names


def test_page_react_returns_tag():
    result = page_react()
    assert isinstance(result, Tag)


def test_page_react_emits_no_root_div():
    result = page_react()
    rendered = str(result.tagify())
    assert 'id="root"' not in rendered


def test_page_react_renders_output_placeholder():
    """The app.py pattern works without a #root div."""
    from shinyreact import output_react

    result = page_react(output_react("hello"))
    rendered = str(result.tagify())
    assert "shinyreact-output" in rendered
    assert 'id="hello"' in rendered


def test_page_react_includes_shinyreact_dep():
    result = page_react()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyreact" in dep_names


def test_page_react_accepts_htmldep_via_args():
    dep = HTMLDependency(
        "my-app", "1.0.0", source={"subdir": "/tmp"}, script={"src": "app.js"}
    )
    result = page_react(dep)
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "my-app" in dep_names
    assert "shinyreact" in dep_names


def test_page_react_no_js_file_css_file_params():
    """page_react() no longer accepts js_file or css_file."""
    import inspect

    sig = inspect.signature(page_react)
    param_names = list(sig.parameters.keys())
    assert "js_file" not in param_names
    assert "css_file" not in param_names


def test_page_react_dep_falls_back_to_cwd_without_file(tmp_path, monkeypatch):
    """page_react_dep() falls back to CWD when the caller has no __file__."""
    (tmp_path / "main.js").write_text("// ...")
    monkeypatch.chdir(tmp_path)

    captured: dict[str, HTMLDependency] = {}
    src = (
        "from shinyreact._page import page_react_dep\n"
        "captured['dep'] = page_react_dep()\n"
    )
    exec(compile(src, "<test>", "exec"), {"captured": captured})

    dep = captured["dep"]
    assert isinstance(dep, HTMLDependency)
    # Source resolved to CWD, so dep_name is the CWD's basename.
    assert dep.name == tmp_path.name
