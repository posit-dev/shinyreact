#!/usr/bin/env bash
# Download all shadcn/ui (new-york-v4) component source files.
#
# Output: js/src/components-src/*.tsx  (raw TypeScript, untouched)
# Requires: gh CLI, authenticated (gh auth status)
#
# Usage (run from anywhere in the repo):
#   bash ui-frameworks/shadcn/download-components.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$SCRIPT_DIR/js/src/components-src"
REGISTRY="repos/shadcn-ui/ui/contents/apps/v4/registry/new-york-v4/ui"

mkdir -p "$OUT_DIR"

echo "Fetching component list..."
COMPONENTS=$(gh api "$REGISTRY" --jq '.[] | select(.name | endswith(".tsx")) | .name')
TOTAL=$(echo "$COMPONENTS" | wc -l | tr -d ' ')
echo "Found $TOTAL components."
echo ""

COUNT=0
for filename in $COMPONENTS; do
  COUNT=$((COUNT + 1))
  name="${filename%.tsx}"
  printf "[%d/%d] %s\n" "$COUNT" "$TOTAL" "$name"
  gh api "$REGISTRY/$filename" --jq '.content' \
    | tr -d '\n' \
    | base64 -d \
    > "$OUT_DIR/$name.tsx"
done

echo ""
echo "Done. $COUNT files saved to:"
echo "  $OUT_DIR/"
echo ""
echo "These are raw shadcn TypeScript source files."
echo "To wrap one for shinyreact, use /scaffold-component."
