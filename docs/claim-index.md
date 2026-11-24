# Claim-to-evidence index

Every claim in this pack, its status, and the exact evidence for it.
Status meanings: VERIFIED — read from the pinned source with a
grep-verified file:line citation; SPECIFIED — stated in the cited public
documentation and cross-checked against code; MODELLED — an output of
the deterministic simulator on the stated inputs; UNTESTABLE — not
decidable from the pinned source alone.

| Claim | Status | Claim | Evidence |
| --- | --- | --- | --- |
| C-01 | VERIFIED | Quorum is weight-based over the door account's signer list. | R-19, R-20, E09: `XChainBridge.cpp:775-811`. |
| C-02 | VERIFIED | Attestation signatures are verified over the canonical message. | R-10, R-11, E35, E36: `XChainAttestations.cpp:102-105`, `:219-258`. |
| C-03 | VERIFIED | Forged attestations with a bad signature are rejected in preflight. | R-12, E15: `XChainBridge.cpp:1213-1238`. |
| C-04 | VERIFIED | Only listed signers' keys count; a master key attests only if not disabled. | R-14, R-15, E02: `XChainBridge.cpp:111-175`. |
| C-05 | VERIFIED | A 1-of-1 bridge is possible; a signer list holds at most 8 signers (32 with ExpandedSignerList). | R-24, E44: `STTx.h:53-64`. |
| C-06 | VERIFIED | Claim IDs are a per-bridge counter; the first ID is 1; overflow returns tecINTERNAL. | R-27, E29: `XChainBridge.cpp:2035-2098`. |
| C-07 | VERIFIED | The claim ID is destroyed after funds move; a replayed claim finds no claim ID. | R-28, E08: `XChainBridge.cpp:737-763`. |
| C-08 | VERIFIED | Only the claim ID owner can claim; the sending account and destination chain must match. | R-29, R-30, E24, E10: `XChainBridge.cpp:1653-1752`, `:852-915`. |
| C-09 | VERIFIED | Account-create claims are strictly ordered with a 128-wide window (at most 127 outstanding). | R-31, R-32, E33, E14: `XChainBridge.h:29`, `XChainBridge.cpp:1121-1191`. |
| C-10 | VERIFIED | The reward pool is split equally among the matching attesters. | R-37, E07: `XChainBridge.cpp:672-736`. |
| C-11 | VERIFIED | A failed account-create transfer removes the claim; a failed claim transfer keeps it. | R-33, E14, E06: `XChainBridge.cpp:1121-1191`, `:615-671`. |
| C-12 | VERIFIED | Bridge creation requires distinct doors, a door submitter, matching issues, and the reserve. | R-01, R-02, R-03, R-04, R-07, E18, E20: `XChainBridge.cpp:1374-1411`, `:1449-1499`. |
| C-13 | VERIFIED | The door cannot commit to itself, and a commit moves funds to the door. | R-39, R-41, E26, E27: `XChainBridge.cpp:1882-1942`, `:1943-1986`. |
| C-14 | VERIFIED | Re-attestation replaces the old attestation; removed signers' attestations are erased. | R-17, R-18, E04, E03: `XChainBridge.cpp:284-344`, `:191-240`. |
| C-15 | VERIFIED | Quorum is evaluated per new attestation; the destination is checked only for add-attestation flow. | R-23, R-22, E04, E05, E38: `XChainBridge.cpp:284-344`, `:350-363`; `XChainAttestations.cpp:546-556`. |
| C-16 | VERIFIED | Claim IDs never expire. | Absence grep: `expir` 0 hits in `XChainBridge.cpp` and `XChainAttestations.cpp` (probe I-01); no expiry field is set when a claim ID is created (E29). |
| C-17 | SPECIFIED | Anyone can run a witness server; evaluating witness reliability is the issuing chain's burden. | R-42, `docs/citations.md` S-03: witness-servers documentation, 24 Nov 2026. |
| C-18 | SPECIFIED | A bridge may start with a single witness server. | `docs/citations.md` S-05: witness-servers documentation, 24 Nov 2026. |
| C-19 | MODELLED | With 5 witnesses and quorum 3, 2 colluding cannot exploit but 3 can. | R-43; scenario S-02; `outputs/derived/xchain-bridge-results.json`. |
| C-20 | MODELLED | With 8 witnesses and quorum 5, 4 colluding degrade the bridge without exploiting it. | R-44; scenario S-08; `outputs/derived/xchain-bridge-results.json`. |
| C-21 | MODELLED | A stalled-witness majority halts honest claims until witnesses return. | Scenario S-03 run B; `outputs/derived/xchain-bridge-results.json`. |
| C-22 | MODELLED | A door master key left enabled turns key theft into total loss. | Scenario S-06 run B; `outputs/derived/xchain-bridge-results.json`. |
| C-23 | UNTESTABLE | Live witness attestation latency and independence. | R-45; no live node was run (gap G-01). |
| C-24 | UNTESTABLE | Real-world door-key management practice across deployed bridges. | No live deployment data (gap G-03). |
