#!/usr/bin/env python3
"""xchain_bridge_model.py — deterministic cross-chain bridge risk model.

Usage:
    python3 src/xchain_bridge_model.py [--help]

Reads configs/scenarios.json and writes:
    outputs/derived/xchain-bridge-results.json
    outputs/derived/scenario-matrix.json

Every number comes from the scenario inputs plus the pinned-code
constants in configs/scenarios.json (at most 8 witnesses, 32 with
ExpandedSignerList; at least 1 witness; quorum between 1 and the total
signer weight; at most 128 account-create claims outstanding; claim IDs
are a per-bridge uint32 counter starting at 1). No live node is
involved, no timestamps are recorded, and no wall-clock time is
measured: re-running produces byte-identical outputs.

Outcome rules (each is a direct application of a pinned rule):
  - No signer list on the door: every attestation fails with
    tecXCHAIN_NO_SIGNERS_LIST, so no claim can reach quorum (halted).
  - Claim ID counter at its maximum (4294967295): the next
    XChainCreateClaimID overflows and fails with tecINTERNAL (halted).
  - Replay after a successful claim: the claim ID was destroyed when
    funds moved, so the replay finds no claim ID (safe).
  - Out-of-order account-create claim: rejected, no funds move (safe).
  - Reward pool unfunded at claim time: quorum is reached, then
    finalize fails with tecUNFUNDED_PAYMENT; the main transfer is
    rolled back and the claim is kept for a retry (degraded).
  - Door master key compromised: if the master key was never disabled,
    the attacker signs door transactions directly and bypasses witness
    quorum (exploited); if it was disabled, the stolen key signs
    nothing (safe).
  - Inflated reward: an attestation's reward amount must match the
    quorum subset to join it, so a minority of inflated attestations
    is excluded and the honest subset finalizes on the correct reward
    (safe); a quorum agreeing on an inflated reward is paid it
    (exploited).
  - Quorum math (equal weights of 1): colluding weight at or above
    quorum steals the door's funds (exploited); honest weight at or
    above quorum finalizes the real event (safe); otherwise the claim
    waits — halted when the shortfall is permanent (witnesses removed
    from the signer list), degraded when it is temporary (witnesses
    stalled, or neither side can reach quorum).
  - Rounds: 1 for an outright rejection or a door-key outcome; the
    quorum for a quorum outcome (the q-th attestation completes it);
    all available attestations (at least 1) for a no-quorum outcome.
"""
import json
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent
PINNED_COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def simulate_run(scenario, run, consts):
    p = run["params"]
    n = p["witnesses"]
    q = p["quorum"]
    c = p["colluding"]
    s = p["stalled"]
    r = p["removed"]
    live = n - s - r
    honest = n - c - s - r

    events = [{"round": ev["round"], "text": ev["text"]}
              for ev in run["events"]]

    if p["no_signer_list"]:
        outcome = "halted"
        reason = "no_signer_list_on_door"
        rounds = 1
        events.append({"round": 1, "text": "tecXCHAIN_NO_SIGNERS_LIST: no attestation can be validated"})
    elif p["claim_id_at_max"]:
        outcome = "halted"
        reason = "claim_id_counter_at_maximum"
        rounds = 1
        events.append({"round": 1, "text": "next claim ID overflows the uint32 counter: tecINTERNAL"})
    elif p["replay_after_success"]:
        outcome = "safe"
        reason = "claim_id_destroyed_after_funds_moved"
        rounds = 1
        events.append({"round": 1, "text": "replayed claim finds no claim ID object: tecXCHAIN_NO_CLAIM_ID"})
    elif p["out_of_order"]:
        outcome = "safe"
        reason = "out_of_order_account_create_claim_rejected"
        rounds = 1
        events.append({"round": 1, "text": "createCount must equal claimCount + 1: rejected"})
    elif p["reward_unfunded"]:
        outcome = "degraded"
        reason = "reward_pool_unfunded_claim_kept_for_retry"
        rounds = q
        events.append({"round": q, "text": "quorum reached, then finalize fails tecUNFUNDED_PAYMENT: main transfer rolled back, claim kept"})
    elif p["door_key_compromised"]:
        if p["master_disabled"]:
            outcome = "safe"
            reason = "disabled_master_key_cannot_sign"
            rounds = 1
            events.append({"round": 1, "text": "disabled master key signs nothing: witness quorum still gates the funds"})
        else:
            outcome = "exploited"
            reason = "door_master_key_bypasses_quorum"
            rounds = 1
            events.append({"round": 1, "text": "attacker signs door transactions directly: no witness needed"})
    elif p["reward_inflated"]:
        if p["reward_inflated_by"] >= q:
            outcome = "exploited"
            reason = "quorum_agrees_on_inflated_reward"
            rounds = q
            events.append({"round": q, "text": "a quorum of attestations agrees on the inflated reward: the door pays it"})
        else:
            outcome = "safe"
            reason = "inflated_reward_excluded_from_quorum_subset"
            rounds = q
            events.append({"round": q, "text": "inflated attestation does not match the quorum subset on reward amount: excluded"})
    elif c >= q:
        outcome = "exploited"
        reason = "colluding_weight_reaches_quorum"
        rounds = q
        events.append({"round": q, "text": f"colluding weight {c} reaches quorum {q}: forged event finalizes"})
    elif honest >= q:
        outcome = "safe"
        reason = "honest_weight_reaches_quorum"
        rounds = q
        events.append({"round": q, "text": f"honest weight {honest} reaches quorum {q}: real event finalizes"})
    elif r > 0:
        outcome = "halted"
        reason = "signer_list_removal_makes_quorum_unreachable"
        rounds = max(1, honest + c)
        events.append({"round": rounds, "text": f"live weight {live} is below quorum {q} and cannot recover without a signer-list change"})
    else:
        outcome = "degraded"
        reason = "neither_side_reaches_quorum"
        rounds = max(1, honest + c)
        events.append({"round": rounds, "text": f"honest weight {honest} and colluding weight {c} are both below quorum {q}: claim waits"})

    return {
        "label": run["label"],
        "title": run["title"],
        "params": p,
        "outcome": outcome,
        "reason": reason,
        "witnesses": n,
        "quorum": q,
        "colluding": c,
        "stalled": s,
        "removed": r,
        "honest_weight": honest,
        "live_weight": live,
        "rounds": rounds,
        "events": events,
    }


