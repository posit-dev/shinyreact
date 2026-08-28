"""Guards the client/server boundary surface against silent growth.

`protocol/surface.json` lists every name that crosses the boundary, next to the
protocol version that describes it. This asserts the Python side matches: the
input handlers shinyreact actually registers with shiny, the custom message
types it sends, and the version constant.

It exists because the surface already grew unnoticed — #221 added
`shinyreact.init` and `shinyreact-deps` while all three protocol constants still
documented "exactly three" boundary shapes (issue #232). Mirrored by
`pkg-r/tests/testthat/test-protocol-surface.R` and
`pkg-js/src/__tests__/protocol-surface.test.ts`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import shinyreact  # noqa: F401  (import registers the input handlers)
from shiny.input_handler import input_handlers
from shinyreact._protocol import PROTOCOL_VERSION

_REPO_ROOT = Path(__file__).parents[2]
_PKG_SRC = _REPO_ROOT / "pkg-py" / "src" / "shinyreact"
_SURFACE = json.loads((_REPO_ROOT / "protocol" / "surface.json").read_text())


def test_registered_input_handlers_match_the_manifest() -> None:
    # Every shinyreact.* handler shiny knows about, straight from the registry
    # rather than from a list in this file — a new @input_handlers.add in the
    # package shows up here whether or not anyone remembered this test.
    registered = sorted(k for k in input_handlers if k.startswith("shinyreact."))
    assert registered == sorted(_SURFACE["inputHandlers"]), (
        "shinyreact's registered input handlers no longer match "
        "protocol/surface.json. Add the new name there and decide whether the "
        "protocol version must change (#232)."
    )


def test_custom_message_types_match_the_manifest() -> None:
    # Source scan: the type is a literal at the send site, and the alternative
    # (asserting only what a test happens to exercise) is what let the surface
    # grow silently in the first place.
    sent = set()
    for path in _PKG_SRC.rglob("*.py"):
        for match in re.finditer(
            r"send_custom_message\(\s*[\"']([^\"']+)[\"']", path.read_text()
        ):
            sent.add(match.group(1))

    assert sent, "found no send_custom_message() calls to check — did the scan break?"
    unlisted = sent - set(_SURFACE["customMessages"])
    assert not unlisted, (
        f"custom message type(s) {sorted(unlisted)} are not in "
        "protocol/surface.json (#232)"
    )


def test_config_tag_id_matches_the_manifest() -> None:
    ids = set()
    for path in _PKG_SRC.rglob("*.py"):
        for match in re.finditer(r"id=\"(shinyreact[^\"]*)\"", path.read_text()):
            ids.add(match.group(1))

    assert ids, "found no shinyreact DOM ids to check — did the scan break?"
    assert ids <= set(_SURFACE["domIds"]), (
        f"DOM id(s) {sorted(ids - set(_SURFACE['domIds']))} are not in "
        "protocol/surface.json (#232)"
    )


def test_protocol_version_matches_the_manifest() -> None:
    assert PROTOCOL_VERSION == _SURFACE["protocolVersion"]
