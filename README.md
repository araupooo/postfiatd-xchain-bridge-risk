# Cross-Chain Bridge Risk in postfiatd

How postfiatd's XChain bridge resists forged attestations, witness
collusion and quorum loss, replayed claims, stalled witnesses, and
door-account key compromise — at commit
`0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10).

## Headline findings

- **Quorum collusion steals the door's funds.** If colluding witness
  weight reaches quorum, a forged event finalizes and the locked
  funds move to the attacker's destination. The code header states
  it directly: "if a quorum of them collude, they can steal the
  funds put into trust" (`XChainBridge.cpp:74-77`).
- **There is no minimum witness count.** A 1-of-1 bridge is
  creatable, and its single witness reaching quorum alone is total
  loss (`STTx.h:53-64`; scenario S-07).
- **Door master-key disablement is not enforced in code.** Bridge
  creation never checks the door's signer list or master key. A
  door whose master key was never disabled can be drained without
  any witness (scenario S-06 run B).
- **Even witness counts with majority quorum degrade at maximum
  safe collusion.** With 8 witnesses and quorum 5, 4 colluding
  witnesses leave honest weight 4 below quorum 5, so neither side
  finalizes (threshold table).
- **Signer-list churn can strand a claim.** Attestations from
  removed signers are erased on the next quorum count; removing 3
  of 5 witnesses mid-claim drops live weight below quorum 3
  (scenario S-05 run B).
- **Claim IDs never expire, and the account-create reward paid is
  the triggering attestation's value, not the bridge's
  SignatureReward** — a quorum agreeing on an inflated reward
  drains the door beyond the bridge's stated reward.

## Contents

- 45 rules (VERIFIED 38, SPECIFIED 4, MODELLED 2, UNTESTABLE 1) —
  `configs/xchain-bridge-rules.json`, with grep-verified file:line
  ranges and verbatim excerpts in `fixtures/source-excerpts/` (44
  excerpts, 7 source files).
- Deterministic simulator (`src/xchain_bridge_model.py`) + scenario
  matrix — 13 scenarios, 18 runs: safe 8, degraded 3, exploited 4,
  halted 3.
- Claim-to-evidence index: 24 claims (VERIFIED 16, SPECIFIED 2,
  MODELLED 4, UNTESTABLE 2) — `docs/claim-index.md`.
- Findings: 12 (HIGH 3, MEDIUM 6, LOW 3) — `findings.json`.
- Risk register: 14 risks (HIGH 3, MEDIUM 8, LOW 3) —
  `docs/risk-register.md`. Gap register: 8 gaps —
  `docs/gap-register.md`.
- Operator decision memo (witness counts, quorum, door keys,
  signer-list changes) — `docs/decision-memo.md`. Methodology —
  `docs/methodology.md`. Evidence index — `docs/evidence-index.md`.

## Reproduction

```bash
bash scripts/run_all.sh        # exit 0 only if every check passes
bash scripts/clean_reproduce.sh  # fresh-copy reproduction (run twice)
```

- Full suite: `run_all.sh` exits 0; probe 12/12 checks pass.
- `outputs/run.log` (unedited full-run log, 10 lines) SHA-256:
  `d7bd8b507fdf812ceddda939b31cb358cff1bfa479cd9c0ee2555ccdf1d445a1`
- Fresh-copy reproduction was run twice; both passed with
  byte-identical deterministic outputs. Fresh-clone run log:
  `outputs/fresh-clone-run.log` SHA-256:
  `d7bd8b507fdf812ceddda939b31cb358cff1bfa479cd9c0ee2555ccdf1d445a1`
  (identical to the shipped `run.log` digest — the first fresh copy
  reproduces the shipped log byte-for-byte). Second fresh-clone run
  log: `outputs/fresh-clone-2-run.log` SHA-256:
  `d7bd8b507fdf812ceddda939b31cb358cff1bfa479cd9c0ee2555ccdf1d445a1`
  (also identical).
- Digests: `xchain-bridge-results.json`
  `6acdd9a3c631f46aca3c143b58ded36d4eb97321526da6f4dd37e9ea190d3a81`;
  `scenario-matrix.json`
  `6b459ece4069f978314e491ee1cb164c3e26c2c89efef4e874ffdf0f6c8c49ff`.
- Verify all digests: `bash scripts/verify_digests.sh`. The full
  unedited output of that check is captured in
  `outputs/verify-digests.log` (SHA-256:
  `eb1d4a11f1240cad6399ceb3c2c8c94946326826eabac293413378807090807a`)
  and its digest is recorded in `run-manifest.json`.

The logs are independently resolvable as raw files:

https://raw.githubusercontent.com/araupooo/postfiatd-xchain-bridge-risk/main/outputs/run.log
https://raw.githubusercontent.com/araupooo/postfiatd-xchain-bridge-risk/main/outputs/fresh-clone-run.log
https://raw.githubusercontent.com/araupooo/postfiatd-xchain-bridge-risk/main/outputs/fresh-clone-2-run.log
https://raw.githubusercontent.com/araupooo/postfiatd-xchain-bridge-risk/main/outputs/probe-run.log
https://raw.githubusercontent.com/araupooo/postfiatd-xchain-bridge-risk/main/outputs/verify-digests.log

## CI

Continuous integration runs the same suite on every push; see the
workflow runs page:

https://github.com/araupooo/postfiatd-xchain-bridge-risk/actions/workflows/verify.yml
