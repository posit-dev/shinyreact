"""Build hook: bundle the shared www/ assets into the package at build time.

The built JS/CSS live in the shared ui-frameworks/shadcn/www/ directory (one
copy feeds the JS, Python, and R packages). Rather than commit a duplicate, this
hook copies them into src/shinyshadcn/www/ when building, so both the sdist and
the wheel ship the assets. The copied directory is gitignored; a source checkout
used via sys.path.insert relies on _dep()'s fallback to the shared directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        shared_www = root.parent / "www"
        dest = root / "src" / "shinyshadcn" / "www"
        # When building from an sdist, the shared dir is gone but the assets are
        # already vendored under src/; nothing to copy.
        if not shared_www.is_dir():
            return
        dest.mkdir(parents=True, exist_ok=True)
        for name in ("shadcn.js", "style.css"):
            asset = shared_www / name
            if asset.exists():
                shutil.copy2(asset, dest / name)
