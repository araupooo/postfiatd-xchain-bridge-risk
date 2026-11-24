# Operator decision memo

## The one rule that matters

**Disable the door master key, and verify it on-chain.** Bridge
creation never checks the door's master key or signer list (R-40,
F-03). A door whose master key was never disabled can be drained by
whoever holds that key, with no witness involved at all (scenario
S-06 run B). The code header says the master key "will be disabled"
— that is a setup instruction, not an enforcement. Check the door
account's flags on the ledger before funding the bridge, and check
again after every bridge modification.

## What to configure

1. **Witness count and quorum.** Use an odd witness count with a
   majority quorum (5 witnesses, quorum 3; 7 witnesses, quorum 4).
   With an even count and majority quorum, the largest collusion
   that cannot exploit the bridge still stalls honest claims
   (threshold table: 8 witnesses, quorum 5, 4 colluding degrades).
   Never run a 1-of-1 bridge outside a test: one compromised
   witness is total loss (F-02, scenario S-07).
2. **Quorum above any plausible colluding set.** The exploit
   threshold is exactly the quorum: colluding weight at or above
   quorum steals the door's funds (R-43, F-01). Size the quorum so
   that no single operator, hosting provider, or jurisdiction
   controls that much weight.
3. **Signer-list changes.** Change the signer list only when no
   claim is in flight, or re-attest after the change. Attestations
   from removed signers are erased on the next quorum count, and a
   mid-claim change can strand a claim below quorum (F-05, scenario
   S-05). Never remove witnesses down to a live weight below quorum.
4. **Reward funding.** Keep the reward funded until the claim
   finalizes. If the claim owner spends the reward between commit
   and claim, finalize fails and the claim waits (F-07, scenario
   S-11). For account creation, a failed transfer still consumes
   the claim (F-08) — verify the destination can receive before
   committing.
5. **Reward accounts.** Audit the reward account in every
   attestation. The code puts no constraint on it (F-10), and for
   account creation the paid reward is the triggering attestation's
   value, not the bridge's SignatureReward (F-09) — a quorum
   agreeing on an inflated reward drains the door.
6. **Outstanding claims.** Treat every outstanding claim ID as
   live: claim IDs never expire (F-11). Monitor the bridge's claim
   ID counter; it stops at 4,294,967,295 (scenario S-12).

## What not to do

- Do not assume the code enforces the setup steps in the docs.
  It does not check the door's signer list, master key, or witness
  reliability at bridge creation — those are operator duties.
- Do not lower the quorum or the SignatureReward through
  BridgeModify without re-checking the collusion threshold
  (R-08, R-43).
- Do not treat a stalled claim as a lost claim: if the shortfall
  is temporary (witnesses stalled), the claim finalizes when they
  return; if it is permanent (witnesses removed), only a
  signer-list change recovers it.
