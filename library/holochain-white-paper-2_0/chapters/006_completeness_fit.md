---
images: []
order: 6
title: Completeness/Fit
---

Multi-agent reality binding (Countersigning)

<span id="page-10-0"></span>The addition of the single feature of Countersigning to Holochain enables our eventually consistent framework to provide most of the consensus assurances people seek from decentralized systems. Countersigning provides the capacity for specific groups of agents to mutually sign a single state-change on all their respective source-chains. It makes the deterministic validity of a single Entry require the cryptographic signatures of multiple agents instead of just one. Furthermore any slow-downs necessary to add coordinated countersigned entries are not just localized to the DNA involved, they are also localized to just the parties involved. The same parties can continue to interact in other DNAs.

The following are common use cases for countersigning:

• **Multi-Agent State Changes:** Some applications require changes that affect multiple agents simultaneously. Consider the transfer of a deed or tracking a chain of custody, where Alice transfers ownership or custody of something to Bob and they want to produce an **atomic change across both of their source chains**. We must be able to prevent indeterminate states like Alice committing a change releasing an item without Bob having taken possession yet, or Bob committing an entry acknowledging possession while Alice's release fails to commit. Holochain provides a countersigning process for multiple agents to momentarily lock their chains while

they negotiate one matching entry that each one commits to their chain. An entry which has roles for multiple signers requires signed chain Actions from each counterparty to enter the validation process. This ensures no party's state changes unless every party's state changes.

- **Cryptocurrencies Based on P2P Accounting:** Extending the previous example, if Alice wants to transfer 100 units of a currency to Bob, they can both sign a single entry where Alice is in the spender role, and Bob the receiver. This provides similar guarantees as familiar double-entry accounting, ensuring changes happen to both accounts simultaneously. Someone's balance can be easily computed by replaying the transactions on their source chain, and both signing parties can be held accountable for any fraudulent transfers that break the data integrity rules of the currency application. There's no need for global time of transactions when each is clearly ordered by its sequence in the chains of the only accounts affected by the change.
- **Witnessed Authoritative Sequence:** Some applications may require an authoritative sequence of changes to a specific data type. Consider changes to membership of a group of administrators, where Carol and David are both members of the group, and Carol commits a change which removes David from the group, and David commits a change which removes Carol. With no global time clock to trust, whose change wins? An application can set up a small pool of N witnesses and configure any change to be the result of a countersigning session that requires M optional witnesses (where M > 50% of N). Whichever action the witnesses sign first would prevent the other action from being signed, because either Carol or David would have been successfully removed and would no longer be authorized participate in a countersigning session to remove the other.
- **Exclusive Control of Rivalrous Data:** Another common need for an authoritative time sequence involves determining control of rivalrous data such as name registrations. Using M of N signing from a witness pool makes it easy to require witnessing for only rivalrous data types, and forgo the overhead of witnessing for all other data. For example, a Twitter-like app would not need witnessing for tweets, follows, unfollows, likes, replies, etc, only for registration of new usernames and for name changes. This preserves the freedom for low-overhead and easy scaling by not forcing consensus to be managed on non-rivalrous data (which typically comprises the majority of the data in web apps).
- **Generalized Micro-Consensus: Entwined multi-agent state change:** Even though Holochain is agent-centric and designed to make

only local state changes, the countersigning process may be seen as an implementation of Byzantine consensus applied to specific data elements or situations. Contextual countersigning is exactly what circumvents the need for global consensus in Holochain applications.

#### Scaling

Holochain's architecture is specifically designed to maintain resilience and performance as both the number of users and interactions increase. Key factors contributing to its scaling capabilities include:

- 1. Agent-centric approach: Unlike traditional blockchain systems, which require global consensus before progressing, Holochain adopts an agent-centric approach where changes made to an agent's state become authoritative once stored on their chain, signed, and communicated to others via the DHT. As a result, agents are able to initiate actions without delay and in parallel to other agents initiating their own actions.
- 2. Bottleneck-Free Sharded DHT: Holochain's DHT is sharded, meaning that each node only stores a fraction of the total data, reducing the storage and computational requirements for each participant. At the same time, the storage of content with agents whose public key is "near" the hash of each Action or Entry, in combination with the use of Linking metadata attached to such hashes, transforms the DHT into a graphing DHT in which data discovery is simple in spite of the sparseness of the address space. When the agents responsible for validating a particular state change receive an authoring agent's proposed state change, they are able to:
  - 1. Request information from others in the DHT regarding the prior state of the authoring agent (where relevant), and
  - 2. Make use of their own copy of the app's validation rules to deterministically validate the change.

While that agent and its validating peers are engaged with the creation and validation of a particular change to the state of the authors chain, in parallel, other agents are able to author state changes to their own chain and have these validated by the validating peers for each of those changes. This bottle-neck free architecture allows users to continue interacting with the system without waiting for global agreement.

With singular actions by any particular agent (and the validation of those actions by a small number of other agents) able to occur simultaneously with singular actions by other agents as well as countersigned actions by particular groups of agents, he net-

