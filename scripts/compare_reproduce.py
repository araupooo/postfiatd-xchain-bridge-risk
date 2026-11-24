#!/usr/bin/env python3
"""compare_reproduce.py — compare a fresh clean_reproduce.sh run against
the shipped outputs.

Usage:
    python3 scripts/compare_reproduce.py <shipped-dir> [fresh-pack-root]

<shipped-dir> holds the shipped outputs/ and fixtures/ trees saved
before the fresh copy was made. The fresh pack root defaults to the
pack this script lives in. Exits 0 only if every comparison check
passes. Writes outputs/derived/compare-results.json in the fresh pack.

Comparison rules:
- JSON files: deep-compare, ignoring volatile fields (timestamps,
  elapsed/wall-time/duration values, host paths). Timing values are
  never compared absolutely; they are only sanity-checked as
  non-negative numbers (loose tolerance by design, never microseconds).
- .log files: timestamp-pattern lines are stripped, then SHA-256
  compared. .txt excerpts: plain SHA-256 compare.
- Excluded from comparison: SHA256SUMS (regenerated per environment),
  compare-results.json (this script's own output), verify-digests.log
  (its content reflects the file set present in each environment: a
  fresh copy has no fresh-clone-* files yet, so its capture lists
  fewer files), and fresh-clone-* evidence files.
"""
import hashlib
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PACK = os.path.dirname(SCRIPT_DIR)

# Volatile JSON keys: ignored in deep comparison.
VOLATILE_EXACT = {
    "generated_at", "timestamp", "started_at", "finished_at",
    "elapsed_ms", "elapsed_s", "duration_s", "duration_ms",
    "wall_time_ms", "wall_time_s", "run_host", "workdir", "hostname",
}
VOLATILE_RE = re.compile(r"^(elapsed|wall_time|duration)[_-]"
                         r"|[_-](elapsed|elapsed_ms|wall_time|duration)$")
TIMESTAMP_LINE_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?")

EXCLUDE_NAMES = {"compare-results.json", "SHA256SUMS", "verify-digests.log"}
EXCLUDE_PREFIX = "fresh-clone-"


def is_volatile(key):
    return key in VOLATILE_EXACT or bool(VOLATILE_RE.search(key))


def deep_equal(a, b, path, diffs):
    """Recursive compare ignoring volatile keys; record diffs."""
    if isinstance(a, dict) and isinstance(b, dict):
        keys = set(a) | set(b)
        for k in sorted(keys):
            if is_volatile(k):
                continue
            if k not in a:
                diffs.append(f"{path}.{k}: missing in fresh")
            elif k not in b:
                diffs.append(f"{path}.{k}: missing in shipped")
            else:
                deep_equal(a[k], b[k], f"{path}.{k}", diffs)
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length {len(a)} vs {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            deep_equal(x, y, f"{path}[{i}]", diffs)
        return
    if isinstance(a, float) or isinstance(b, float):
        try:
            if abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a))):
                return
        except (TypeError, ValueError):
            pass
    if a != b:
        diffs.append(f"{path}: {a!r} vs {b!r}")


