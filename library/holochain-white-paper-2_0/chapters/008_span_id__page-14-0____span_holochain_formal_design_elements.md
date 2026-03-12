---
images:
- _page_23_Figure_1.jpeg
- _page_23_Figure_4.jpeg
- _page_24_Figure_1.jpeg
- _page_24_Figure_3.jpeg
- _page_25_Figure_1.jpeg
order: 8
title: <span id="page-14-0"></span>Holochain Formal Design Elements
---

Now we turn to a more formal and detailed presentation of the Holochain system, including assumptions, architecture, integrity guarantees, and formal state model.

<span id="page-14-1"></span><sup>18</sup> We use the term "grammatic" as a way to generalize from the usual understanding of grammar which is linguistic. Where grammar is often understood to be limited to language, grammatics points to the pattern of creating templates with classes of items that can fill slots in those templates. This pattern can be used for creating "grammars" of social interaction, "grammars" of physical structures (we would call Christopher Alexander's "A Pattern Language" for architecture an example of grammatics), and so on.

**Purpose of this Section:** To provide an understanding of the functional requirements of Holochain and specify a technical implementation of the cryptographic state transitions and application processes that enforce Holochain's integrity guarantees.

#### Definition of Foundational Principles

- **Cryptography:** Holochain's integrity guarantees are largely enabled by cryptography. It is used in three main ways.
  - **– Hashes:** Data is uniquely identified by its hash, which is the key used to retrieve the data from a Content Addressable Store.
  - **– Signing:** Origination of data (for all storage and network communications) is verified by signing a hash with a private key.
  - **– Encryption:** Data is encrypted at rest and on the wire throughout the system.
- **Agency:** Holochain is agent-centric. Each and every state change is a result of:
  - 1. A record of an agent's action,
  - 2. signed by the authoring agent,
  - 3. linearly sequenced and timestamped
  - 4. to their local source chain.

Each agent is the sole authority for managing its local state (by virtue of controlling their private key required for signing new actions to their source chain).

- **Accountability:** Holochain is also socio-centric. Each Holochain application defines its set of mutually enforced data integrity rules. Every local state change gets validated by other agents to ensure that it adheres to the rules of that application. Peers also enforce limits on publishing rates, protect against network integrity threats, and can ban rule-breakers by a process we call *warranting*.
- **Data:** Unlike some other decentralized approaches, in Holochain, data does not have first-order, independent, ontological existence. Every record in the shared DHT network space MUST CARRY its provenance from a local source chain as described below.
- **Provenance:** Each record created in a Holochain application starts as an action pair on someone's local source chain. As such, even when published to the shared DHT, records must carry the associated public key and signature of the agent who created it. This means every piece of data carries meta-information about where that data came from (who created it, and in what sequence on the their chain). Note: In other hash-chain based systems Holochain's "actions" are often called "headers," which link to the previous headers to create the chain. In Holochain, while the action does establish

<span id="page-14-2"></span><sup>19</sup> A number of projects in the Holochain ecosystem are already exhibiting this characteristic of evolvability, such as The Weave / Moss (see [https://theweave.social\)](https://theweave.social), Ad4m [\(https://ad4m.dev/\)](https://ad4m.dev/), Memetic Activation Platform (see [https://github.com/evomimic/we-all-map/wiki/MAP-](https://github.com/evomimic/we-all-map/wiki/MAP-Overview)[Overview\)](https://github.com/evomimic/we-all-map/wiki/MAP-Overview).

temporal order, its core function is to record an act of agency, that of "speaking" data into existence.

- **State:** State changes in Holochain are local (signed to a local *Source Chain*) and then information about having created a local state change is shared publicly on the DHT. This allows global visibility of local state changes, without a need to manage consensus about a global state, because there is truly no such thing as global state in a system that allows massive, simultaneous, decentralized change.
- **Time:** There is no global time nor global absolute sequence of events in Holochain either. No global time is needed for local state changes, and since each local change is stored in a hash chain, we get a clear, immutable, sequence of actions tagged with local timestamps. (Note: For apps that need some kind of time proof to interface with the outside world (e.g. token or certificate expiration timestamps) we plan to provide a time proof service that replaces the need for centrally trusted timeservers.)

#### System Architecture Overview

In Holochain every app defines a distinct, peer-to-peer, encrypted network where one set of rules is mutually enforced by all users. This network consists of the peers running the app, who participate in routing messages to each other and validating and storing redundant copies of the application's database.

Holochain operates different subsystems, each of which functions on separate workflows and change models. Even though Holochain functions as a common underlying database on the back-end, the workflows in each subsystem each have different input channels which trigger different transformational processes. Each workflow has distinct structural bottlenecks and security constraints, which necessitates that execution of workflows is parallelized across subsystems, and sometimes within a subsystem.

- 1. **Local Agent State:** Represented as changes to an agent's state by signing new records with their private key, and committing them to a local hash chain of their action history called a Source Chain. Initial chain genesis happens upon installation/activation, and all following changes result from "zome calls" into the app code.
- 2. **Global Visibility of Local State Changes:** After data has been signed to a Source Chain it gets published to a Graphing DHT (Distributed Hash Table) where it is validated by the peers who will store and serve it. The DHT is continually balanced and healed by gossip among the peers.
- 3. **Network Protocols:** Holochain instantiates the execution of app DNA on each node under the agency identified by the public key, transforming code into a collective networked organism. An agent's public key *is* their network address, and is

- used as the to/from target for remote zome calls, signals, publishing, and gossip. Holochain is transportagnostic, and can operate on any network transport protocol which a node has installed for routing, bootstrapping, or proxying connections through NAT and firewalls.
- 4. **Distributed Application:** Apps are compiled and distributed into WebAssembly (WASM) code bundles which we call a DNA. Data integrity is enforced by the validation defined in an app's DNA, which is composed of data structures, functions, and callbacks packaged in Zomes (short for chromosome) which function as reusable modules. DNAs are coupled with an Agent's public key and activated or instantiated into a Cell. Installation and activation status of these bundles is managed by a runtime container.

#### Some notes on terminology

*Biological Language* We have chosen biological language to ground us in the pattern of collective distributed coherence that we observe in biological organisms. This is a pattern in which the agents that compose an organism (cells) all start with the same ground rules (DNA). Every agent has a copy of the rules that *all* the other agents are playing by, clearly identifying membership in the collective self based on matching DNA.

This is true of all Holochain DNAs, which can also be combined together to create a multi-DNA application (with each DNA functioning like a distinct micro-service in a more complex application). In a hApp bundle, each DNA file is the complete set of integrity zomes (WASM) and settings whose hash also becomes the first genesis entry in the agent's source chain. Therefore, if the DNA hash in your first chain record does not match mine, we are not cells of the same network organism. A "zome" is a code module, which functions as the basic compositional unit for assembling the complete set of an application's DNA.

When a DNA is instantiated along with a public/private key pair, it becomes a "cell" which is identified by the combination of the DNA hash and the public key.

Students of biology may recognize ways that our language doesn't fully mesh with their expectations. Please forgive any imprecision with understanding of our intent to build better language for the nature of distributed computing that more closely matches biology than typical mechanistic models.

*The Conductor* Much of the discussion below is from the perspective of a single DNA, which is the core unit in Holochain that provides a set of integrity guarantees for binding agents together into a single social context. However, Holochain can also be seen as micro-service provider, with each DNA providing one micro-service. From this perspective, a Holochain node is a running process that manages many connections to many DNAs simultaneously, from user interfaces initiating actions, from other nodes sharing a subset of identical DNAs, and from cells within the same node sharing the same agent ID but bound to different DNAs. Thus, we call a Holochain node the **Conductor** as it manages the information flows from "outside" (UI calls and calls from other local cells) and from "inside" (network interactions) as they flow into and out of the may DNA instances running code. This term was chosen as it suggests the feel of musical coordination of a group, as well as the conduit of an electrical flow. Please see the [Implementation](hwp_A_implementation_spec.md) Spec [\(Appendix](hwp_A_implementation_spec.md) A) for a more detailed on how a complete Holochain Conductor must be built.

#### Integrity Guarantees

Within the context of the Basic Assumptions and the System Architecture both described above, the Holochain system makes the following specific integrity guarantees for a given Holochain DNA and network:

- 1. **State:** Agents' actions are unambiguously ordered from any given action back to genesis, unforgeable, non-repudiable, and immutable (accomplished via local hash chains called a Source Chain, because all data within the network is sourced from these chains.)
- 2. **Self-Validating Data:** Because all DHT data is stored at the hash of its content, if the data returned from a request does not hash to the address you requested, you know you've received altered data.
- 3. **Self-Validating Keys:** Agents declare their address on the network as their public key, and key rotation is subject to rules defined by the agent and enforced by their peers. Peers can confirm any published data or remote call is valid by checking the signature using the from address as the public key.
- 4. **Termination of Execution:** No node can be coerced into infinite loops by non-terminating application code in either remote zome call or validation callbacks. Holochain uses WASM metering to guarantee a maximum execution budget to address the the Halting Problem.
- 5. **Deterministic Validation:** Ensure that only deterministic behaviors (ones that will always get the same result no matter who calls them on what computer) are available in validation functions. An interim result of "missing dependency" is also acceptable, but final evaluation of valid/invalid status for each datum must be consistent across all nodes and all time spans.
- 6. **Strong Eventual Consistency:** Despite network partitions, all nodes who are authorities for a given DHT address (or become one at any point) will eventually converge to the same state for data at that address. This is ensured by the DHT functioning as a conflict-free replicated data type (CRDT).
- 7. **"0 of N" Trust Model:** Holochain is immune to "majority attacks" because any node can always

- validate data for themselves independent of what any other nodes say.[20](#page-16-0)
- 8. **Data Model Scalability:** Because of the overlapping sharding scheme of DHT storage and validation, the total computing power and overall throughput for an application scales linearly as more users join the app.
- 9. **Atomic Zome Calls:** Multiple writes in a single zome call will all be committed in a single SQL transaction or all fail together. If they fail the zome call, they will report an error to the caller and the writes will be rolled back.

Source Chain: Formal State Model

Data in a Holochain application is created by agents changing their local state. This state is stored as an append-only hash chain. Only state changes originated by that agent (or state changes that they are party to in a multi-agent action) are stored to their chain. Source Chains are NOT a representation of global state or changes that others are originating, but only a sequential history of local state changes authored by one agent.

The structure of a Source Chain is that of a hash chain which uses headers (called "actions" in Holochain terms) to connect a series of entries. Each record in the chain is a two-element tuple, containing the action and the entry (if applicable for the action type).

Since the action contains the prior action hash and current entry hash (if applicable), each record is a tamper-proof atomic data element. Additionally, in practice a record is always transmitted along with a signature on the action's hash, signed by the private complement of the public key in the action. This means that anyone can hash the entry content to make sure it hasn't been tampered with, and they can hash the action data and compare the accompanying signature on that hash to ensure it matches the author's public key. The action's chain sequence and monotonic timestamp properties provide further immutable reinforcement of logical chain ordering.

Data in Holochain is kept in Content Addressable Stores which are key-value stores where the key is the hash of the content. This makes all content self-validating, whether served locally or remotely over the DHT. Data can be retrieved by the action hash (synonymous with record hash) or the entry hash.

The code that comprises a Holochain application is categorized into two different types of zomes:

- 1. **Integrity Zomes** which provide the immutable portion of the app's code that:
  - identifies the types of entries and links that may be committed in the app,

<span id="page-16-0"></span><sup>20</sup> See this Levels of Trust Diagram [https://miro.medium.com/max/1248/0\\*k3o00pQovnOWRwtA.](https://miro.medium.com/max/1248/0*k3o00pQovnOWRwtA)

- defines the structure of data entries, and
- defines the validation code each node runs for each type of operation that intends to add to state at a given DHT address.
- 2. **Coordinator Zomes**, the set of which can be removed from or added to while an app is live, and which contain various create, read, update, and delete (CRUD) operations for entries and links, functions related to following graph links and querying collections of data on the DHT, and any auxillary functionality someone wants to bundle in their application.

Each application running on Holochain is uniquely identified by a DNA hash of the integrity zome code, after being compiled to Web Assembly (WASM) and bundled with additional settings and properties required for that app.

*Application Note: Multiple DNA-level apps can be bundled together like interoperating micro-services in a larger Holochain Application (hApp), but the locus of data integrity and enforcement remains at the single DNA level, so we will stay focused on that within this document.*

There are three main types of Zome functions:

- 1. ( *z<sup>f</sup>* ) zome functions which do not alter state.
- 2. ( *Z<sup>f</sup>* ) that can be called to produce state changes, as well as the
- 3. Validation Rules ( *V<sup>R</sup>* ) for enforcing data integrity of any such state changes (additions, modifications, or deletions of data).

$$z_{f_1} \dots z_{f_x} \in \text{Coordinator Zomes}$$
  
 $Z_{f_1} \dots Z_{f_x} \in \text{Coordinator Zomes}$   
 $V_{R_1} \dots V_{R_x} \in \text{Integrity Zomes}$ 

*Note about Functions: Most functionality does not need to be in the immutable, mutually enforced rules included in the DNA hash (Integrity Zomes); only the functionality which validates data ( ( V<sup>R</sup> ) ) does. In practice, including code that does not contribute to data validation ( ( z<sup>f</sup> ), ( Z<sup>f</sup> ) ) in the integrity zome creates a brittle DNA that is difficult to update when bugs are repaired or functionality needs to be introduced or retired.*

The first record in each agent's source chain contains the DNA hash. This initial record is what demonstrates that each agent possessed, at installation time, identical and complete copies of the the rules by which they intend to manage and mutually enforce all state changes. If a source chain begins with a different DNA hash, then its agent is in a different network playing by a different set of rules.

**Genesis:** The genesis process for each agent creates three initial entries.

1. The hash of the DNA is stored in the first chain record with action *C*<sup>0</sup> like this:

$$C_0 = WASM \begin{Bmatrix} a_{DNA} \\ e_{DNA} \end{Bmatrix}$$

2. Followed by a "Membrane Proof" which other nodes can use to validate whether the agent is allowed to join the application network. It can be left empty if the application membrane is completely open and it doesn't check or use proofs of membership.

$$C_1 = \begin{Bmatrix} a_{mp} \\ e_{mp} \end{Bmatrix}$$

3. And finally the agent's Public Key that they have generated, which also becomes their address on the network and DHT. Keys are the only entry type for which the hash algorithm is equality (meaning the hash of a key is the key itself, so it cannot contain any content other than the public key).

$$C_2 = \begin{Bmatrix} a_K \\ e_K \end{Bmatrix}$$

**Initialization:** After genesis, DNAs may have also provided initialization functions which are all executed the first time an inbound zome call is received and run. This delay in initialization is to allow time for the application to have joined and been validated into the network, just in case initialization functions may need to retrieve some data from the network.

Initialization functions may write entries to the chain, send messages, or perform any variety of actions, but after all coordinator zomes' initialization functions (according to the order they were bundled together) have successfully completed their initializations, an InitZomesComplete action is written to the source chain, so that it will not re-attempt initialization, thus preventing any redundant side-effects.

**Ongoing Operation via Calls to Zome Functions:** All changes following genesis and initialization occur by Zome call to a function contained in a Coordinator Zome in the following form:

$$Z_c = \{Z_f, Params, CapTokenSecret\}$$

Where *Z<sup>f</sup>* is the Zome function being called, *P arams* are the parameters passed to that Zome function, and *CapT okenSecret* references the capability token which explicitly grants the calling agent the permission to call that function.

Based on the interface connection and state when the Zome call is received we construct a context which provides additional necessary parameters to validate state transformation:

$$Context(Z_c) = \{Provenance, C_n\}$$

Provenance contains the public key of the caller along with their cryptographic signature of the call as proof that it originated from the agent controlling the associated private key.

 $C_n$  is the Source Chain's latest action at the time we begin processing the zome call. The Zome call sees (and potentially builds upon) a snapshot of this state through its lifetime, and validation functions will all be called "as at" this state. Since multiple simultaneous zome calls might be made, tracking the "as at" enables detection of another call having successfully changed the state of the chain before this call completed its execution, at which point any actions built upon the now-obsolete state may need to be reapplied to and validated on the new state. Zome Calls & Changing Local State First, Holochain's "subconscious" security system confirms CapTokenSecret permits the agent identified by the *Provenance* to call the targeted function. It returns a failure if not. Otherwise it proceeds to further check if the function was explicitly permitted by the referenced capability token.

Note on Permissions: Capability tokens function similarly to API keys. Cap token grants are explicitly saved as private entries on the granting agent's source chain and contain a secret used to call them. Cap token claims containing the secret are saved on the calling agent's chain so they can be used later to make calls that execute the capabilities that have been granted.

If the Zome call is one which alters local state (distinct from a call that just reads from the chain or DHT state), we must construct a bundle of state changes that will attempt to be appended to the source chain in an atomic commit:

$$\Delta_C(C_n, Z_c) = \begin{cases} a_I & a_{II} & \dots & a_x \\ e_I & e_{II} & \dots & e_x \end{cases}$$

where a Chain is composed of paired actions,  $a_x$ , and entries,  $e_x$ .

The next chain state is obtained by appending the changes produced by a zome call to the state of the chain at that point.

$$C_n = C_n + \Delta_C(C_n, Z_c)$$

If the validation rules pass for these state changes and the current top of chain is still in state  $C_n$  then the transaction is committed to the persistent store, and the chain is updated as follows:

$$C_n = \begin{cases} a_{DNA} & \dots & a_n \\ e_{DNA} & \dots & e_n \end{cases}$$

If the validation rules fail, the deltas will be rejected with an error. Also, if the chain state has changed from  $C_n$ , we can:

- 1. return an error (e.g. "Chain head has moved"),
- 2. commit anyway, restarting the validation process at a new "as at"  $C'_n$  if the commit is identified as "stateless" in terms of validation dependencies (e.g., a tweet generally isn't valid or invalid because of prior tweets/state changes). We refer to any application entry types that can be committed this way as allowing "relaxed chain ordering".

Note about Action/Entry Pairs: This paired structure of the source chain holds true for all application data. However, certain action types defined by the system, whose entry payloads are small or require metadata that is additional to primary entry content, integrate what would be entry content as additional fields inside the action instead of creating a separate entry which would add unnecessary gossip on the DHT. These types are identified and described in Appendix A, Implementation.

#### Countersigning

<span id="page-18-0"></span>So far we have discussed individual agents taking Actions and recording them on their Source Chains. It is also desireable for subsets of agents to mutually consent to a single Action by atomically recording the Action to their chains. We achieve this through a process of Countersigning, whereby a session is initiated during which the subset of agents builds an Action that all participating agents sign, and during which all agents promise one another that they will not take some other action in the meantime.

There are two ways of managing the countersigning process:

- 1. Assigned completion: where one preselected agent (whom we call the Enzyme) acts as a coordinator for ensuring completion of a signing session.
- Randomized completion: where any agent in the neighborhood of the Entry address (which is cryptographically pseudorandom and is computed on data contributed by each counterparty) can report completion.

Additionally there are two contexts for making these atomic changes across multiple chains:

- 1. When the change is about parties who are accountable to the change, i.e., their role is structurally part of the state change, as in spender/receiver of a mutual credit transaction
- 2. When the change simply requires witnessing by M of N parties, i.e., all that's needed is a "majority" of a group to agree on the atomicity. This allows a kind of "micro-consensus" to be implemented in parts of

an application. It's an affordance for applications to implement a set of "super-nodes" that manage a small bit of consensus. Note that in our current implementation, M of N countersigning always uses an Enzyme to manage the session completion.

*Countersigning Constraints*

- 1. All actions must be signed together; one action is not enough to validate an atomic state change across multiple chains.
  - All parties must be able to confirm the validity of each others's participation in that state change (meaning each chain is in a valid state to participate in the role/capacity which they are engaging – e.g., a spender has the credits they're spending at that point in their chain).
- 2. The moment the enzyme or random session completer agent holds and broadcasts all the signed and valid actions, then everyone is committed.
- 3. It should not be possible for a participant to withhold and/or corrupt data and damage/fork/freeze another participant's source chain.
- 4. It should not require many network fetches to calculate state changes based on countersignatures (i.e., it should be possible to get a unified logical unit – that is, multiple actions on a single entry hash address on the DHT).
- 5. Participants can NOT move their chain forward without a provable completion of the process, and there IS a completion of the process in a reasonable time frame
  - The countersigning process should work as closely as possible to the standard single-agent "agent-centric network rejection of unwanted realities": anyone who moves forward before the process has timed out or completed, or anyone who tries to submit completion outside of timeouts, will be detected as a bad fork.

*Countersigning Flow* Here is a high-level summary of how a countersigning session flows:

- 0. Alice sends a **preflight request** to Bob, Carol, etc, via a remote call.
  - The preflight request includes all information required to negotiate the session with the entry itself, for example:
    - **–** Entry hash: What data are we agreeing to countersign? (The contents of the entry are often negotiated beforehand and communicated to all parties separately, although the app data field described below can also be used for this purpose.)
    - **–** Action base: What type is the entry we'll be countersigning, and will it be a Create or an Update?
    - **–** Update/delete references: what are we agreeing to modify?
    - **–** Session times: Will I be able to accept the session start time, or will it cause my

- chain to be invalid? Am I willing to freeze my chain for this long?
- **–** The agents and roles: Are these the parties I expected to be signing with?
- **–** App data: can point to necessary dependencies or, if the contents of the entry to be countersigned are small, the entry itself.
- 1. If the other parties accept, they freeze their chains and each return a **preflight response** to Alice. It contains:
  - The original request.
  - The state of the party's source chain "as at" the time they froze it.
  - Their signature on the above two fields.
- 2. Alice builds a session data package that contains the preflight request along with the source chain states and signatures of all consenting parties, and sends it to them.
- 3. Each party builds and commits an action that writes the countersigned entry (including the contents of the session data package and the entry data itself) to their source chains. At this point, unsigned actions are created for themselves and every other party and full record validation is run against each action, as though they were authoring as that agent.
- 4. After everything validates, each agent signs and sends their action to the session completer – either the enzyme (if one was elected) or the entry's DHT neighborhood.
- 5. The session completer reveals all the signed actions as a complete set, sending it back to all parties.
- 6. Each signer can check for themselves that the set is valid simply by comparing against the session entry and preflight info. They do not have to rerun validation; they only need to check signatures, integrity, and completeness of the action set data.
- 7. All counterparties now proceed to write the completed action to their source chain and publish its data to the DHT.
- 8. The DHT authorities validate and store the action and entry data as normal.

#### Graph DHT: Formal State Model

Holochain performs a topological transform on the set of the various agents' source chains into a contentaddressable graph database (graph DHT or GDHT) sharded across many nodes who each function as authoritative sources for retrieving certain data.

**Fundamental Write Constraint:** The DHT can never be "written" to directly. All data enters the DHT **only** by having been committed to an agent's source chain and then being **transformed** from validated local chain state into the elements (DHT operations) required for GDHT representation and lookup.

**Structure of GDHT data:** The DHT is a contentaddressable space where each piece of content is found at the address which is the hash of its content. In addition, any address in the DHT can have metadata attached to it. This metadata is not part of the content being hashed.

*Note about hashing: Holochain uses 256-bit Blake2b hashes with the exception of one entry type, AgentPub-Key, which is a 256-bit Ed25519 public key and its hash function is simply the identity function. In other words, the content of the AgentPubKey is identical to its hash. This preserves content-addressability but also enables agent keys to function as self-proving identifiers for network transport and cryptographic functions like signing or encryption.*

**DHT Addresses:** Both Actions and Entries from source chains can be retrieved from the DHT by either the ActionHash or EntryHash. The DHT get() function call returns a Record, a tuple containing the most relevant action/entry pair. Structurally, Actions "contain" their referenced entries so that pairing is obvious when a Record is retrieved by ActionHash. However, Actions are also attached as metadata at an EntryHash, and there could be many Actions which have created the same Entry content. A get() function called by EntryHash returns the oldest undeleted Action in the pair, while a get\_details() function call on an EntryHash returns all of the Actions.

**Agent Addresses & Agent Activity:** Technically an AgentPubKey functions as both a content address (which is never really used because performing a get() on the key just returns the key itself) and a network address to send communications to that agents. But in addition to the content of the key stored on the DHT is metadata about that agent's chain activity. In other words, a get\_agent\_activity() request retrieves metadata about their chain records and chain status.

Formally, the entire GDHT is represented as a set of 'basis hashes' *bc<sup>x</sup>* , or addresses where both content *c* and metadata *m* may be stored:

$$GDHT = \{d_1, \dots, d_n\}$$

The data at a basis hash can consist of content and/or metadata:

$$d_{b_{c_x}} = (c_x, M)$$

A basis hash is the hash of the content stored at the address:

$$b_{c_x} = hash(c_x)$$

The total set of content represented by the GDHT consists of entries *E*, actions *A*, and external content *T* (where the addresses can still store metadata and be used as references, but the content is not stored in the DHT):

$$E = \{e_1, \dots, e_n\}$$

$$A = \{a_1, \dots, a_n\}$$

$$T = \{t_1, \dots, t_n\}$$

$$C = E \bigsqcup A \bigsqcup T$$

An address can hold a set of metadata:

$$M = \{m_1, \dots, m_n\}$$
$$m_x = \text{metadata}$$

There may be arbitrary types of metadata. For instance, every instance of entry content *e* has a set of creation actions *A<sup>e</sup>* associated with it:

$$\forall e \, M_{context} = \{a_{e1}, \dots, a_{en}\}$$

And any address may have a set of links pointing to other addresses, each of which is a tuple of its type, an arbitrary tag, and a reference to the target address *bc<sup>T</sup>* :

$$M_{link} = \{link_1, \dots, link_n\}$$
$$\exists c_T \ link = (type, tag, b_{c_T})$$

For links, we refer to an address with link metadata as a **Base** and the address that the link points to as a **Target**. The link can also be typed and have an optional *tag* containing arbitrary content.

**Topological Transform Operations:** A source chain is a hash chain of actions with entries, but these are transformed into DHT operations which ask DHT nodes to perform certain validation and storage tasks on the content and metadata at the address, because we are transforming or projecting from authorship history to a distributed graph. Chain entries and actions are straightforwardly stored in the graph as nodes, as *C* at their hash in the DHT, but more sophisticated operations are also performed on existing DHT entries. For example, when updating/deleting entries, or adding/removing links, additional metadata is registered in parts of the DHT to properly weave a graph.

#### Graph Transformation

<span id="page-20-0"></span>While source chain entries and actions contain all the information needed to construct a graphing DHT, the data must be restructured from a linear local chain under single authority and location, to a graph across many nodes (where a node is an address or hash, optionally with content) with many authorities taking responsibility for redundantly storing content and metadata for the entire range of nodes. In this section we focus only on

the transformation from source chain to DHT. The [next](#page-22-0) [section](#page-22-0) will focus on the election of authoritative sources for data.

The linking/graphing aspects must be constructed from the state changes committed to source chains.

The process from an agent's action to changed DHT state is as follows:

- 1. An action produces a **source chain record** detailing the nature of the action, including the context in which it was taken (author and current source chain state).
- 2. The source chain record is transformed to **DHT operations**, each of which has a **basis hash** that it applies to.
- 3. The author sends these DHT operations to the respective neighborhoods of their basis hashes, where peers who have assumed authority for the basis hashes **integrate** them into an updated state for the data at those basis hashes.

The following table shows how each action (which gets stored on the author's source chain as a record) is transformed into multiple DHT operations. Remember an operation corresponds with a way that the DHT state needs to be manipulated.

For viable eventual consistency in a gossipped DHT, all actions must be idempotent (where a second application of an operation will not result in a changed state) and additive/monotonic:

- The deletion of an entry creation action and its corresponding entry doesn't actually delete the entry; it *marks* the action as deleted. At the entry basis hash, the delete action becomes part of a CRDTstyle "tombstone set", and a set difference is taken between the entry creation actions *A<sup>c</sup>* and entry deletion actions *A<sup>d</sup>* that reference at the entry's basis hash to determine which creation actions are still 'live' (*Ac<sup>l</sup>* = *A<sup>c</sup>* − *Ad*). Eventually the entry itself is considered deleted when *A<sup>c</sup>* − *A<sup>d</sup>* = ∅.
- The removal of a link adds the removal action to a tombstone set at the link's base address in a similar fashion, subtracting the link removal actions from the link creation actions they reference to determine the set of live links.
- Updating an entry creation action and its corresponding entry doesn't change the content in place; it adds a link to the original action and entry pointing to their replacements. One entry creation action may validly have many updates, which may or may not be seen by the application's logic as a conflict in need of resolution.

The transformation of an action is followed by sending the operation to specific DHT basis hashes, instructing the agents claiming authority for a range of address space covering those basis hashes, to validate and store (integrate) the operations into their respective portions of the

DHT store. Because the DHT is a **graph** database, what is added is either a node or an edge. A node is a basis hash in the DHT, while an edge is part of the addressable content or metadata stored at a node.

Here is a legend of labels and symbols used in the diagrams:

- The large, gray, rounded rectangle on the left of each row represents the agent *k* currently making an action, and encompasses the data they produce.
- A label styled as do\_x() is the function representing the action being taken by the agent *k*. It yields a record of the action, which is saved to the source chain.
- *a<sup>n</sup>* is the action that records the action. It is represented by a square.
- *an*−<sup>1</sup> is the action immediately preceding the action currently being recorded.
- *E* is action-specific data which is contained in a separate *entry* which has its own home in the DHT. It is represented by a circle.
- *e* : {*. . .* } is action-specific data which performs an operation on prior content. Such data exists wholly within the action of the record of the action.
- Overlapping shapes (primarily square actions and circular entries) represent data that travels together and can be seen as a single unit for the purpose of defining what exists at a given basis hash. In the case of an entry basis hash, where multiple actions authoring the same entry may exist, each entry/action pair can be seen as its own unit, or alternatively the content at that address can be seen as a superposition of multiple entry/action pairs.
- *k* is the public key of the agent taking an action.
- → is a graph edge pointing to the hash of other content on the DHT.
- *C<sup>B</sup>* and *C<sup>T</sup>* are a link base and target, the basis hashes of previously existing content. Any addressable content can be the base and target of a link. These are represented by blobs.
- Blue arrows are graph edges.
- *a<sup>p</sup>* and *E<sup>p</sup>* are the previously existing content which a graph edge → references, when the reference may *only* pertain to a action or an entry, respectively.
- A label styled as RegisterX is a DHT operation that adds metadata to a basis hash. A label styled as StoreX is a DHT transform that adds addressable content to a DHT basis hash. The payload of an operation is contained in a gray triangle.
- Basis hashes are represented as *b<sup>x</sup>* in black circles, in which the subscript *x* represents the kind of addressable content stored at that basis hash. For instance, *b<sup>k</sup>* is the basis hash of the author *k*'s agent ID entry; that is, their public key.
- A stack of rounded rectangles represents the neighborhood of the basis hash being manipulated, in which multiple peers may be assuming authority for the same hash.

- Gray arrows represent the transformation or movement of data.
- Data attached to a basis hash by a line is metadata, while data overlapping a basis hash is primary content.
- A green slash indicates existing data that has been replaced by an update. A green arrow leads from the update action to the data it replaces.
- A red X indicates existing data that has been *tombstoned*; that is. it is marked as dead. A red arrow leads from the delete action to the data it tombstones.

<span id="page-22-0"></span>*Authority Election* In the case of source chain entries (and actions), it is fairly obvious that the author who created them is the **author**itative source. But part of translating from a series of local chain states to a resilient global data store involves identifying which nodes in the network become the responsible authorities for holding which DHT content.

Most existing DHT frameworks simply have nodes volunteer to hold specific content, and then use the DHT as a tracking layer to map content hashes to the nodes holding the content. But this allows content to disappear arbitrarily and also creates imbalanced dynamics between people who consume content and people who serve it (leechers & seeders). Since Holochain is designed to function more like a distributed database than a content distribution network, it needs to ensure resilience and permanence of data elements, as well as load balancing and reasonable performance, on a network where nodes are likely coming online and going offline frequently.

As such, Holochain doesn't rely on nodes to volunteer to hold specific entries, but rather to volunteer aggregate capacity (e.g., holding 100MB of data rather than arbitrarily chosen entries). Authoring nodes are responsible for publishing entries from their local DHT instance to other nodes on the network (**authorities**) who will become responsible for serving that data.

Like most DHT architectures, Holochain uses a "nearness" algorithm to compute the "distance" between the key of a piece of data and the key of a peer holding the data; in our case, between the 256-bit Blake2b basis hash of the data or metadata to be stored and the 256-bit Ed25519 public key (network address) of nodes. Basically, it is the responsibility of the nodes *nearest* a basis hash to store data and metadata for it, within an "arc" of authority of their choosing.

Holochain's validating, graphing, gossiping DHT implementation is called **rrDHT**.

rrDHT is designed with a few performance requirements/characteristics in mind.

- 1. It must have a compact and computationally simple representational model for identifying which nodes are responsible for which content, and which nodes actually hold which content. (A **"world model"** of what is where.)
- 2. It must have **lookup speeds** at least as fast as Kademlia's binary trees ( O(*n* log *n*) ). Current testing shows an average of 3 hops/queries to reach an authority with the data.
- 3. It must be **adjustable** to be both resilient and performant across many DHT compositional make-ups (reliability of nodes, different network topologies, high/low usage volumes, etc.)

**World Model:** The network location space is a circle comprising the range of unsigned 32-bit numbers, in which the location 0 is adjacent to the location 2 <sup>32</sup> − 1. It can

![](_page_23_Figure_1.jpeg)

FIG. 1. Operations and state changes produced by create action

![](_page_23_Figure_4.jpeg)

FIG. 2. Operations and state changes produced by update action

![](_page_24_Figure_1.jpeg)

FIG. 3. Operations and state changes produced by delete action

![](_page_24_Figure_3.jpeg)

FIG. 4. Operations and state changes produced by create\_link action

be more precisely defined as:

*L* : Z mod 2<sup>32</sup>

Defining this in terms of modulo arithmetic has an important consequence for routing a publish or query request to the correct agent, which we will explain later.

The larger 256-bit address space of the DHT, consisting of 256-bit "basis hashes" *B* (Blake2b-256 hashes of addressable content *C*, which as previously defined includes Ed25519 public keys of agents *K*), is mapped to the smaller network location space via a function:

map\_to\_loc : *B* → *L*

![](_page_25_Figure_1.jpeg)

FIG. 5. Operations and state changes produced by delete\_link action

which is the XOR of 8 × 32-bit segments of the hashes. At the storage level, the original address is still used for addressing content and metadata, so collisions in the smaller space are not a concern.

Using the sets *B* and *L* to denote all basis addresses and network locations in the DHT, respectively:

$$|L| = 2^{32}$$
  
 $|B| = 2^{256}$   
 $\therefore |B| = |L| \cdot 2^{256-32}$ 

Each agent has a network location *l<sup>k</sup>* in this 32-bit space as well as an arc size *sarc* indicating how large an arc of the location circle they are claiming authority for. The storage arc *ARCl<sup>k</sup>* defines the range of basis hashes for which a node claims authority. The arc spreads clockwise from *lk*.

$$ARC_{l_k}:\{l_k,\ldots,l_k+s_{arc}\}$$

As a consequence of modulo arithmetic, agents close to 2 32 may end up claiming authority for data at and beyond 0; for example, if the network location for an agent's public key *k* is 2 <sup>32</sup> − 2 and their arc of authority is 20, the arc extends to network location 18:

$$(2^{32} - 2 + 20) \mod 2^{32} = 18$$

A node can rapidly resolve any basis hash *b* to the most likely candidate for an authority *pbest* by comparing the basis hash's network location *l<sup>b</sup>* to all the peers they know about (the set *L<sup>P</sup>* , or their "peer table") using the following algorithm (expressed in pseudocode):

p\_best = L\_P .sort\_ascending\_by(l\_p -> (l\_b - l\_p) mod 2^32) .first()

It is then determined whether the peer is indeed an authority for *lb*, either by relying on locally cached knowledge of their arc or asking them directly. At this point, if the peer is determined to not claim authority, the next less likely candidate may be chosen, on the hope that their arc is larger, or the most likely candidate is asked if they know of a *more* likely candidate. They are in an advantageous place to do so, as agents' peer tables are naturally biased toward peers that are near to them in the network location space.

*Network Location Quantization* Additionally, arcs are subjected to **quantization** which splits the network location space *L* into disjoint subsets of a given size *sq*, and to which the starting arc boundary *k* and arc size *sarc* are also snapped. The quantized arc is then fully represented by three numbers: the quantized chunk size *sq*, the number of chunks until the start boundary *kq*, and the number of chunks from start to end *nq*.

Peers also quantize the time dimension such that the size of chunks of time increase quadratically as the dimension extends into the past.

The spaces of network locations and time form two dimensions of a coordinate space, and each operation can be mapped to a point in this space using the network location of its basis hash as the *x* coordinate and its authoring time as the *y* coordinate.

When the coordinate space is quantized, it forms a grid. Each agent holds a finite region of this grid, bounded by their quantized arc, and the total set of held operations within each grid cell is fingerprinted using a lossy algorithm (such as the XOR of the hashes of all the operations whose coordinates fall within the cell).

When two peers attempt to synchronize the held sets of operations for the intersection of their two address spaces  $ARC_{l_{k_a}} \cap ARC_{l_{k_b}}$ , they can then simply compare their respective fingerprints of each cell within that intersection. If the fingerprints do not match, they exchange and compare the entire list of operation hashes they each hold. This allows peers to more quickly compare and synchronize regions of shared authority, and the quadratic nature of quantum sizes in the time dimension allows them to prioritize syncing of newer, more rapidly changing data, by comparing more fingerprints from smaller time regions for newer data, and fewer fingerprints over larger time regions for older data.

DHT Communication Protocols So far we have described the topological transformation between the agentic holding of state on a source chain into the shape of the shared data for making that state visible via the DHT. Additionally we have described an addressing scheme that makes data deterministically retrievable. Now we must describe the communication protocols that allow agents to come and go on the network while still maintaining the necessary data redundancy.

Peers conduct all communication with each other using **messages** of various classes and types. There are two levels of abstraction for messages; the lower level establishes peer connections in discrete **network spaces** and defines basic messages for maintaining DHT state and sending arbitrary application messages, while the higher level adapts these basic message types to implement Holochain-specific features.

There are two classes of messages, both of which are non-blocking; that is, they are sent asynchronously and don't monopolize the peer connection while waiting for a response:

- Notify messages are "fire-and-forget"; that is, they don't anticipate a response from the receiver.
- Request messages are wrapped in an 'envelope' that has a sequence ID, and anticipate a corresponding **response** message with the same sequence ID from the receiver.

Basic Message Types These message types exist at the lower level.

- Notify message types
  - Broadcast sends a message of one of the following types:
    - \* User contains arbitrary, application-level data. Here, the application in question is Holochain rather than a specific hApp.
    - \* **AgentInfo** advertises an agent's current storage arc and network transport addresses.
    - \* Publish advertises that one or more DHT operations are available for retrieval. An arbitrary context value indicates the publishing context, which in practice is a bit

field that indicates whether it's being published as part of a countersigning session and whether a validation receipt is needed.

- DelegateBroadcast sends a broadcast, but rather than expecting the receiver to do something with it, it expects them to broadcast it in turn to the peers in their DHT neighborhood.
- FetchOp requests the data for one or more DHT operations, usually as a follow-up from receiving a Publish broadcast message or MissingOpHashes gossip message advertising that such operations are available. While it is strictly a notify-class message, it functions similarly to a request-class message in that it anticipates a response in the form of a PushOpData message.
- PeerUnsolicited is similar to Peer-QueryResp below, but is initiated by a node without being prompted.
- PushOpData sends the data for one or more DHT operations as a response to a FetchOp message. Each op optionally includes the quantized region it belongs to if it's being pushed as part of a historical sync.
- Gossip is a container for messages implementing various gossip strategies among nodes who share authority for portions of the DHT's network location space.
- Request message types
  - Call and CallResp allow a peer to make an arbitrary, application-level function call to another peer and receive data in response. As with broadcast, the application in question is Holochain.
  - PeerGet and PeerGetResp allow a peer to ask another peer if they know about a specific agent. The response contains the same data as an AgentInfo message.
  - PeerQuery and PeerQueryResp allow a
    peer to ask another peer if they know of any
    agents who are currently claiming authority for
    a given 32-bit network location. The response
    contains zero or more AgentInfos.

DHT data is synchronized between peers two stages:

- 1. A node sends a peer the hashes of the DHT operations they have available. This can happen via publish, where the initiator is creating new operations, or via gossip, where the initiator and remote peer engage in one or more rounds of comparing the operations they respectively hold for a shared arc of the network location space.
- 2. The remote peer 'fetches' the data for the operations they need but do not have.

Holochain-Specific Message Types The following Holochain-specific message types are implemented using the preceding basic message types. Unless otherwise

noted, the following messages follow a call-and-response pattern using **Call** and **CallResp**.

- An agent uses **CallRemote** to attempt a remote procedure call (RPC) to a zome function in another peer's cell.
- When an authority has finished validating DHT operations as a consequence of receiving a publish message, they send a **ValidationReceipts** message to the publisher. This tells the publisher that the authority has received the data, deemed it to be valid, and is now holding it for serving to other peers. This message uses the **User** broadcast message type.
- **Get** requests the addressable content stored at the given basis hash.
- **GetMeta** requests all metadata stored at the given basis hash.
- **GetLinks** requests only link metadata of a certain type at the given basis hash, optionally with a filter predicate.
- **CountLinks** is similar to GetLinks, but only requests the count of all links matching the type and filter predicate.
- **GetAgentActivity** requests all or a portion of the 'agent activity' metadata for the given agent ID, which includes source chain actions, chain status (whether it has been forked), and any outstanding warrants collected for that agent (see the [following](#page-28-0) [section](#page-28-0) for a description of warrants).
- **MustGetAgentActivity** requests only the portion of the agent activity metadata that can be guaranteed to be unchanging (if it exists) regardless of the current state at the agent's basis hash — that is, a contiguous sequence of source chain actions, notwithstanding any contiguous sequence that may exist in a fork of that agent's chain.
- There are three message types used in negotiating a countersigning session, all of which use the **User** broadcast message:
  - **–** Counterparties use **CountersigningSession-Negotiation**, with a subtype of **Enzyme-Push**, to send their signed **Create** or **Update** action to the designated facilitator of the session (the Enzyme) when such an agent has been elected.
  - **–** When an Enzyme has not been elected, counterparties instead use **PublishCountersign** to send their action to the neighborhood of the basis hash of the **StoreEntry** DHT operation that they will eventually produce if countersigning succeeds.
  - **–** When authorities have received a PublishCountersign message from all expected counterparties, they then send the complete list of signed actions to all parties using **CountersigningSessionNegotiation** with a subtype of **AuthorityResponse**.

**Fast Push vs. Slow Heal** It is important to underscore the dual way in which data is propagated around the DHT, and the rationale for designing Holochain in such a way.

When data is initially created with the intention of persisting it in the DHT, it is sent to the neighborhoods of the appropriate authorities using a **fast push** strategy. This is the **Publish** broadcast message described above, in which the creator of the data takes responsibility for making sure it reaches a sufficient number of authorities to ensure resilience and availability of the data. The creator then attempts to re-send the Publish message to more authorities until they have received a satisfactory number of **ValidationReceipts** in response. (In practice, the publisher uses a combination of **Broadcast** and **DelegateBroadcast**, the latter message type reducing the burden on the publisher, who is unlikely to know of as many peers in the DHT operation's neighborhood as the authorities do, and who may intend to go offline before they have received a satisfactory number of validation receipts.)

After data has been created and has 'saturated' the neighborhood of the data's basis hashes, however, ongoing maintenance is required to keep the data alive as authorities leave and join the network. This is done using a **slow heal** strategy, in which authorities in the same neighborhood regularly initiate **gossip rounds**[21](#page-27-0) to check each other's stores for new data.

Additionally, gossip is split into **recent** and **historical** gossip, wherein peers attempt to sync data that is younger than a certain threshold (for instance, five minutes) using a diffing strategy (a Bloom filter) that results in fewer unnecessary deltas being transferred, while data that is older than this threshold can afford to use a strategy with more noisy diffs (time/space quantization).

This multi-tiered strategy is chosen for Holochain because of the observation that, in a typical application, the set of data created recently changes more often than the set of data created further in the past. In fact, as long as peers are synchronizing frequently, the latter set should only change when a partial or full network partition is resolved.

A secondary concern is that, for many applications such as social media, digital currencies, or telemetry, historical data is less relevant and accessed less frequency than recent data. Any discrepancy between two peers' views of the total data set can often in practice be tolerated.

Hence, this approach favors freshness of recent data so that it becomes available to all peers in a timely fashion

<span id="page-27-0"></span><sup>21</sup> While we use the term 'gossip' exclusively for the slow-heal strategy, both fast-push and slow-heal can be considered a gossip protocol (see [https://en.wikipedia.org/wiki/Gossip\\_protocol\)](https://en.wikipedia.org/wiki/Gossip_protocol), as in both strategies a piece of data is initially communicated to a small number of peers who then communicate it to a larger number of their peers.

expected of modern networked applications, while resolution of discrepancies in historical data is treated as a maintenance concern.

#### Security & Safety

Many factors contribute to a system's ability to live up to the varying safety and security requirements of its users. In general, the approach taken in Holochain is to provide affordances that take into account the many types of realworld costs that result from adding security and safety to systems such that application developers can match the trade-offs of those costs to their application context. The integrity guarantees listed in prior sections detail the fundamental data safety that Holochain applications provide. Two other important facets of system security and safety come from:

- 1. Gating access to functions that change state, for which Holochain provides a unified and flexible Object Capabilities model.
- 2. Detecting and blocking participation of bad actors, for which Holochain provides the affordances of validation, warranting, and blocking.
