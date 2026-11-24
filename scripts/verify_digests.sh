#!/bin/bash
# verify_digests.sh — verify SHA-256 digests of every pack file listed in
# SHA256SUMS. Exits 0 only if every digest matches.
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PACK_ROOT" || exit 1
if [ ! -f SHA256SUMS ]; then
  echo "SHA256SUMS missing"
  exit 1
fi
sha256sum -c SHA256SUMS
