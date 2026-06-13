#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-all}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
mkdir -p "$DIST"

build_layer() {
  echo "Building shared layer..."
  TMP=$(mktemp -d)
  mkdir -p "$TMP/python"
  cp -r "$ROOT/lambdas/shared/"* "$TMP/python/"
  (cd "$TMP" && zip -r "$DIST/shared-layer.zip" python/)
  rm -rf "$TMP"
  echo "  -> dist/shared-layer.zip"
}

build_lambda() {
  local name="$1"
  echo "Building $name lambda..."
  TMP=$(mktemp -d)
  cp -r "$ROOT/lambdas/$name/"* "$TMP/"
  if [ -f "$TMP/requirements.txt" ]; then
    pip install -q -r "$TMP/requirements.txt" -t "$TMP/"
  fi
  (cd "$TMP" && zip -r "$DIST/$name.zip" . -x "*.pyc" -x "__pycache__/*")
  rm -rf "$TMP"
  echo "  -> dist/$name.zip"
}

case "$TARGET" in
  shared-layer) build_layer ;;
  api)          build_lambda api ;;
  send-email)   build_lambda send-email ;;
  all)
    build_layer
    build_lambda api
    build_lambda send-email
    ;;
  *)
    echo "Unknown target: $TARGET"
    echo "Usage: $0 [shared-layer|api|send-email|all]"
    exit 1
    ;;
esac
