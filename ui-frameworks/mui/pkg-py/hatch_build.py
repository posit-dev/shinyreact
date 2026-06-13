"""Build hook: bundle the shared www/ asset into the package at build time.

The built JS lives in the shared ui-frameworks/mui/www/ directory. Rather than
commit a duplicate, this hook copies it into src/shinymui/www/ when building, so
both the sdist and the wheel ship it. The copied directory is gitignored; a
source checkout used via sys.path.insert relies on _dep()'s fallback to the
shared directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        shared_www = root.parent / "www"
        dest = root / "src" / "shinymui" / "www"
        if not shared_www.is_dir():
            return
        dest.mkdir(parents=True, exist_ok=True)
        for name in ("mui.js",):
            asset = shared_www / name
            if asset.exists():
                shutil.copy2(asset, dest / name)
