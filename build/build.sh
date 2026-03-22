#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

VERSION=$(python3 -c "from lca import __version__; print(__version__)")
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
[[ "$ARCH" == "aarch64" ]] && ARCH="arm64"
BINARY="dist/lca-${VERSION}-${OS}-${ARCH}"

echo "==> Building lca ${VERSION} for ${OS}/${ARCH}"

rm -rf build/pyinstaller-work dist/lca

pyinstaller \
  --distpath dist \
  --workpath build/pyinstaller-work \
  --noconfirm \
  build/lca.spec

mv dist/lca "$BINARY"

echo "==> Smoke test:"
"$BINARY" --version
"$BINARY" doctor

SIZE=$(du -sh "$BINARY" | cut -f1)
echo "==> Done: $BINARY ($SIZE)"
echo ""
echo "Install to PATH:"
echo "  sudo cp $BINARY /usr/local/bin/lca"
