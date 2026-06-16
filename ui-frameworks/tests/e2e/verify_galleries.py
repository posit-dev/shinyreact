#!/usr/bin/env python
"""End-to-end smoke test for the ui-frameworks gallery apps.

Static checks (build / import / R CMD check / ruff) don't mount the React tree or
run a Shiny session, so they miss runtime crashes (see issue #166). This script
serves each Python gallery, drives it headless, and fails if EITHER side errors:

  * client  — a React error (pageerror / console.error) that blanks the output
  * server  — a Python traceback in the Shiny log (render/reactive exception)

It also guards gallery parity (the shadcn Python/R galleries must declare the
same tabs) so the R gallery can't silently drift out of date.

Run:  uv run python ui-frameworks/tests/e2e/verify_galleries.py
Requires playwright + chromium:
  uv pip install playwright && uv run python -m playwright install chromium
"""

from __future__ import annotations

import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[3]
SHINY = shutil.which("shiny") or "shiny"

# Each target: the app to serve, the labels to click in order (tabs then action
# buttons), and the minimum number of rendered elements expected at the end.
TARGETS = [
    {
        "name": "shadcn gallery-py",
        "app": "ui-frameworks/shadcn/examples/gallery-py/app.py",
        "clicks": [
            "Inputs",
            "Display",
            "Actions",
            "Overlays",
            "Navigation",
            "Layout",
            "Feedback",
            "Show toast",
        ],
        "min_els": 20,
    },
    {
        "name": "shadcn component-explorer",
        "app": "ui-frameworks/shadcn/examples/shinyreact-shadcn/app.py",
        "clicks": ["Inputs", "Display", "Overlays", "Navigation", "Layout", "Feedback"],
        "min_els": 20,
    },
    {
        "name": "mui gallery-py",
        "app": "ui-frameworks/mui/examples/gallery-py/app.py",
        "clicks": [],  # one page, no tabs — the typography crash blanks it on load
        "min_els": 100,
    },
]

# Lines in the server log that indicate a real crash (a bare "connection closed"
# at the end is normal — the browser just disconnected).
TRACEBACK_RE = re.compile(
    r"traceback|attributeerror|not iterable|unhandled error|reactiveerror|"
    r"error in |valueerror|typeerror|keyerror",
    re.IGNORECASE,
)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(app: str, port: int, log_path: Path):
    log = open(log_path, "w")
    proc = subprocess.Popen(
        [SHINY, "run", "--port", str(port), str(REPO / app)],
        stdout=log,
        stderr=subprocess.STDOUT,
        cwd=str(REPO),
    )
    # Wait for startup.
    deadline = time.time() + 40
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited early; log:\n{log_path.read_text()}")
        if "Application startup complete" in log_path.read_text():
            return proc
        time.sleep(0.3)
    raise RuntimeError(f"server did not start in time; log:\n{log_path.read_text()}")


def drive(port: int, clicks: list[str]):
    pe, ce = [], []
    sel = "[data-slot], [class*=Mui], button, input"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.on("pageerror", lambda e: pe.append(str(e)))
        pg.on("console", lambda m: ce.append(m.text) if m.type == "error" else None)
        pg.goto(f"http://localhost:{port}", wait_until="networkidle")
        pg.wait_for_timeout(3000)
        # Track the MAX elements seen across views — the last tab/category
        # clicked may legitimately be small (e.g. Feedback has one component).
        max_els = len(pg.query_selector_all(sel))
        for label in clicks:
            el = pg.query_selector(
                f"[role=tab]:has-text('{label}'), button:has-text('{label}')"
            )
            if el:
                el.click()
                pg.wait_for_timeout(1500)
                max_els = max(max_els, len(pg.query_selector_all(sel)))
        b.close()
    return pe, ce, max_els


def server_errors(log_path: Path) -> list[str]:
    return [
        ln
        for ln in log_path.read_text().splitlines()
        if TRACEBACK_RE.search(ln) and not ln.startswith("INFO:")
    ]


def check_target(t: dict) -> list[str]:
    port = free_port()
    log_path = REPO / f".gallery-e2e-{port}.log"
    proc = serve(t["app"], port, log_path)
    try:
        pe, ce, els = drive(port, t["clicks"])
        srv = server_errors(log_path)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_path.unlink(missing_ok=True)

    problems = []
    if pe:
        problems.append(f"page errors: {pe[:3]}")
    if ce:
        problems.append(f"console errors: {ce[:3]}")
    if srv:
        problems.append(f"server traceback: {srv[-3:]}")
    if els < t["min_els"]:
        problems.append(f"only {els} elements rendered (expected >= {t['min_els']})")
    print(f"  {'FAIL' if problems else 'ok  '}  {t['name']:28s} els={els}")
    return [f"{t['name']}: {p}" for p in problems]


def check_parity() -> list[str]:
    """shadcn Python and R galleries must declare the same tab set."""

    def tabs(path: str, fn: str) -> set[str]:
        text = (REPO / path).read_text()
        return set(re.findall(rf'{fn}\(\s*"([a-z_]+)"', text))

    py = tabs("ui-frameworks/shadcn/examples/gallery-py/app.py", "sc.tab")
    r = tabs("ui-frameworks/shadcn/examples/gallery-r/app.R", "shadcn_tab")
    tag = "FAIL" if py != r else "ok  "
    print(f"  {tag}  shadcn gallery parity  py={len(py)} r={len(r)}")
    if py != r:
        return [f"gallery parity: py tabs {sorted(py)} != r tabs {sorted(r)}"]
    return []


def main() -> int:
    print("Verifying ui-frameworks galleries (serve + headless drive):")
    failures: list[str] = []
    for t in TARGETS:
        try:
            failures += check_target(t)
        except Exception as e:  # noqa: BLE001 — surface any harness failure as a test failure
            print(f"  FAIL  {t['name']:28s} harness error: {e}")
            failures.append(f"{t['name']}: harness error: {e}")
    failures += check_parity()

    print()
    if failures:
        print(f"FAILED ({len(failures)} problem(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All galleries rendered cleanly (no client or server errors).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
