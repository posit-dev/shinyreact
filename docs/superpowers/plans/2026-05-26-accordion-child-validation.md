# Accordion Child Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve #106 by validating that `accordion` children are `accordion_panel` instances, raising a clear `TypeError` at insertion (`__init__`, `append`) and as a defense-in-depth check at `tagify()`.

**Architecture:** A private module-level helper `_check_panel(child)` raises `TypeError` if `child` is not an `accordion_panel`. It is called from three sites in `accordion`: a positional-arg loop in `__init__` (Core form), an overridden `append()` (Express `with`-block path + direct calls), and a loop at the top of `tagify()` (catches direct mutation of `children`). The four existing `# type: ignore[union-attr]` comments in `tagify()` are removed since the loop narrows the type. The same change is applied independently to `shinyui` and `shinyuiclassonly`.

**Tech Stack:** Python 3.10+, htmltools `TagChild`, pytest, pyright.

**Spec:** `docs/superpowers/specs/2026-05-26-accordion-child-validation-design.md`

---

## File Structure

**Modify:**
- `pkg-py/src/shinyui/_accordion.py` — add `_check_panel` helper, validate in `__init__`, override `append`, add loop in `tagify`, drop four `# type: ignore[union-attr]` comments.
- `pkg-py/src/shinyuiclassonly/_accordion.py` — identical changes.
- `pkg-py/tests/shinyui/test_accordion.py` — append six new tests.
- `pkg-py/tests/shinyuiclassonly/test_accordion.py` — append six new tests (mirrored).

No new files. No changes to `accordion_panel`, `AllowsChildren`, or any other component.

---

## Task 1: shinyui accordion — add failing tests

**Files:**
- Modify: `pkg-py/tests/shinyui/test_accordion.py` (append at end)

- [ ] **Step 1: Append the six tests at the bottom of `pkg-py/tests/shinyui/test_accordion.py`**

Add these imports near the top of the file if not already present (the file currently has `import pytest` and the shinyui imports — `sys` is new):

```python
import sys
```

Append at the bottom:

```python
def test_init_rejects_non_panel_positional_arg():
    """Core form: bare string positional arg raises TypeError at construction."""
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        accordion("some text", id="acc")  # type: ignore[arg-type]


def test_append_rejects_non_panel():
    """Direct .append() of a non-panel child raises TypeError."""
    a = accordion(id="acc")
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.append("text")  # type: ignore[arg-type]


def test_express_with_block_rejects_bare_string():
    """Express form: bare string inside `with accordion(...)` raises TypeError.

    This validates the displayhook -> dispatch_to_active_parent -> append
    path that is the real-world hazard described in #106.
    """
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        with accordion(id="acc"):
            sys.displayhook("Some descriptive text")


def test_tagify_rejects_directly_mutated_children():
    """Defense-in-depth: bypassing __init__/append still fails at tagify()."""
    a = accordion(accordion_panel("A"), id="acc")
    a.children.append("text")  # bypass the guards
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.tagify()


def test_error_message_names_offending_type():
    """The TypeError includes the offending child's type name."""
    a = accordion(id="acc")
    with pytest.raises(TypeError, match=r"got str\b"):
        a.append("text")  # type: ignore[arg-type]


def test_well_formed_accordion_still_tagifies():
    """Regression guard: validation does not break the happy path."""
    a = accordion(
        accordion_panel("A", "body-a"),
        accordion_panel("B", "body-b"),
        id="acc",
    )
    tag = a.tagify()
    assert tag.attrs.get("id") == "acc"
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run:

```bash
uv run pytest pkg-py/tests/shinyui/test_accordion.py -v -k "rejects or names_offending or well_formed"
```

Expected: the five "rejects/names_offending" tests fail (currently `AttributeError` at render or no error at insertion); `test_well_formed_accordion_still_tagifies` passes (existing behavior).

- [ ] **Step 3: Commit the failing tests**

```bash
git add pkg-py/tests/shinyui/test_accordion.py
git commit -m "test(shinyui): failing tests for #106 accordion child validation"
```

---

## Task 2: shinyui accordion — implement validation

**Files:**
- Modify: `pkg-py/src/shinyui/_accordion.py`

- [ ] **Step 1: Add the `_check_panel` helper near the top of the module**

Insert after the existing `_MISSING = object()` line (around line 21):

```python
def _check_panel(child: object) -> None:
    if not isinstance(child, accordion_panel):
        raise TypeError(
            f"accordion children must be accordion_panel instances, "
            f"got {type(child).__name__}"
        )
