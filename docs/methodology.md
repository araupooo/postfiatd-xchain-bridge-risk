# Methodology

## Pinned source

All source findings are pinned to postfiatd commit
`0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10). Every cited
line was verified with `grep -n` on a local checkout of that commit
(`~/workspace/postfiatd-pin-0085a1f`); no line number comes from a web
fetch. The 44 verbatim excerpts in `fixtures/source-excerpts/` were
extracted by `scripts/extract_excerpts.py` from that checkout, and
`fixtures/source-hashes.json` records the SHA-256, git blob SHA, and
size of every excerpt and every cited source file.

## How the rules were built

1. Read the bridge code paths end to end:
   `XChainBridge.cpp` (bridge creation, modification, claims, commits,
   claim IDs, attestations, account creation, reward distribution,
   claim finalization), `XChainBridge.h` (the 128-claim window, the
   claim class comment on replay prevention),
   `XChainAttestations.cpp` (signature verification, the signed
   message, the match rules), `XChainAttestations.h` (the attestation
   class declarations), `STXChainBridge.cpp` (the bridge fields),
   `SetSignerList.cpp` (signer-count and quorum bounds), and
   `STTx.h` (the 1-to-8, or 32, signer limits).
2. Recorded every hard-coded constant that bounds the behaviour:
   at most 128 account-create claims outstanding, claim IDs are a
   uint32 counter starting at 1, signer lists hold 1 to 8 entries
   (32 with ExpandedSignerList), quorum must be above zero and no
   greater than the total signer weight.
3. Recorded every absence that matters, and re-grepped each one in
   the probe: no expiry on claim IDs, no minimum witness count in the
   bridge code, no signer-list or master-key check at bridge creation,
   no constraint on the attestation reward account, no reorg handling,
   no bridge-level attestation throttle.
4. Cross-checked the four SPECIFIED rules against the XRPL
   documentation pages in `docs/citations.md`, quoting them verbatim.
   Where the docs and the code diverge, the pack follows the code:
   the header comment says the door master key "will be disabled",
   but the code never enforces it (F-03).

## How the simulator works

`src/xchain_bridge_model.py` reads `configs/scenarios.json` and
applies the pinned rules in a fixed order: no signer list, claim ID
at maximum, replay after success, out-of-order account-create claim,
unfunded reward pool, door-key compromise, inflated reward, then the
weight math (colluding weight >= quorum exploits; honest weight >=
quorum is safe; otherwise degraded when the shortfall is temporary
and halted when it is permanent). All witnesses carry equal weight 1
in the scenarios, matching the usual deployment of one key per
witness. Rounds are 1 for an outright rejection or a door-key
outcome, the quorum for a quorum outcome, and all available
attestations (at least 1) for a no-quorum outcome.

## What is source-derived, simulated, and unknown

- Source-derived (VERIFIED): the rule table, the excerpts, the
  findings, the claim-to-evidence index, and the risk register's
  mechanisms.
- Simulated (MODELLED): the 18 scenario runs and the threshold
  table. They are deterministic consequences of the pinned rules on
  the stated inputs, not measurements.
- Specified (SPECIFIED): deployment facts from the XRPL docs, quoted
  verbatim in `docs/citations.md`.
- Unknown (UNTESTABLE): live witness behaviour, real deployment
  configurations, and counterparty-chain reorganisation handling.
  These are listed in `docs/gap-register.md`.

## Honest limits

- No live node was run and no real cross-chain transfer was made.
  Every attack outcome is a simulator output.
- The witness-server program itself was not audited; only the
  on-ledger checks are.
- The model assumes equal witness weights. Unequal weights change
  the arithmetic but not the rule: the exploit threshold is still
  "colluding weight >= quorum".
