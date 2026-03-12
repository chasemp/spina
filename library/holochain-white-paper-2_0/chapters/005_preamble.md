---
images: []
order: 5
title: Preamble
---

In the frame of the Byzantine Generals Problem, the correctness of a distributed coordination system is analyzed through the lens of "fault tolerance". In our frame we take on a broader scope and address the question of the many kinds of confidence necessary for a system's adoption and continued use. We identify and address the following dimensions of confidence:

- 1. **Fault Tolerance:** the system's resilience to external perturbations, both malicious and natural. Intrinsic integrity.
- 2. **Completeness/Fit:** the system's *a priori* design

- elements that demonstrate fitness for purpose. We demonstrate this by describing how Holochain addresses multi-agent reality binding, scalability, and shared-state finality.
- 3. **Security:** the system's ability to cope with intentional disruption by malicious action, beyond mere detection of faults.
- 4. **Evolvability:** the system's inherent architectural affordances for increasing confidence over time, especially based on data from failures of confidence in the above dimensions.

Our claim is that if all of these dimensions are sufficiently addressed, then the system takes on the properties of antifragility; that is, it becomes more resilient and coherent in the presence of perturbations rather than less.

#### Fault Tolerance

In distributed systems much has been written about Fault Tolerance especially to those faults known as "Byzantine" faults. These faults might be caused by either random chance or by malicious action. For aspects of failures in system confidence that arise purely from malicious action, see the [Security](#page-12-0) section.

- 1. **Faults from unknown data provenance:** Because all data transmitted in the system is generated and cryptographically signed by Agents, and those signatures are also included in the hash-chains, it is always possible to verify any datum's provenance. Thus, faults from intentional or accidental impostors is not possible. The system cannot prevent malicious or incautious actors from stealing or revealing private keys, however, although it does include affordances to deal with these eventualities. These are discussed under [Human](#page-13-0) Error.
- 2. **Faults from data corruptibility in transmission and storage:** Because all state data is stored along with a cryptographic hash of that data, and because all data is addressed and retrieved by that hash and can be compared against the hash, the only possible fault is that the corruption resulted in data that has the same hash. For Blake2b-256 hashing (which is what we use), this is known to be a vanishingly small possibility for both intentional and unintentional data corruption.[ˆcorruption] Furthermore, because all data is stored as hash-chains, it is not possible for portions of data to be retroactively changed. Agents' Source Chains thus become immutable append-only event logs.

One possible malicious act that an Agent can take is to roll back their chain to some point and start publishing different data from that point forward. But because the publishing protocol requires Agents to also publish all of their Actions to the neighborhood of their own public key, any Actions that lead to a forked chain will be easily and immediately

detected by simply detecting more than one action linked to the same previous action.

It is also possible to unintentionally rollback one's chain. Imagine a setting where a hard-drive corruption leads to a restore from an outdated backup. If a user starts adding to their chain from that state, it will appear as a rollback and fork to validators.

Holochain adds an affordance for such situations in which a good-faith actor can add a Record repudiating such an unintentional chain fork.

3. **Faults from temporal indeterminacy:** In general these faults do not apply to the system described here because it only relies on temporality where it is known that one can rely on it; i.e., when recording Actions that take place locally as experienced by an Agent. As these temporally recorded Actions are shared into the space in which nodes may receive messages in an unpredictable order, the system still guarantees eventual consistency (though not uniform global state) because of the intrinsic integrity of recorded hash-chains and deterministic validation. Additionally, see the [Multi-agent](#page-10-0) reality binding [\(Countersigning\)](#page-10-0) section for more details on how some of the use cases addressed by consensus systems are handled in this system.