```

(Note: `accordion_panel` is already imported at the top of the file.)

- [ ] **Step 2: Validate positional args in `__init__`**

In the runtime `__init__` (currently around lines 135–150), insert a validation loop at the top of the body, before `self._open = open`:

```python
    def __init__(
        self,
        *args: accordion_panel,
        id: str,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None:
        for child in args:
            _check_panel(child)
        self._open = open
        self.multiple = multiple
        self.class_ = class_
        self.width = width
        self.height = height
        super().__init__(*args, id=id)
```

- [ ] **Step 3: Override `append()` on `accordion`**

`AllowsChildren.append` returns `Self` — preserve that contract. Add this method to the `accordion` class. Place it directly after `__init__` and before `open_panels` (around line 152):

```python
    def append(self, child: TagChild) -> Self:
        _check_panel(child)
        return super().append(child)
```

Add the two imports needed for the annotations at the top of the file:

```python
from htmltools import Tag, TagChild
from typing_extensions import Self
```

(The existing import line `from htmltools import Tag` becomes `from htmltools import Tag, TagChild`. `typing_extensions.Self` is a new import.)

- [ ] **Step 4: Add the defense-in-depth loop at the top of `tagify()` and drop the type: ignore comments**

Replace the `tagify()` body (currently lines 157–183) with:

```python
    def tagify(self) -> Tag:
        import shiny.ui as _sui

        # `shiny.ui.accordion` does an explicit isinstance(panel, AccordionPanel)
        # check on its positional args and rejects rendered Tags. So instead of
        # calling child.tagify() (which now returns Tag), we read each child's
        # stored state and build shiny's AccordionPanel wrapper inline. A single
        # .tagify() on the outer result lets htmltools' walker resolve any
        # remaining Tagifiable descendants (e.g. an input_slider inside a panel).
        for child in self.children:
            _check_panel(child)

        panels = [
            _sui.accordion_panel(
                child.title,
                *child.children,
                value=child._value,
                icon=child.icon,
            )
            for child in self.children
        ]
        return _sui.accordion(
            *panels,
            id=self.id,
            open=self._open,
            multiple=self.multiple,
            class_=self.class_,
            width=self.width,
            height=self.height,
        ).tagify()
```

(Note: the four `# type: ignore[union-attr]` comments on `child.title`, `*child.children`, `value=child._value`, `icon=child.icon` are gone. The preceding `for child in self.children: _check_panel(child)` loop narrows pyright's view of `child` to `accordion_panel`.)

- [ ] **Step 5: Run the new tests to verify they pass**

Run:

```bash
uv run pytest pkg-py/tests/shinyui/test_accordion.py -v
```

Expected: all tests in `test_accordion.py` pass, including the six added in Task 1.

- [ ] **Step 6: Run pyright on the file to confirm no new type errors and the `# type: ignore` removals don't cause regressions**

Run:

```bash
make py-check-types
```

Expected: no new errors. If pyright reports "Unnecessary `# type: ignore`" was previously suppressed and is now correctly removed, that's the change we wanted.

- [ ] **Step 7: Commit**

```bash
git add pkg-py/src/shinyui/_accordion.py
git commit -m "fix(shinyui): validate accordion children are accordion_panel (#106)

accordion.tagify() previously accessed .title/.children/._value/.icon
on every child, but list[TagChild] permits arbitrary values. Validate
in __init__ (positional), append() (Express displayhook path), and
tagify() (defense in depth) and raise TypeError with the offending
type name. Removes four # type: ignore[union-attr] suppressions in
tagify()."
```

---

## Task 3: shinyuiclassonly accordion — add failing tests

**Files:**
- Modify: `pkg-py/tests/shinyuiclassonly/test_accordion.py` (append at end)

- [ ] **Step 1: Read the current test file to confirm import style**

Run:

```bash
head -20 pkg-py/tests/shinyuiclassonly/test_accordion.py
```

Confirm the imports use `from shinyuiclassonly._accordion import accordion` and `from shinyuiclassonly._accordion_panel import accordion_panel` (or equivalents). If they differ, adapt the test snippet below to match.

- [ ] **Step 2: Append the six mirrored tests at the bottom of the file**

Add this import near the top if not already present:

```python
import sys
```

Append at the bottom:

```python
def test_init_rejects_non_panel_positional_arg():
    """Core form: bare string positional arg raises TypeError at construction."""
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        accordion("some text", id="acc")  # type: ignore[arg-type]


def test_append_rejects_non_panel():
    """Direct .append() of a non-panel child raises TypeError."""
    a = accordion(id="acc")
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.append("text")  # type: ignore[arg-type]


def test_express_with_block_rejects_bare_string():
    """Express form: bare string inside `with accordion(...)` raises TypeError."""
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        with accordion(id="acc"):
            sys.displayhook("Some descriptive text")


def test_tagify_rejects_directly_mutated_children():
    """Defense-in-depth: bypassing __init__/append still fails at tagify()."""
    a = accordion(accordion_panel("A"), id="acc")
    a.children.append("text")
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.tagify()


def test_error_message_names_offending_type():
    """The TypeError includes the offending child's type name."""
    a = accordion(id="acc")
    with pytest.raises(TypeError, match=r"got str\b"):
        a.append("text")  # type: ignore[arg-type]


def test_well_formed_accordion_still_tagifies():
    """Regression guard: validation does not break the happy path."""
    a = accordion(
        accordion_panel("A", "body-a"),
        accordion_panel("B", "body-b"),
        id="acc",
    )
    tag = a.tagify()
    assert tag.attrs.get("id") == "acc"
```

(If `pytest` is not already imported in this test file, add `import pytest` at the top.)

- [ ] **Step 3: Run the new tests to verify they fail**

Run:

```bash
uv run pytest pkg-py/tests/shinyuiclassonly/test_accordion.py -v -k "rejects or names_offending or well_formed"
```

Expected: the five "rejects/names_offending" tests fail; `test_well_formed_accordion_still_tagifies` passes.

- [ ] **Step 4: Commit the failing tests**

```bash
git add pkg-py/tests/shinyuiclassonly/test_accordion.py
git commit -m "test(shinyuiclassonly): failing tests for #106 accordion child validation"
```

---

## Task 4: shinyuiclassonly accordion — implement validation

**Files:**
- Modify: `pkg-py/src/shinyuiclassonly/_accordion.py`

- [ ] **Step 1: Add the `_check_panel` helper near the top of the module**

Insert after the `from ._roles import UiLayout` import block (around line 19), before `class accordion`:

```python
def _check_panel(child: object) -> None:
    if not isinstance(child, accordion_panel):
        raise TypeError(
            f"accordion children must be accordion_panel instances, "
            f"got {type(child).__name__}"
        )
```

(`accordion_panel` is already imported.)

- [ ] **Step 2: Validate positional args in `__init__`**

In the runtime `__init__` (currently around lines 55–71), insert a validation loop at the top of the body, before `self.id = id`:

```python
    def __init__(
        self,
        *args: accordion_panel,
        id: Optional[str] = None,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None:
        for child in args:
            _check_panel(child)
        self.id = id
        self._open = open
        self.multiple = multiple
        self.class_ = class_
        self.width = width
        self.height = height
        super().__init__(*args)
```

- [ ] **Step 3: Override `append()` on `accordion`**

Add this method to the `accordion` class, directly after `__init__` and before `tagify`:

```python
    def append(self, child: TagChild) -> Self:
        _check_panel(child)
        return super().append(child)
```

Update the imports at the top of the file. Change:

```python
from htmltools import Tag
```

to:

```python
from htmltools import Tag, TagChild
from typing_extensions import Self
```

- [ ] **Step 4: Add the defense-in-depth loop at the top of `tagify()` and drop the type: ignore comments**

Replace the `tagify()` body (currently lines 73–95) with:

```python
    def tagify(self) -> Tag:
        import shiny.ui as _sui

        # shiny.ui.accordion rejects pre-rendered Tags (isinstance check on
        # AccordionPanel). Rebuild wrappers from each child's stored state.
        for child in self.children:
            _check_panel(child)

        panels = [
            _sui.accordion_panel(
                child.title,
                *child.children,
                value=child._value,
                icon=child.icon,
            )
            for child in self.children
        ]
        return _sui.accordion(
            *panels,
            id=self.id,
            open=self._open,
            multiple=self.multiple,
            class_=self.class_,
            width=self.width,
            height=self.height,
        ).tagify()
```

- [ ] **Step 5: Run the new tests to verify they pass**

Run:

```bash
uv run pytest pkg-py/tests/shinyuiclassonly/test_accordion.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Run pyright**

Run:

```bash
make py-check-types
```

Expected: no new errors.

- [ ] **Step 7: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_accordion.py
git commit -m "fix(shinyuiclassonly): validate accordion children are accordion_panel (#106)

Mirror the shinyui fix: validate in __init__, append, and tagify;
remove four # type: ignore[union-attr] suppressions in tagify()."
```

---

## Task 5: Final verification

- [ ] **Step 1: Run the full Python check suite**

Run:

```bash
make py-check
```

Expected: format check passes, type check passes, all tests pass.

- [ ] **Step 2: Confirm no stray `# type: ignore[union-attr]` remain in the two `_accordion.py` files**

Run:

```bash
grep -n "type: ignore\[union-attr\]" pkg-py/src/shinyui/_accordion.py pkg-py/src/shinyuiclassonly/_accordion.py
```

Expected: no matches (both files are clean).

- [ ] **Step 3: If anything failed, fix it with a new follow-up commit**

If `make py-check` reveals a formatter complaint or a missed import, edit the offending file and create a new commit (`fix:` prefix). If a test failure surfaces in an unrelated file, investigate — the validation should be inert for non-accordion code paths.
