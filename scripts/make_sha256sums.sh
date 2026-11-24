#!/bin/bash
# make_sha256sums.sh — regenerate SHA256SUMS over every pack file except
# SHA256SUMS itself, the internal-only PACK-READY.md, and the
# internal-only research/ directory (never shipped, never counted).
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PACK_ROOT" || exit 1
find . -type f \
  ! -name SHA256SUMS ! -name PACK-READY.md ! -name '.DS_Store' \
  ! -path './.git/*' ! -path './research/*' ! -path '*/__pycache__/*' \
  | sort | xargs sha256sum > SHA256SUMS
wc -l SHA256SUMS
