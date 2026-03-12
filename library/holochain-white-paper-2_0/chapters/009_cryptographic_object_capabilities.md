---
images: []
order: 9
title: Cryptographic Object Capabilities
---

To use a Holochain application, end-users must trigger zome calls that effect local state changes on their Source Chains. Additionally, zome functions can make calls to other zome functions on remote nodes in the same application network, or to other cells running on the same conductor. All of these calls must happen in the context of some kind of permissioning system. Holochain's security model for calls is based on the Object-capability security model[22](#page-28-1), but augmented for a distributed cryptographic context in which we use cryptographic signatures to further prove the necessary agency for taking action and create an additional defense against undesired capability leakage.

Access is thus mediated by Capability Grants of four types:

- **Author**: Only the agent owning the source change can make the zome call. This capability is granted to all zome functions.
- **Assigned**: Only the named agent(s) with the given capability secret can make the zome call.
- **Transferrable**: Anybody with the given capability secret can make the zome call. This is equivalent to the common definition of object-capabilities.
- **Unrestricted**: Anybody can make the zome call (no secret nor proof of authorized key needed to use this capability).

All zome calls must be signed and supply a required capability claim argument that MUST be checked by the

system receiving the call. Agents record capability grants on their source chains and distribute their associated secrets as necessary according to the application's needs. Receivers of secrets can record them as claims (usually as a private entry) on their chains for later lookup. The "agent" type grant is just the agent's public key.

#### Warrants

<span id="page-28-0"></span>We take that, by definition, in a fully distributed system, there is no way for a single agent to control the actions of other agents that comprise the system; i.e., what makes an agent an agent is its ability to act independently. This creates a challenge: How do agents deal with "bad-actor" agents, as they cannot be controlled by another party?

In Holochain "bad-action" is defined by attempts by agents to act in a way inconsistent with a DNA's validation rules. Because a DNA's network ID is defined by the hash of its integrity bundle (which includes both data structures and the deterministic validation rules) we can know that every agent in a network started with the same rules, and thus can deterministically run those rules to determine if any action fails validation. (Note that some validation rules reveal bad actions not just in structure or content of data committed, but also bad behavior. For example, validating timestamps over contiguous sequences of Actions enables detection of and protection against spam and denial-of-service attacks. Holochain has its own base validation rules as well; for instance, a source chain must never 'fork', so the presence of two parallel branching points from one prior source chain record is considered a bad-action.)

Once a bad-action has been identified via a validation failure, it is considered to be unambiguously a consequence of malicious intent. The only way invalid data can be published is by intentionally circumventing the validation process on the author's device when committing to chain.

Each Warrant must be self-proving. It must flag the agent being warranted as a bad actor and include references to set of actions which fail to validate. This might be, for example, a single signed Action that fails validation, or it might be a set of Actions that are issued consecutively which exceed spam rate limits, or a set of Actions that are issued concurrently which cause the agent's chain to fork.

Upon receipt of a Warrant, a node must take three actions:

- 1. **Determine who is the bad actor.** For any Warrant, someone either performed a bad action, or someone created a false report of bad action. So a node must validate the referenced actions. If they fail validation, then the reported agent is the bad actor. If the actions pass validation, then the Warrant author is the bad actor.
- 2. **Block the bad actor.** Add either the warranted agent or the Warrant author to the validating node's peer block list. This node will no longer interact

<span id="page-28-1"></span><sup>22</sup> See [https://en.wikipedia.org/wiki/Object-capability\\_model.](https://en.wikipedia.org/wiki/Object-capability_model)

with bad actor, and will reject any connection attempts from that agent.

3. **Report it to the bad actor's Agent Activity Authorities.** Because nodes expect to be able to find out if an agent is warranted by asking its neighbors who validate its chain activity, those neighbors must be notified of any warrants.

There is no global blocking of a bad actor. Each agent must confirm for themselves whom to block. Warrants and blocking, taken together, enable the network to defend itself from bad actors while preserving individual agency in the warranting process.

Note: Beyond Warrants, blocking can also theoretically be used by apps or agents for whatever reason the application logic or node owner may have to refuse to participate with a node. It allows for local, voluntary self-defense against whatever nodes someone might interpret as malicious, or simply ending communication with peers that are no longer relevant (e.g., a terminated employee).

#### Cross-DNA Composability

Holochain is designed to be used to build micro-services that can be assembled into applications. We expect DNAs to be written that assume the existence of other longrunning DNAs and make calls to them via the agency of a user having installed both DNAs on their node. The Capabilities security model described above makes sure this kind of calling is safe and can only happen when permissions to do so have been explicitly granted in a given context. The HDK call function provides an affordance to allow specification of the DNA by hash when making the call, so the Holochain node can make a zome call to that DNA and return the result to the calling node.
