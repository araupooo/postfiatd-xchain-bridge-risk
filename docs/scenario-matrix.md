# Scenario matrix

Deterministic outputs of `src/xchain_bridge_model.py` on
`configs/scenarios.json`. `honest_weight = witnesses - colluding - stalled - removed`;
`live_weight = witnesses - stalled - removed`. safe: the real event finalizes and
forged events are rejected. degraded: no side reaches quorum but the shortfall is
temporary (witnesses stalled, or neither side can reach quorum). exploited: colluding
weight reaches quorum, or the door key bypasses quorum. halted: quorum is unreachable
and cannot recover without a signer-list change, a new claim ID, or a signer list.
Rounds: 1 for an outright rejection or a door-key outcome; the quorum for a quorum
outcome (the q-th attestation completes it); all available attestations (at least 1)
for a no-quorum outcome.

| Scenario | Run | Witnesses | Quorum | Colluding | Stalled | Removed | Outcome | Reason | Honest weight | Live weight | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S-01 | A | 3 | 2 | 1 | 0 | 0 | safe | honest_weight_reaches_quorum | 2 | 3 | 2 |
| S-01 | B | 3 | 2 | 2 | 0 | 0 | exploited | colluding_weight_reaches_quorum | 1 | 3 | 2 |
| S-02 | A | 5 | 3 | 2 | 0 | 0 | safe | honest_weight_reaches_quorum | 3 | 5 | 3 |
| S-02 | B | 5 | 3 | 3 | 0 | 0 | exploited | colluding_weight_reaches_quorum | 2 | 5 | 3 |
| S-03 | A | 5 | 3 | 0 | 1 | 0 | safe | honest_weight_reaches_quorum | 4 | 4 | 3 |
| S-03 | B | 5 | 3 | 0 | 3 | 0 | degraded | neither_side_reaches_quorum | 2 | 2 | 2 |
| S-04 | A | 5 | 3 | 0 | 0 | 0 | safe | claim_id_destroyed_after_funds_moved | 5 | 5 | 1 |
| S-05 | A | 5 | 3 | 0 | 0 | 1 | safe | honest_weight_reaches_quorum | 4 | 4 | 3 |
| S-05 | B | 5 | 3 | 0 | 0 | 3 | halted | signer_list_removal_makes_quorum_unreachable | 2 | 2 | 2 |
| S-06 | A | 5 | 3 | 0 | 0 | 0 | safe | disabled_master_key_cannot_sign | 5 | 5 | 1 |
| S-06 | B | 5 | 3 | 0 | 0 | 0 | exploited | door_master_key_bypasses_quorum | 5 | 5 | 1 |
| S-07 | A | 1 | 1 | 1 | 0 | 0 | exploited | colluding_weight_reaches_quorum | 0 | 1 | 1 |
| S-08 | A | 8 | 5 | 4 | 0 | 0 | degraded | neither_side_reaches_quorum | 4 | 8 | 8 |
| S-09 | A | 5 | 3 | 0 | 0 | 0 | safe | out_of_order_account_create_claim_rejected | 5 | 5 | 1 |
| S-10 | A | 5 | 3 | 0 | 0 | 0 | safe | inflated_reward_excluded_from_quorum_subset | 5 | 5 | 3 |
| S-11 | A | 5 | 3 | 0 | 0 | 0 | degraded | reward_pool_unfunded_claim_kept_for_retry | 5 | 5 | 3 |
| S-12 | A | 5 | 3 | 0 | 0 | 0 | halted | claim_id_counter_at_maximum | 5 | 5 | 1 |
| S-13 | A | 5 | 3 | 0 | 0 | 0 | halted | no_signer_list_on_door | 5 | 5 | 1 |

## Threshold table

Minimum colluding witness weight that exploits the bridge equals the quorum.
`colluding_at_boundary` is one below quorum: the largest collusion that cannot
exploit. With an even witness count and majority quorum, the honest side cannot
reach quorum at that boundary, so the bridge degrades instead of staying safe.

| Witnesses | Quorum | Colluding at boundary | Honest at boundary | Honest reaches quorum | Outcome at boundary | Minimum colluding to exploit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 0 | 1 | yes | safe | 1 |
| 3 | 2 | 1 | 2 | yes | safe | 2 |
| 5 | 3 | 2 | 3 | yes | safe | 3 |
| 7 | 4 | 3 | 4 | yes | safe | 4 |
| 8 | 5 | 4 | 4 | no | degraded | 5 |
| 8 | 4 | 3 | 5 | yes | safe | 4 |
| 32 | 17 | 16 | 16 | no | degraded | 17 |

## Totals

13 scenarios, 18 runs: safe 8, degraded 3, exploited 4, halted 3.
