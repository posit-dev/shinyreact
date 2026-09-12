import subprocess
import sys
from pathlib import Path

from shiny.express import input
from shinyreact import reactive_output, set_react_page

# The bundle is gitignored, so a fresh clone has no `www/` at all and Shiny
# fails to mount it. Build it on first run instead of greeting the reader with
# a stack trace. `npm run dev` overwrites www/ui.js with the dev stub, which is
# the HMR workflow this example is about -- see the README.
_app_dir = Path(__file__).parent
if not (_app_dir / "www" / "ui.js").exists():
    print("www/ui.js not found -- building the client bundle...", file=sys.stderr)
    # `@posit-dev/shinyreact` comes from npm, so this is an ordinary install --
    # nothing in the repo has to be built first.
    subprocess.run(["npm", "install"], cwd=_app_dir, check=True)
    subprocess.run(["npm", "run", "build"], cwd=_app_dir, check=True)

# npm tier: the client imports `@posit-dev/shinyreact` and bundles shinyreact.js
# itself, so the server must not serve it too -- two copies on one page. The
# `#shinyreact-config` tag is still emitted: it carries the protocol version
# and any bookmark restore payload.
set_react_page(shinyreact_js="client")


# `input.count()` is pushed from App.tsx via useShinyInput("count", ...); the
# `doubled` output is read there via useShinyOutputValue("doubled", ...).
@reactive_output
def doubled():
    # Echoes the client-pushed count, doubled — proves the Shiny round-trip
    # keeps working while you hot-edit the client.
    return input.count() * 2
