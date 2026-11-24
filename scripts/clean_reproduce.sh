#!/bin/bash
# clean_reproduce.sh — full fresh-environment reproduction check, twice.
#
# Copies the pack to a throwaway directory, drops all shipped outputs
# and SHA256SUMS, re-runs every generation step from scratch via
# scripts/run_all.sh, and compares the fresh numbers with the shipped
# ones via scripts/compare_reproduce.py. The whole cycle runs TWICE
# (the task requires two fresh-clone reproductions); the first run's
# outputs are copied back as outputs/fresh-clone-* and the second
# run's as outputs/fresh-clone-2-*. Exits 0 only if every comparison
# check passes in both cycles.
#
# The fresh outputs are copied back into outputs/fresh-clone-* so the
# reproductions themselves are evidence. The reproduction logs are
# deterministic (no timestamps, no workdir paths) so SHA256SUMS stays
# stable across runs. Only deterministic comparisons are made: JSON
# deep-compare ignoring volatile fields, digest compare for logs after
# stripping timestamp lines; timing values are never compared
# absolutely.
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d /tmp/xchain-repro.XXXXXX)"
echo "clean_reproduce.sh workdir: $WORK"
mkdir -p "$WORK/shipped"
# Save the shipped outputs and fixtures for comparison.
if [ -d "$PACK_ROOT/outputs" ]; then
  cp -r "$PACK_ROOT/outputs" "$WORK/shipped/outputs"
fi
if [ -f "$PACK_ROOT/fixtures/source-hashes.json" ]; then
  mkdir -p "$WORK/shipped/fixtures"
  cp "$PACK_ROOT/fixtures/source-hashes.json" "$WORK/shipped/fixtures/"
fi
if [ -d "$PACK_ROOT/fixtures/source-excerpts" ]; then
  mkdir -p "$WORK/shipped/fixtures/source-excerpts"
  cp "$PACK_ROOT/fixtures/source-excerpts/"*.txt "$WORK/shipped/fixtures/source-excerpts/" 2>/dev/null || true
fi

run_cycle() {
  local cycle="$1" prefix="$2"
  echo "=== reproduction cycle $cycle ($prefix) ==="
  rm -rf "$WORK/pack"
  cp -r "$PACK_ROOT" "$WORK/pack"
  cd "$WORK/pack" || exit 1

  # Drop everything the generation steps produce, so the run is from scratch.
  rm -rf outputs
  mkdir -p outputs/derived
  rm -f SHA256SUMS
  rm -f run-manifest.json
  rm -f fixtures/source-hashes.json
  rm -f fixtures/source-excerpts/*.txt

  echo "--- cycle $cycle step 1: run_all.sh (fresh copy) ---"
  bash scripts/run_all.sh || { echo "run_all.sh FAILED in fresh copy (cycle $cycle)"; exit 1; }
  echo "--- cycle $cycle step 2: compare with shipped ---"
  python3 scripts/compare_reproduce.py "$WORK/shipped" "$WORK/pack" \
    || { echo "compare_reproduce.py FAILED (cycle $cycle)"; exit 1; }

  echo "--- cycle $cycle step 3: copy fresh outputs back as ${prefix} evidence ---"
  for f in outputs/*.json outputs/*.log; do
    [ -e "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$PACK_ROOT/outputs/${prefix}$base"
  done
  for f in outputs/derived/*; do
    [ -e "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$PACK_ROOT/outputs/${prefix}derived-$base"
  done
  # Deterministic compare log (no timestamps, no workdir paths).
  {
    echo "clean_reproduce.sh fresh run (cycle $cycle)"
    echo "shipped simulator status: $(python3 -c "import json;print(json.load(open('$WORK/shipped/outputs/derived/run-summary.json'))['steps']['simulator'])")"
    echo "fresh simulator status: $(python3 -c "import json;print(json.load(open('outputs/derived/run-summary.json'))['steps']['simulator'])")"
    echo "shipped probe status: $(python3 -c "import json;print(json.load(open('$WORK/shipped/outputs/derived/run-summary.json'))['steps']['probe'])")"
    echo "fresh probe status: $(python3 -c "import json;print(json.load(open('outputs/derived/run-summary.json'))['steps']['probe'])")"
    echo "compare: $(python3 -c "import json;d=json.load(open('outputs/derived/compare-results.json'));print('%d/%d checks PASS' % (d['passed'], d['total']))")"
  } > "$PACK_ROOT/outputs/${prefix}compare.log"
  cat "$PACK_ROOT/outputs/${prefix}compare.log"
  cd "$PACK_ROOT" || exit 1
}

# Cycle 1 -> outputs/fresh-clone-*, cycle 2 -> outputs/fresh-clone-2-*.
run_cycle 1 "fresh-clone-"
run_cycle 2 "fresh-clone-2-"

# Re-run the suite in the main pack so run-manifest.json records both
# reproduction logs and their digests, then regenerate digests.
echo "--- step: re-run run_all.sh in the main pack (record reproductions) ---"
bash "$PACK_ROOT/scripts/run_all.sh" || { echo "run_all.sh FAILED in main pack"; exit 1; }
bash "$PACK_ROOT/scripts/make_sha256sums.sh" || exit 1
bash "$PACK_ROOT/scripts/verify_digests.sh" || exit 1
echo "clean_reproduce.sh: ALL CHECKS PASSED"
