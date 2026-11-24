#!/usr/bin/env python3
"""extract_excerpts.py — pull verbatim pinned-source excerpts into fixtures/.

Usage:
    python3 scripts/extract_excerpts.py [PACK_ROOT] [MANIFEST]
    PINNED_CHECKOUT=<path>  (default ~/workspace/postfiatd-pin-0085a1f)

The manifest (default fixtures/excerpts-manifest.json) is a JSON object:
    {"pinned_commit": "<40-hex>",
     "repo": "postfiatd",
     "excerpts": [{"id": "<file-stem>", "file": "<repo-relative path>",
                   "start_line": <int>, "end_line": <int>,
                   "anchor": "<text expected inside the range, optional>",
                   "blob_sha": "<git blob SHA, optional>",
                   "blob_size": <bytes, optional>}, ...]}

The script verifies `git rev-parse HEAD` in PINNED_CHECKOUT equals the
pinned commit and refuses to run otherwise. For each entry it checks
the line range is in bounds, the anchor (when given) is inside the
range, and the manifest blob SHA/size (when given) match the checkout
file. It writes fixtures/source-excerpts/<id>.txt with a header giving
repo, commit, file, lines, plus blob SHA/size, and writes
fixtures/source-hashes.json with SHA-256 digests and git blob SHAs per
excerpt and per source file.

Line numbers are never taken from a web fetch: they come from the local
checkout of the pinned commit.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
MANIFEST = Path(sys.argv[2]) if len(sys.argv) > 2 else PACK_ROOT / "fixtures" / "excerpts-manifest.json"
PIN = Path(os.environ.get("PINNED_CHECKOUT", "~/workspace/postfiatd-pin-0085a1f")).expanduser()
COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"
REPO = "postfiatd"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(relpath):
    out = subprocess.run(["git", "-C", str(PIN), "hash-object", "--", relpath],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def fail(msg):
    print(f"extract_excerpts: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if not PIN.is_dir():
        fail(f"pinned checkout not found: {PIN} "
             f"(set PINNED_CHECKOUT to the postfiatd checkout at {COMMIT})")
    try:
        head = subprocess.run(["git", "-C", str(PIN), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError as exc:
        fail(f"git rev-parse HEAD failed in {PIN}: {exc.stderr.strip()}")
    if head != COMMIT:
        fail(f"pinned checkout HEAD {head} != {COMMIT} ({PIN})")
    print(f"pinned checkout verified: {head}")

    if not MANIFEST.is_file():
        fail(f"excerpts manifest not found: {MANIFEST}")
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest.get("pinned_commit") and manifest["pinned_commit"] != COMMIT:
        fail(f"manifest pinned_commit {manifest['pinned_commit']} != {COMMIT}")
    entries = manifest.get("excerpts")
    if not isinstance(entries, list) or not entries:
        fail(f"manifest {MANIFEST} has no non-empty \"excerpts\" list")

    outdir = PACK_ROOT / "fixtures" / "source-excerpts"
    outdir.mkdir(parents=True, exist_ok=True)
    hashes = {"pinned_commit": COMMIT, "repo": REPO, "files": {}, "excerpts": {}}

    for entry in entries:
        ex_id = entry.get("id")
        relpath = entry.get("file")
        first = entry.get("start_line")
        last = entry.get("end_line")
        if not ex_id or not ID_RE.match(str(ex_id)):
            fail(f"bad excerpt id: {ex_id!r} (must match {ID_RE.pattern})")
        if not relpath or not isinstance(first, int) or not isinstance(last, int):
            fail(f"excerpt {ex_id}: need file, start_line, end_line")
        src = PIN / relpath
        if not src.is_file():
            fail(f"excerpt {ex_id}: file not in checkout: {relpath}")
        lines = src.read_text().splitlines()
        if first < 1 or last < first or last > len(lines):
            fail(f"excerpt {ex_id}: range {first}-{last} out of bounds "
                 f"for {relpath} ({len(lines)} lines)")
        chunk = lines[first - 1:last]
        anchor = entry.get("anchor")
        if anchor and not any(anchor in ln for ln in chunk):
            fail(f"excerpt {ex_id}: anchor {anchor!r} not in "
                 f"{relpath}:{first}-{last}")
        size = src.stat().st_size
        blob = git_blob_sha(relpath)
        if entry.get("blob_sha") and entry["blob_sha"] != blob:
            fail(f"excerpt {ex_id}: manifest blob_sha {entry['blob_sha']} "
                 f"!= checkout blob {blob} for {relpath}")
        if entry.get("blob_size") is not None and entry["blob_size"] != size:
            fail(f"excerpt {ex_id}: manifest blob_size {entry['blob_size']} "
                 f"!= checkout size {size} for {relpath}")
        file_sha = sha256_file(src)
        f = hashes["files"].setdefault(relpath, {})
        f["sha256"] = file_sha
        f["git_blob_sha"] = blob
        f["lines"] = len(lines)
        f["size_bytes"] = size

        text = (f"# Source excerpt {ex_id} — {REPO} {COMMIT}.\n"
                f"# File: {relpath}, lines {first}-{last}.\n"
                f"# Line numbers verified with grep -n on a local checkout "
                f"of the pinned commit.\n"
                f"# Source file SHA-256: {file_sha}\n"
                f"# Source file git blob SHA: {blob}\n"
                f"# Source file size: {size} bytes\n\n"
                f"# --- {relpath} lines {first}-{last} ---\n"
                + "\n".join(chunk) + "\n")
        (outdir / f"{ex_id}.txt").write_text(text)
        hashes["excerpts"][ex_id] = {
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "file": relpath,
            "lines": f"{first}-{last}",
            "blob_sha": blob,
            "blob_size": size,
        }
        print(f"wrote fixtures/source-excerpts/{ex_id}.txt")

    with open(PACK_ROOT / "fixtures" / "source-hashes.json", "w") as fh:
        json.dump(hashes, fh, indent=1)
        fh.write("\n")
    print("wrote fixtures/source-hashes.json")


if __name__ == "__main__":
    main()
