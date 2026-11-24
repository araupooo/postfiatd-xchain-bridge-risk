# Risk register

Forged attestation, witness collusion and quorum loss, replayed claims,
stalled witnesses, and door-account key compromise in the postfiatd
XChain bridge. Severity is judged by impact on the funds locked in the
door accounts and on the bridge's ability to keep moving legitimate
claims.

| Risk | Severity | Risk | Evidence / mitigation in the pinned code |
| --- | --- | --- | --- |
| K-01 | HIGH | Quorum collusion theft: colluding witness weight at or above quorum finalizes a forged event and moves the door's funds to the attacker. | Weight >= quorum finalizes (R-21, F-01). Mitigation: keep quorum above any plausible colluding set; scenario S-01/S-02. |
| K-02 | HIGH | Single-witness bridge: a 1-of-1 bridge loses everything to one compromised witness. | No minimum witness count in bridge code (R-24, F-02); scenario S-07. Mitigation: never run a 1-of-1 bridge outside a test. |
| K-03 | HIGH | Door master key left enabled: whoever holds the master key drains the door without any witness. | Bridge creation never checks the master key (R-40, F-03); scenario S-06. Mitigation: disable the master key at setup and verify it on-chain. |
| K-04 | MEDIUM | Even-n majority quorum degradation: maximum safe collusion stalls honest claims instead of leaving them safe. | Threshold table (R-44, F-04); scenario S-08. Mitigation: prefer odd witness counts with majority quorum. |
| K-05 | MEDIUM | Signer-list churn strands claims: removing witnesses mid-claim erases their attestations and can drop a quorum below threshold. | Attestations from removed signers are erased (R-18, F-05); scenario S-05. Mitigation: change signer lists only when no claim is in flight, or re-attest after the change. |
| K-06 | MEDIUM | Re-attestation switching: a witness can change its attested amount or destination by attesting again. | Re-attestation replaces the old attestation (R-17, F-06). Mitigation: witnesses must attest exactly once per event; monitor for changed attestations. |
| K-07 | MEDIUM | Reward pool unfunded stall: if the claim owner spent the reward funds, finalize fails and the claim waits. | Main transfer rolls back, claim kept (F-07); scenario S-11. Mitigation: keep the reward funded until the claim finalizes. |
| K-08 | MEDIUM | Account-create claim burn: a failed account-create transfer consumes the claim while no account is created. | ClaimCount advances even on failure (R-33, F-08). Mitigation: verify the destination can receive before committing. |
| K-09 | MEDIUM | Quorum-agreed reward inflation in account creation: the paid reward is the triggering attestation's value, not the bridge's. | attBegin->rewardAmount is paid (F-09). Mitigation: witnesses must attest only the reward they observed on the source chain. |
| K-10 | MEDIUM | Reward account misdirection: an attestation can name any reward account, and a per-account failure is tolerated. | No constraint on the reward account (F-10). Mitigation: audit reward accounts in attestations before quorum. |
| K-11 | MEDIUM | Stale claims never expire: a claim created long ago can still be completed at any later time. | No expiry on claim IDs (F-11). Mitigation: treat every outstanding claim ID as live; monitor the bridge's claim ID counter. |
| K-12 | LOW | Reward rounding remainder stays with the reward pool source. | Equal split with downward rounding (R-37, F-12). Mitigation: none needed; the remainder is dust. |
| K-13 | LOW | No bridge-level attestation throttle beyond the ledger transaction fee. | Attestation submission has no rate limit in the attestation path (absence; probe I-01). Mitigation: the ledger fee is the only cost; monitor attestation volume. |
| K-14 | LOW | Claim-ID exhaustion after 2^32 - 1 claims: the counter overflows and the bridge can no longer issue claim IDs. | uint32 counter (R-27); scenario S-12. Mitigation: none at this scale; the bound is 4,294,967,295 claims. |