def main():
    if "--help" in sys.argv[1:]:
        print(__doc__.strip())
        print("\nusage: python3 src/xchain_bridge_model.py [--help]")
        return 0
    sc = load_json(PACK_ROOT / "configs" / "scenarios.json")
    consts = sc["constants"]
    assert sc.get("pinned_commit") == PINNED_COMMIT, "scenarios pinned_commit mismatch"
    assert sc.get("schema_version") == 1, "scenarios schema_version != 1"

    results_scenarios = []
    matrix_rows = []
    totals = {"scenarios": 0, "runs": 0, "safe": 0, "degraded": 0,
              "exploited": 0, "halted": 0}
    for scenario in sc["scenarios"]:
        runs = [simulate_run(scenario, run, consts)
                for run in scenario["runs"]]
        results_scenarios.append({
            "id": scenario["id"],
            "title": scenario["title"],
            "runs": runs,
        })
        totals["scenarios"] += 1
        for run in runs:
            totals["runs"] += 1
            totals[run["outcome"]] += 1
            matrix_rows.append({
                "scenario": scenario["id"],
                "run": run["label"],
                "witnesses": run["witnesses"],
                "quorum": run["quorum"],
                "colluding": run["colluding"],
                "stalled": run["stalled"],
                "removed": run["removed"],
                "outcome": run["outcome"],
                "reason": run["reason"],
                "honest_weight": run["honest_weight"],
                "live_weight": run["live_weight"],
                "rounds": run["rounds"],
            })

    threshold_table = []
    for n, q in ((1, 1), (3, 2), (5, 3), (7, 4), (8, 5), (8, 4), (32, 17)):
        boundary = q - 1
        honest_at_boundary = n - boundary
        honest_reaches = honest_at_boundary >= q
        outcome_at_boundary = "safe" if honest_reaches else "degraded"
        threshold_table.append({
            "witnesses": n,
            "quorum": q,
            "colluding_at_boundary": boundary,
            "honest_at_boundary": honest_at_boundary,
            "honest_reaches_quorum": honest_reaches,
            "outcome_at_boundary": outcome_at_boundary,
            "min_colluding_to_exploit": q,
        })

    limits_table = [
        {"item": "maximum witnesses", "value": consts["max_witnesses"], "unit": "signers"},
        {"item": "maximum witnesses with ExpandedSignerList", "value": consts["max_witnesses_expanded"], "unit": "signers"},
        {"item": "minimum witnesses", "value": consts["min_witnesses"], "unit": "signer"},
        {"item": "minimum quorum", "value": consts["quorum_min"], "unit": "weight"},
        {"item": "maximum quorum", "value": "total signer weight", "unit": "weight"},
        {"item": "minimum witness count enforced by bridge code", "value": None, "unit": "none: 1-of-1 allowed"},
        {"item": "account-create claim window", "value": consts["account_create_max"], "unit": "claims"},
        {"item": "account-create claims outstanding at most", "value": consts["account_create_max"] - 1, "unit": "claims"},
        {"item": "first claim ID", "value": consts["claim_id_first"], "unit": "id"},
        {"item": "maximum claim ID", "value": consts["claim_id_max"], "unit": "id"},
        {"item": "claim ID expiry", "value": None, "unit": "none: claims never expire"},
        {"item": "attestation throttle", "value": None, "unit": "none beyond the ledger transaction fee"},
        {"item": "reward currency", "value": "XRP", "unit": "currency"},
        {"item": "minimum account-create amount scope", "value": "XRP-XRP bridges only", "unit": "scope"},
    ]

    results = {
        "pack": "Cross-Chain Bridge Risk in postfiatd",
        "pinned_commit": PINNED_COMMIT,
        "constants": consts,
        "scenarios": results_scenarios,
        "totals": totals,
        "threshold_table": threshold_table,
        "limits_table": limits_table,
    }
    matrix = {"rows": matrix_rows, "totals": totals}

    outdir = PACK_ROOT / "outputs" / "derived"
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "xchain-bridge-results.json", "w") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(outdir / "scenario-matrix.json", "w") as fh:
        json.dump(matrix, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"simulator: {totals['scenarios']} scenarios, {totals['runs']} runs")
    print(f"simulator: safe {totals['safe']}, degraded {totals['degraded']}, "
          f"exploited {totals['exploited']}, halted {totals['halted']}")
    print("simulator: wrote outputs/derived/xchain-bridge-results.json")
    print("simulator: wrote outputs/derived/scenario-matrix.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
