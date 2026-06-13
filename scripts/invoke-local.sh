#!/usr/bin/env bash
set -euo pipefail

FUNCTION="${1:-}"
PAYLOAD="${2:-'{}'}"

if [ -z "$FUNCTION" ]; then
  echo "Usage: $0 <function-name> [payload-json]"
  echo "  e.g.: $0 panpan-dev-api '{\"rawPath\":\"/checkout\"}'"
  exit 1
fi

aws lambda invoke \
  --function-name "$FUNCTION" \
  --payload "$PAYLOAD" \
  --cli-binary-format raw-in-base64-out \
  /dev/stdout