def timing_values_ok(obj, path, problems):
    """Timing values must be non-negative numbers; never compared exactly."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if is_volatile(k) and isinstance(v, (int, float)):
                if v < 0:
                    problems.append(f"{path}.{k}: negative timing {v}")
            timing_values_ok(v, f"{path}.{k}", problems)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            timing_values_ok(v, f"{path}[{i}]", problems)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_log_stripped(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for raw in fh:
            try:
                line = raw.decode("utf-8")
            except UnicodeDecodeError:
                line = raw.decode("utf-8", "replace")
            if TIMESTAMP_LINE_RE.search(line):
                continue
            h.update(raw)
    return h.hexdigest()


def deterministic_files(root):
    """Deterministic output files under <root>/outputs (relative paths)."""
    found = []
    outdir = os.path.join(root, "outputs")
    for dirpath, _dirs, files in os.walk(outdir):
        for name in files:
            if name in EXCLUDE_NAMES or name.startswith(EXCLUDE_PREFIX):
                continue
            full = os.path.join(dirpath, name)
            found.append(os.path.relpath(full, outdir))
    return sorted(found)


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    if len(sys.argv) < 2:
        print("usage: compare_reproduce.py <shipped-dir> [fresh-pack-root]",
              file=sys.stderr)
        return 2
    shipped_dir = sys.argv[1]
    fresh_pack = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PACK
    checks = []

    def check(label, ok, detail=""):
        checks.append({"check": label, "pass": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + label +
              ((" — " + detail) if detail else ""))

    shipped_summary = os.path.join(shipped_dir, "outputs", "derived",
                                   "run-summary.json")
    fresh_summary = os.path.join(fresh_pack, "outputs", "derived",
                                 "run-summary.json")
    if os.path.isfile(shipped_summary) and os.path.isfile(fresh_summary):
        diffs = []
        deep_equal(load_json(shipped_summary), load_json(fresh_summary),
                   "run-summary", diffs)
        check("run-summary.json identical (ignoring volatile fields)",
              not diffs, "; ".join(diffs[:3]))
    else:
        check("run-summary.json exists in shipped and fresh",
              False, f"shipped={os.path.isfile(shipped_summary)} "
                     f"fresh={os.path.isfile(fresh_summary)}")

    # Every deterministic derived JSON deep-compared.
    shipped_derived = os.path.join(shipped_dir, "outputs", "derived")
    fresh_derived = os.path.join(fresh_pack, "outputs", "derived")
    derived_names = set()
    for d in (shipped_derived, fresh_derived):
        if os.path.isdir(d):
            derived_names |= {n for n in os.listdir(d)
                              if n.endswith(".json")
                              and n not in EXCLUDE_NAMES
                              and not n.startswith(EXCLUDE_PREFIX)}
    for name in sorted(derived_names):
        if name == "run-summary.json":
            continue  # already compared above
        sp, fp = os.path.join(shipped_derived, name), os.path.join(fresh_derived, name)
        if not (os.path.isfile(sp) and os.path.isfile(fp)):
            check(f"derived/{name} present in shipped and fresh",
                  False, f"shipped={os.path.isfile(sp)} "
                         f"fresh={os.path.isfile(fp)}")
            continue
        diffs = []
        try:
            deep_equal(load_json(sp), load_json(fp), name, diffs)
        except ValueError as exc:
            diffs.append(f"invalid JSON: {exc}")
        check(f"derived/{name} identical (ignoring volatile fields)",
              not diffs, "; ".join(diffs[:3]))

    # Timing sanity: non-negative numbers only, never exact-compared.
    problems = []
    for d in (shipped_derived, fresh_derived):
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                if name.endswith(".json") and name not in EXCLUDE_NAMES \
                        and not name.startswith(EXCLUDE_PREFIX):
                    try:
                        timing_values_ok(load_json(os.path.join(d, name)),
                                         name, problems)
                    except ValueError:
                        pass
    check("all timing values non-negative (loose band, never exact)",
          not problems, "; ".join(problems[:3]))

    # Deterministic output file sets match.
    s_files = deterministic_files(shipped_dir)
    f_files = deterministic_files(fresh_pack)
    check("deterministic output file sets match",
          s_files == f_files,
          f"shipped-only={sorted(set(s_files) - set(f_files))} "
          f"fresh-only={sorted(set(f_files) - set(s_files))}")

    # Per-file content compare: JSON deep-compare, logs stripped, else digest.
    for rel in sorted(set(s_files) & set(f_files)):
        sp = os.path.join(shipped_dir, "outputs", rel)
        fp = os.path.join(fresh_pack, "outputs", rel)
        if rel.endswith(".json"):
            continue  # already deep-compared above
        if rel.endswith(".log"):
            ok = sha256_log_stripped(sp) == sha256_log_stripped(fp)
            check(f"outputs/{rel} identical (timestamp lines stripped)", ok)
        else:
            ok = sha256_file(sp) == sha256_file(fp)
            check(f"outputs/{rel} identical (SHA-256)", ok)

    # Excerpts and source hashes, when present on both sides.
    for rel in ("fixtures/source-hashes.json",):
        sp, fp = os.path.join(shipped_dir, rel), os.path.join(fresh_pack, rel)
        if os.path.isfile(sp) and os.path.isfile(fp):
            diffs = []
            deep_equal(load_json(sp), load_json(fp), rel, diffs)
            check(f"{rel} identical (ignoring volatile fields)",
                  not diffs, "; ".join(diffs[:3]))
    for sub in ("fixtures/source-excerpts",):
        names = set()
        for base in (os.path.join(shipped_dir, sub), os.path.join(fresh_pack, sub)):
            if os.path.isdir(base):
                names |= set(os.listdir(base))
        for name in sorted(names):
            sp = os.path.join(shipped_dir, sub, name)
            fp = os.path.join(fresh_pack, sub, name)
            if not (os.path.isfile(sp) and os.path.isfile(fp)):
                check(f"{sub}/{name} present in shipped and fresh", False,
                      f"shipped={os.path.isfile(sp)} "
                      f"fresh={os.path.isfile(fp)}")
                continue
            check(f"{sub}/{name} identical (SHA-256)",
                  sha256_file(sp) == sha256_file(fp))

    passed = sum(1 for c in checks if c["pass"])
    result = {"checks": checks, "passed": passed, "total": len(checks)}
    outpath = os.path.join(fresh_pack, "outputs", "derived",
                           "compare-results.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(f"compare: {passed}/{len(checks)} checks PASS")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