- work is not updating state globally (as blockchains typically do) but is instead creating, validating, storing, and serving changes of the state of particular agents in parallel.
- 3. Multiple networks: In Holochain, each application (DNA) operates on its own independent network, effectively isolating the performance of individual apps. This prevents a high-traffic, data-heavy, or processing-heavy app from affecting the performance of other lighter apps within the ecosystem. Participants are able to decide for themselves which applications they want to participate in.
- 4. Order of Complexity: "Big O" notation is usually only applied to local computation based on handling n number of inputs. However, we may consider a new type of O-notation for decentralized systems which includes two inputs, n as the number transactions/inputs/actions, and m as the number of nodes/peers/agents/users, as a way of expressing the time complexity for both an individual node and for the aggregate power of the entire network of nodes. Most blockchains are some variant of  $\mathcal{O}(n^2 * m)$  in their order of complexity. Every node must gossip and validate all state changes. However, Holochain retains a constant  $\mathcal{O}(\frac{log(n)}{m})$  complexity for any network larger than a given size R, where Ris the sharding threshold. As the number of nodes in the network grows, each node performs a static workload irrespective of network size; or expressed inversely, a smaller portion of the total network workload.

#### Shared-state Finality

Many blockchains approximate chain finality by assuming that the "longest chain wins." That strategy does not translate well to agent-centric chains, which are simply histories of an agent's actions. While there is no concern about forking global state because a Holochain app doesn't have one, we can imagine a situation where Alice and Bob have countersigned a transaction, then Alice forks her source chain by later committing an Action to an earlier sequence position in her chain. If the timestamp of this new, conflicting Action precedes the timestamp of the transaction with Bob, it could appear that Bob had knowingly participated in a transaction with a malicious actor, putting his own integrity in question. This can even happen non-maliciously when someone suffers data loss and restores from a backup after having made changes that were not included in the backup. While the initial beta version of Holochain does not offer fork finality protections for source chains, later versions will incorporate "meta-data hardening" which enables gossiping peers to tentatively solidify a state of affairs when they see that gossip for a time window has calmed and neighbors have converged on the same state. After this settling period (which might be set to something between 5 to 15 minutes) any later changes which would produce a conflict <span id="page-12-0"></span>(such as forking a chain) can be rejected, preserving the legitimacy of state changes that were made in good faith.

#### Security

The system's resilience to intentional gaming and disruption by malicious actors will be covered in depth in future papers, but here we provide an overview.

Many factors contribute to a system's ability to live up to the varying safety and security requirements of its users. In general, the approach taken in Holochain is to provide affordances that take into account the many types of real-world costs that result from adding security and safety to systems such that application developers can match the trade-offs of those costs to their application context. The integrity guarantees listed in the formal system description detail the fundamental data safety that Holochain applications provide. Some other important facets of system security and safety come from:

- 1. Gating access to functions that change local state, for which Holochain provides a unified and flexible Object Capabilities model
- 2. Detecting and blocking participation of bad actors, including attempts to flood a DHT with otherwise valid data, for which Holochain provides the affordances of validation and warranting.
- 3. Protection from attack categories
- 4. Resilience to human error

Gating Access via Cryptographic Object Capabilities

To use a Holochain application, end-users must trigger Zome Calls that effect local state changes on their Source Chains. Additionally, Zome Functions can make calls to other Zome Functions on remote nodes in the same app, or to other DNAs running on the same Conductor. All of these calls must happen in the context of some kind of permissioning system. Holochain's security model for calls is based on the Object-capability[16](#page-12-1) security model, but augmented for a distributed cryptographic context in which we use cryptographic signatures to prove the necessary agency for taking action.

Access is thus mediated by Capability Grants of four types:

- **Author**: only the agent owning the source change can make the zome call
- **Assigned**: only the specified public key holders can make the zome call, as verified by a signature on the function call payload
- **Transferrable**: anybody with the given secret can make the zome call

• **Unrestricted**: anybody can make the zome call (no secret nor proof of authorized key needed to use this capability)

All zome calls must be signed and also take a required capability claim parameter that MUST be checked by the system for making the call. Agents record capability grants on their source chains and distribute their corresponding secrets as applicable according to the application's needs. Receivers of secrets can record them as private capability claim entries on their chains for later lookup and use. The "agent" type grant is just the agent's public key.

#### Validation & Warranting

We have already covered how Holochain's agent-centric validation and intrinsic data integrity provides security from malicious actors trying to introduce invalid or incorrect information into an Application's network, as every agent can deterministically verify data and thus secure itself. It is also important, however, to be able to eject malicious actors from network participation who generate or propagate invalid data, so as to proactively secure the network against the resource drain that future such actions from those actors may incur.

