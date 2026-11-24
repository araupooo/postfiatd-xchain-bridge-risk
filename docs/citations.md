# Citations

Public documentation consulted for the SPECIFIED rules, with verbatim
quotes. Accessed 24 Nov 2026. Each entry notes whether the code
agrees, and where it diverges the pack follows the code.

## S-01 — Attestation transactions: any account can submit signatures

Source: https://xrpl.org/docs/references/protocol/transactions/types/xchainaddaccountcreateattestation
(XRPL.org XChainAddAccountCreateAttestation documentation.)

> "Any account can submit signatures."

Cross-check: agrees with the code — the attestation preclaim checks
the signer against the door's signer list, never the submitting
account (`XChainBridge.cpp:1240-1270`, E16). Rule R-16.

## S-02 — Attestation transactions: signer-list change drops collected signatures

Source: https://xrpl.org/docs/references/protocol/transactions/types/xchainaddaccountcreateattestation
(same page as S-01.)

> "The signature must be from one of the keys on the door's signer list at the time the signature was provided. If the signature list changes between the time the signature was submitted and the quorum is reached, the new signature set is used and some of the currently collected signatures may be removed."

Cross-check: agrees with the code — `claimHelper` erases
attestations whose key is no longer in the signer list
(`XChainBridge.cpp:191-240`, E03). Rule R-26.

## S-03 — Witness servers: anyone can run one; reliability is the issuing chain's burden

Source: https://xrpl.org/docs/concepts/xrpl-sidechains/witness-servers
(XRPL.org witness-servers documentation.)

> "Anyone can run a witness server. However, the burden is on the participants of the issuing chain to evaluate the reliability of witness servers. If you run a witness server, you must also run an `xrpld` node and sync it to the chain the witness server needs access to."

Cross-check: the code has no witness registry and no reliability
check — the only gate is the door's signer list. The docs statement
is a deployment fact, not a code fact. Rule R-42, claim C-17.

## S-04 — Attestation transactions: reward only to current-list accounts; quorum must agree on the reward

Source: https://xrpl.org/docs/references/protocol/transactions/types/xchainaddaccountcreateattestation
(same page as S-01.)

> "The reward is only sent to accounts that have keys on the current list. A quorum of signers need to agree on the `SignatureReward`, the same way they need to agree on the other data. A single witness server can't provide an incorrect value for this in an attempt to collect a larger reward."

Cross-check: agrees with the code for account-create attestations —
the match compares amount, rewardAmount, and chain direction
(`XChainAttestations.cpp:642-652`; no excerpt file for this range).
For claim attestations the reward is fixed by the claim ID object
instead. Rule R-38.

## S-05 — Witness servers: a bridge may start with one witness server

Source: https://xrpl.org/docs/concepts/xrpl-sidechains/witness-servers
(same page as S-03.)

> "Issuing chains may choose to configure a bridge with only one witness server initially and run the witness server itself. This strategy is helpful in the initial period, when the issuing chain hasn't established itself yet in the marketplace."

Cross-check: agrees with the code — no minimum witness count exists
in the bridge code (R-24), so a one-witness bridge is creatable. The
docs statement is a deployment fact, not a code fact. Claim C-18.
