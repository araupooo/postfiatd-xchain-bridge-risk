# Evidence index

Where every deliverable lives, and how to check it.

| Deliverable | Location | How to verify |
| --- | --- | --- |
| Rule table (45 rules: VERIFIED 38, SPECIFIED 4, MODELLED 2, UNTESTABLE 1) | `configs/xchain-bridge-rules.json` | `bash scripts/run_all.sh` step 2 validates ids, statuses, and ranges. |
| Scenario inputs (13 scenarios, 18 runs) | `configs/scenarios.json` | Same step 2 validation; the simulator prints the totals. |
| Deterministic simulator | `src/xchain_bridge_model.py` | `python3 src/xchain_bridge_model.py --help`; re-run reproduces byte-identical outputs (probe G-01). |
| Scenario results | `outputs/derived/xchain-bridge-results.json` | SHA-256 in `outputs/run.log` and `run-manifest.json`. |
| Scenario matrix | `outputs/derived/scenario-matrix.json` | Same; human-readable form in `docs/scenario-matrix.md`. |
| Probe results (12/12) | `outputs/derived/probe-results.json`, `outputs/probe-run.log` | `python3 scripts/probe.py` (exit 0 only if every check passes). |
| Verify-digests capture | `outputs/verify-digests.log` | Full unedited output of `scripts/verify_digests.sh`, captured by `run_all.sh` step 7; digest in `run-manifest.json`. |
| Verbatim excerpts (44) | `fixtures/source-excerpts/E01.txt` … `E44.txt` | `scripts/extract_excerpts.py` re-extracts them from the pinned checkout; digests in `fixtures/source-hashes.json`. |
| Excerpt manifest + source hashes | `fixtures/excerpts-manifest.json`, `fixtures/source-hashes.json` | Probe H-01 compares every blob SHA/size with `git hash-object` in the checkout. |
| Claim index (24 claims) | `docs/claim-index.md` | Probe F-01 reconciles the counts (16/2/4/2). |
| Findings (12) | `findings.json` | Probe F-01 reconciles the count (HIGH 3, MEDIUM 6, LOW 3). |
| Risk register (14) | `docs/risk-register.md` | Probe F-01 reconciles the count (HIGH 3, MEDIUM 8, LOW 3). |
| Gap register (8) | `docs/gap-register.md` | Probe F-01 reconciles the count. |
| Methodology | `docs/methodology.md` | States what is source-derived vs simulated vs unknown. |
| Decision memo | `docs/decision-memo.md` | Operator guidance: witness counts, quorum, door keys, signer-list changes. |
| Citations | `docs/citations.md` | Four SPECIFIED rules with verbatim quotes and access date, plus the one-witness quote. |
| Run manifest | `run-manifest.json` | Full counts + results/matrix digests + verify-digests digest + both reproduction logs; verified by probe H-01. |
| Full-run log | `outputs/run.log` | Unedited `run_all.sh` output with full 64-character SHA-256 digests. |
| Fresh-copy reproductions (x2) | `outputs/fresh-clone-run.log`, `outputs/fresh-clone-compare.log`, `outputs/fresh-clone-derived-*`; `outputs/fresh-clone-2-run.log`, `outputs/fresh-clone-2-compare.log`, `outputs/fresh-clone-2-derived-*` | Produced by `scripts/clean_reproduce.sh` (two cycles); both compare runs pass. |
| Digest manifest | `SHA256SUMS` | `bash scripts/verify_digests.sh` (covers every shipped file except itself). |