As agents publish their actions to the DHT, other agents serve as validators. When validation passes, they send a validation receipt back to the authoring agent, so they know the network has seen and stored their data. When validation fails, they send a negative validation receipt, known as a warrant, back to the author and their neighbors so the system can propagate these provably invalid attempted actions. This also flags the offending agent as corrupted or malicious so that other nodes can block them and stop interacting with the offending agent. Every node can confirm the warrant for themselves, as it is justified by the shared deterministic validation rules, of which all agents have a copy.

This enables a dynamic whereby any single honest agent can detect and report any invalid actions. So instead of needing a majority consensus to establish reliability of data (an "N/2 of N" trust model), Holochain enables "one good apple to heal the bunch" with a "1 of N" trust model for any data you acquire from agents on the network.

For even stricter situations, apps can achieve a "0 of N" trust model, where no external agents need to be trusted, because nodes can always validate data for themselves, independent of what any other nodes say.

#### Security from Attack Categories

*Consensus Attacks* This whole category of attack starts from the assumption that consensus is required for distributed systems. Because Holochain doesn't start from that assumption, the attack category really doesn't apply, but it's worth mentioning because there are a number of attacks on blockchain which threaten confidence in the reliability of the chain data through collusion between

<span id="page-12-1"></span><sup>16</sup> See [https://en.wikipedia.org/wiki/Object-capability/\\_model](https://en.wikipedia.org/wiki/Object-capability/_model)

some majority of nodes. The usual thinking is that it takes a large number of nodes and massive amounts of computing power or financial incentives to prevent undue hijacking of consensus. However, since Holochain's data coherence doesn't derive from all nodes awaiting consensus, but rather on deterministic validation, nobody ever needs to trust a consensus lottery.

*Sybil Attacks* Since Holochain does not rely on any kind of majority consensus, it is already less vulnerable to Sybil Attacks, the creation of many fake colluding accounts which are typically used to overwhelm consensus of honest agents. And since Holochain enables "1 of N" and even "0 of N" trust models, Sybils cannot entirely overwhelm honest agents' ability to determine the validity of data.

Additionally, since Holochain is a heterogeneous environment in which every app operates on its own isolated network, a Sybil Attack can only be attempted on a single app's network at a time. For each app, an appropriate membrane can be defined on a spectrum from very open and permissive to closed and strict by defining validation rules on a Membrane Proof.

A membrane proof is passed in during the installation process of an agent's instance of the app, so that the proof can be committed to the agent's chain just ahead of their public key. An agent's public key acts as their address in that application's DHT network, and is created during the genesis process in order to join the network. Other agents can confirm whether an agent may join by validating the membership proof.

A large variety of membrane proofs is possible, ranging from none at all, loose social triangulation, or an invitation from any current user, to stricter invitation lists, proofof-work requirements, or a kind of proof-of-stake showing the agent possesses and has staked some value which they lose if their account gets warranted.

We generally suggest that applications may want to enforce some kind of membrane against Sybils, not because consensus or data integrity are at risk but because carrying a lot of Sybils makes unnecessary work for honest agents running an application. We cover more about this in the next section.

*Denial-of-Service Attacks* Holochain is not systemically subject to denial-of-service attacks because there is no central point to attack. Because each application is its own network, attackers would have to flood every agent of every application to carry out a systemic denial-of-service attack; to do that would require knowing who all those agents are, which is also not recorded in one single place. One point of vulnerability is the bootstrap servers for an application. But this is not a systemic vulnerability, as each application can designate its own bootstrap server, and they can also be arbitrarily hardened against denialof-service to suit the needs of the application.

*Eclipse Attacks* An Eclipse Attack happens when a newly joining node is prevented from ever joining the main/honest network because it initially connects to a dishonest node which only ever shares information about other colluding dishonest nodes. This attack is specific to gossip-based peer-to-peer networks such as Bitcoin, Holochain, and DHTs like IPFS.

Holochain apps bypass the risk of an Eclipse Attacks by providing an address for a bootstrap service which ensures your first connection is to a trusted or honest peer. If an application fails to provide a bootstrap service, nodes will try connecting via https://bootstrap.holochain.org which provides initial trusted peers, if those have been specified. If not specified, the default bootstrap service provides random access to any and all peers using the app, which at least ensures nodes cannot be partitioned from honest peers.

<span id="page-13-0"></span>Application developers can take steps to further protect their users by providing in-app methods of exchanging signed pings with known nodes (such as a progenitor, migrator, notary, witness, or initial admin node) so a node can ensure it is not partitioned from the real network. *Human Error* There are some aspects of security, especially those of human error, that all systems are subject to. People will still lose their keys, use weak passwords, get computer viruses, etc. But, crucially, in the realm of "System Correctness" and "confidence," the question that needs addressing is how the system interfaces with mechanisms to mitigate against human error. Holochain provides significant tooling to support key management in the form of its core Distributed Public Key Infrastructure (DPKI) and DeepKey app built on that infrastructure. Among other things, this tooling provides assistance in managing keys, managing revocation methods, and reclaiming control of applications when keys or devices have become compromised.

A definition and specification of a DPKI system is outside of the scope of this paper; see the DeepKey design specification[17](#page-13-1) for a more thorough exploration.
