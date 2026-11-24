# Gap register

Questions the pinned source alone cannot answer. Each gap is a
source-only limitation: it names what is unknown, why it is unknown,
and what would close it.

| Gap | Gap | Why it is open | What would close it |
| --- | --- | --- | --- |
| G-01 | No live node run; all attack outcomes are simulator outputs. | No live node was run in this pack. | A live node run against a controlled attacker, or a multi-node testnet with hostile witnesses. |
| G-02 | No measurement of real witness attestation latency or independence. | Latency and independence are live-network data, not code. | Witness-server logs over weeks, reporting attestation delays and key-holder overlap. |
| G-03 | No data on deployed bridge configurations (witness counts, quorums, master-key state). | Deployed configurations are off-ledger choices, not code. | A survey of live bridges, or on-ledger reads of door signer lists and master-key flags. |
| G-04 | The bridge spec document referenced in the code header (`docs/bridge/spec.md`) is not in the pinned checkout. | The file does not exist in the pinned tree. | The spec document from the upstream repository, or the XRPL docs pages cited in `docs/citations.md`. |
| G-05 | Reward-pool funding behaviour under real claim-owner balance changes unmeasured. | Owner balances change live, not in code. | Live claim traces showing reward funding at claim time. |
| G-06 | The account-create claim-burn case (F-08) was not exercised against a live ledger. | It needs a live bridge with a failing destination. | A controlled account-create commit to a destination that cannot receive, on a testnet bridge. |
| G-07 | The witness-server software itself was not audited here; only the on-ledger checks are. | The witness server is a separate program (`xbridge_witness`), outside the pinned tree. | A read of the witness-server source and its signing-key handling. |
| G-08 | Counterparty-chain reorganisation behaviour is out of scope: no reorg handling exists in the pinned bridge code. | `reorg` has 0 hits in the bridge code (probe I-01); confirmation depth is a witness-server concern. | A read of the witness server's confirmation logic plus reorg data from the counterparty chain. |
