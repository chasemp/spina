---
images:
- _page_58_Picture_1.jpeg
- _page_58_Figure_3.jpeg
- _page_59_Figure_9.jpeg
order: 15
title: Preamble
---

- *BasisHash* is the address to which an operation is being applied.
- *OperationT ype* is the type of operation a node is responsible for performing.
- *P ayload* is the self-proving structure which contains the data needed to perform the operation. In all cases this includes the Action; it may also include the Entry if such a thing exists for the action type and if it is required to validate and perform the operation.

The technical implementation below of the human-friendly grammar above compresses and drops unnecessary items where possible. There are a couple of *OperationT ype* where we can drop the entry (but never the action); in these cases we can reduce all the data down to Action + an *OperationT ype* enum struct which usually contains the entry.

The basis hash (or hash neighborhood we're sending the operation to) can be derived from the payload using the dht\_basis function outlined below.

```
enum DhtOp {
    ChainOp(ChainOp),
    WarrantOp(WarrantOp),
}
impl DhtOp {
    fn dht_basis(self) -> AnyLinkableHash {
    match self {
        Self::ChainOp(op) => op.dht_basis(),
        Self::WarrantOp(op) => op.dht_basis(),
    }
```

```
}
}
// Ops that start with `Store` store new addressable content at the basis hash.
// Ops starting with `Register` attach metadata to the basis hash.
enum ChainOp {
    StoreRecord(Signature, Record, RecordEntry),
    StoreEntry(Signature, NewEntryAction, Entry),
    RegisterAgentActivity(Signature, Action),
    RegisterUpdatedContent(Signature, action::Update, RecordEntry),
    RegisterUpdatedRecord(Signature, action::Update, RecordEntry),
    RegisterDeletedBy(Signature, action::Delete),
    RegisterDeletedEntryAction(Signature, action::Delete),
    RegisterAddLink(Signature, action::CreateLink),
    RegisterRemoveLink(Signature, action::DeleteLink),
}
impl ChainOp {
    fn dht_basis(self) -> AnyLinkableHash {
        match self {
            StoreRecord(_, action, _) => hash(action),
            StoreEntry(_, action, _) => hash(action.entry),
            RegisterAgentActivity(_, action) => header.author(),
            RegisterUpdatedContent(_, action, _) => action.original_entry_address,
            RegisterUpdatedRecord(_, action, _) => action.original_action_address,
            RegisterDeletedBy(_, action) => action.deletes_address,
            RegisterDeletedEntryAction(_, action) => action.deletes_entry_address,
            RegisterAddLink(_, action) => action.base_address,
            RegisterRemoveLink(_, action) => action.base_address,
        }
    }
}
struct WarrantOp(Signed<Warrant>);
struct Warrant {
    proof: WarrantProof,
    // The author of the warrant.
    author: AgentHash,
    timestamp: Timestamp,
}
enum WarrantProof {
    ChainIntegrity(ChainIntegrityWarrant),
}
impl WarrantProof {
    fn dht_basis(self) -> AnyLinkableHash {
        self.action_author()
    }
    fn action_author(self) -> AgentPubKey {
        match self {
            Self::ChainIntegrity(w) => match w {
                ChainIntegrityWarrant::InvalidChainOp { action_author, .. } => action_author,
                ChainIntegrityWarrant::ChainFork { chain_author, .. } => chain_author,
            },
        }
```

```
}
}
enum ChainIntegrityWarrant {
    InvalidChainOp {
        action_author: AgentHash,
        action: (ActionHash, Signature),
        validation_type: ValidationType,
    },
    ChainFork {
        chain_author: AgentHash,
        action_pair: ((ActionHash, Signature), (ActionHash, Signature)),
    },
}
```

*Uniquely Hashing Dht Operations* When items are gossiped/published to us, we SHOULD be able to quickly check:

- 1. Do we consider ourselves an authority for this basis hash?
- 2. Have we integrated it yet?

and quickly take appropriate action.

To facilitate this, implementations MUST define a reproducible way of hashing DHT operations. The following code outlines the minimal necessary contents to create the correct operation hash. The basic procedure for all operations is:

- 1. Drop all data from the operation except the action.
- 2. Wrap the action in a variant of a simplified enum representing the minimal data needed to uniquely identify the operation, thus allowing it to be distinguished from other operations derived from the same action.
- 3. Serialize and hash the simplified value.

```
// Parallels each variant in the `ChainOp` enum, only retaining the minimal data
// needed to produce a unique operation hash.
enum ChainOpUniqueForm {
    StoreRecord(Action),
    StoreEntry(NewEntryAction),
    RegisterAgentActivity(Action),
    RegisterUpdatedContent(action::Update),
    RegisterUpdatedRecord(action::Update),
    RegisterDeletedBy(action::Delete),
    RegisterDeletedEntryAction(action::Delete),
    RegisterAddLink(action::CreateLink),
    RegisterRemoveLink(action::DeleteLink),
}
// Conversion implementation for all the types involved in a `DhtOp`.
impl ChainOp {
    fn as_unique_form(self) -> ChainOpUniqueForm {
        match self {
        Self::StoreRecord(_, action, _) => ChainOpUniqueForm::StoreRecord(action),
        Self::StoreEntry(_, action, _) => ChainOpUniqueForm::StoreEntry(action),
        Self::RegisterAgentActivity(_, action) => {
            ChainOpUniqueForm::RegisterAgentActivity(action)
        }
        Self::RegisterUpdatedContent(_, action, _) => {
            ChainOpUniqueForm::RegisterUpdatedContent(action)
        }
        Self::RegisterUpdatedRecord(_, action, _) => {
            ChainOpUniqueForm::RegisterUpdatedRecord(action)
        }
        Self::RegisterDeletedBy(_, action) => ChainOpUniqueForm::RegisterDeletedBy(action),
        Self::RegisterDeletedEntryAction(_, action) => {
```

```
ChainOpUniqueForm::RegisterDeletedEntryAction(action)
        }
        Self::RegisterAddLink(_, action) => ChainOpUniqueForm::RegisterAddLink(action),
        Self::RegisterRemoveLink(_, action) => ChainOpUniqueForm::RegisterRemoveLink(action),
        }
    }
}
trait HashableContent {
    type HashType: HashType;
    fn hash_type(self) -> Self::HashType;
    fn hashable_content(self) -> HashableContentBytes;
}
impl HashableContent for DhtOp {
    type HashType = hash_type::DhtOp;
    fn hash_type(self) -> Self::HashType {
        hash_type::DhtOp
    }
    fn hashable_content(self) -> HashableContentBytes {
        match self {
            DhtOp::ChainOp(op) => op.hashable_content(),
            DhtOp::WarrantOp(op) => op.hashable_content(),
        }
    }
}
impl HashableContent for ChainOp {
    type HashType = hash_type::DhtOp;
    fn hash_type(self) -> Self::HashType {
        hash_type::DhtOp
    }
    fn hashable_content(self) -> HashableContentBytes {
        HashableContentBytes::Content(
            self.as_unique_form().try_into()
        )
    }
}
impl HashableContent for WarrantOp {
    type HashType = hash_type::DhtOp;
    fn hash_type(&self) -> Self::HashType {
        hash_type::DhtOp
    }
    fn hashable_content(&self) -> HashableContentBytes {
        self.warrant().hashable_content()
    }
}
impl HashableContent for Warrant {
```

```
type HashType = holo_hash::hash_type::Warrant;
    fn hash_type(&self) -> Self::HashType {
        Self::HashType::new()
    }
    fn hashable_content(&self) -> HashableContentBytes {
        HashableContentBytes::Content(self.try_into())
    }
}
```

### Changing States of DHT Content

As a simple accumulation of data (DHT operations) attached to their respective basis addresses, a Holochain DHT exhibits a logical monotonicity[30](#page-57-0). The natural consequence of this property is that any two peers who receive the same set of DHT operations will arrive at the same database state without need of a coordination protocol.

While the monotonic accumulation of operations is the most fundamental truth about the nature of DHT data, it is nevertheless important for the goal of ensuring Holochain's fitness for application development that we give the operations further meaning. This happens at two levels:

- **Data and metadata**: The immediate result of applying an operation to a basis address is that data or metadata is now available for querying at that basis address. This takes the form of:
  - **–** A record as primary data,
  - **–** An entry and its set of creation actions as primary data, presented as the Cartesian product {*e*}×{*h*1*, . . . , hn*},
  - **–** Record updates and deletes as metadata,
  - **–** Link creations and deletions as metadata,
  - **–** Agent activity as a tree of metadata,
  - **–** Validation status as metadata, and
  - **–** Warrants as metadata.
- **CRUD**: The total set of metadata on a basis address can always be accessed and interpreted as the application developer sees fit (see get\_details in the DHT Data [Retrieval](#page-42-0) section of this appendix), but certain opinionated interpretations of that set are useful to provide as defaults[31](#page-57-1):
  - **–** The set difference between all record creates/updates and deletes that refer to them can be accessed as a "tombstone" set that yields the list of non-deleted records, the liveness of an entry or record, or the earliest live non-deleted record for an entry (see get in the DHT Data [Retrieval](#page-42-0) section).
  - **–** The set difference between all link creates and link deletes that refer to them can be accessed as a tombstone set that yields the list of non-deleted links (see get\_links in the DHT Data [Retrieval](#page-42-0) section).

*Validation and Liveness on the DHT* The first task before changing the DHT to include a new piece of data is to validate the operation according to both system-level and application-specific rules. Additionally, an operation MUST be accompanied by a valid provenance signature that matches the public key of its author.

DHT operations whose validation process has been abandoned are not gossiped. There are two reasons to abandon validation. Both have to do with consuming too much resources.

- 1. It has stayed in our validation queue too long without being able to resolve dependencies.
- 2. The app validation code used more resources (CPU, memory, bandwidth) than we allocate for validation. This lets us address the halting problem of validation with infinite loops.

be validly seen as operations in a simple operation-based conflictfree replicated data type (CRDT) (see [https://crdt.tech\)](https://crdt.tech), we have chosen not to use this term in order to avoid overlaying of preconceptions formed by more capable CRDTs.

<span id="page-57-0"></span><sup>30</sup> *Keeping CALM: When Distributed Consistency is Easy*, Joseph M Hellerstein and Peter Alvaro [https://arxiv.org/abs/1901.01930.](https://arxiv.org/abs/1901.01930)

<span id="page-57-1"></span><sup>31</sup> While this interpretation indicates that the set of metadata can

![](_page_58_Picture_1.jpeg)

*Entry Liveness Status* The 'liveness' status of an Entry at its DHT basis is changed in the following ways:

![](_page_58_Figure_3.jpeg)

An Entry is considered Dead when ALL of the valid creation Actions which created it have been marked as deleted by valid deletion Actions; that is, Live entails a non-empty result of a set difference between the creation Action hashes and the deletes\_address field of the deletion Action hashes stored at the entry's basis.

Withdrawn and Purged are placeholders for possible future features:

- Withdrawn: The record has been marked by its author as such, usually to correct an error (such as accidental forking of their chain after an incomplete restoration from a backup). The same set difference rules apply to Live/Withdrawn as to Live/Dead.
- Purged: The addressable content has been erased from the CAS database, possibly by collective agreement to drop it – e.g., for things that may be illegal or unacceptable to hold (e.g., child pornography).

The process of changing data to these two states is unimplemented.

*Action Liveness Status* An Action is considered Dead only after a RegisterDeletedBy operation which references the Action's has has been integrated at the Action's basis.

*Link Liveness Status* A link is considered Dead only after at least one RegisterDeleteLink operation which references the CreateLink action has been integrated at the link base's basis.

*Agent Status* An Agent's status, which can be retrieved from the Agent ID basis (that is, the Agent's public key), is a composite of:

- Liveness of AgentID Entry, according to the above rules defined in Entry Liveness Status
- Validity of every Source Chain action (that is, whether all RegisterAgentActivity operations are valid)
- Linearity of Source Chain (that is, whether there are any branches in the Source chain, also determined during integration of RegisterAgentActivity operations)
- Presence of valid Warrants received from other authorities via WarrantOp DHT operations

![](_page_59_Figure_9.jpeg)

P2P Networking

A robust networking implementation for Holochain involves three layers:

- 1. The Holochain P2P networking layer, which is designed around the peer-to-peer communication needs of agents in a DNA and the building of the DNA's graph DHT,
- 2. An underlying P2P layer that handles the fact that a Holochain node will be managing communication on behalf of potentially multiple agents in multiple networks, and will be connecting with other nodes, any of which may be running non-overlapping sets of DNAs, and
- 3. A transport-level layer that supplies and interprets transport.

Thus, from a networking perspective, there is the view of a single DNA (which is its own network), in which more than one local agent may be participating, but there is also the view of an agent belonging to many DNAs at the same time.

Because the same DHT patterns that work at the level of a Holochain DNA sharing storage of application data also work to solve the problem of a shared database holding updates to a routing table of peer addresses, we have implemented a generalized P2P DHT solution and built the higher-level Holochain P2P networking needs on top of that lower level. Below we describe the high-level requirements and network messages for Holochain, followed by the lower-level requirements and network messages that carry the higher-level ones.
