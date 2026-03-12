---
images:
- _page_53_Figure_1.jpeg
order: 13
title: Ribosome/Zome Interop ABI
---

Because WebAssembly code can only interface with its host system via function calls that pass simple numeric scalars, an application binary interface (ABI) must be defined to pass rich data between the Ribosome host and the zome guest.

The host and guest expose their functionality via named functions, and the input and output data of these functions (a single argument and a return value) are passed as a tuple of a shared memory pointer and a length. This tuple is a reference to the serialized data that makes up the actual input or output data.

The caller is responsible for serializing the expected function argument and storing it in a shared memory location in the WebAssembly virtual machine instance, then passing the location and length to the callee.

The callee then accesses the data at the given location, attempts to deserialize it, and operates on the deserialized result.

The same procedure is followed for the function's return value, with the role of the caller and callee reversed.

<span id="page-30-0"></span><sup>23</sup> See [https://wasmer.io/.](https://wasmer.io/)

<span id="page-30-1"></span><sup>24</sup> See [https://rust-lang.org.](https://rust-lang.org)

<span id="page-30-3"></span><span id="page-30-2"></span><sup>25</sup> See [https://docs.rs/hdi/.](https://docs.rs/hdi/)

<sup>26</sup> See [https://docs.rs/hdk/.](https://docs.rs/hdk/)

Because errors may occur when the callee attempts to access and deserialize its argument data, the callee MUST return (or rather, serialize, store, and return the address and length of) a Rust Result<T, WasmError> value, where WasmError is a struct of this type:

```
struct WasmError {
    file: String,
    line: u32,
    error: WasmErrorInner,
}
enum WasmErrorInner {
    PointerMap,
    Deserialize(Vec<u8>),
    Serialize(SerializedBytesError),
    ErrorWhileError,
    Memory,
    Guest(String),
    Host(String),
    HostShortCircuit(Vec<u8>),
    Compile(String),
    CallError(String),
    UninitializedSerializedModuleCache,
}
```

The type Result<T, WasmError> is aliased to ExternResult<T> for convenience, and will be referred to as such in examples below.

Our implementation provides a wasm\_error! macro for the guest that simplifies the construction of an error result with the correct file and line number, along with a WasmErrorInner::Guest containing an application-defined error string.

Our implementation also provides various macros to abstract over the mechanics of this process, wrapping host functions and guest callbacks, automatically performing the work of retrieving/deserializing and serializing/storing input and output data, and presenting more ergonomic function signatures (in the case of host functions) or allowing application developers to write more ergonomic function signatures (in the case of guest functions). In particular, the #[hdk\_extern] procedural macro, when applied to a guest function, handles the conversion of the bytes stored in the memory to a map of arguments, passes those arguments, and handles the conversion of the return value to bytes stored in memory.

Hereafter, our examples of host and guest functions will assume the use of ergonomic function signatures.

#### Handling Guest Functions

For any guest function, the Ribosome MUST prepare a context which includes the list of host functions which may be called by the given type of function:

- Guest functions which are only intended to establish valid entry and link types (entry\_defs and link\_types) MUST NOT be given access to any host functions.
- Guest functions which are expected to give a repeatable result for the input arguments (validate) MUST NOT be given access to host functions whose return values vary by context.
- Guest functions which are expected to not change source chain state (validate, genesis\_self\_check, post\_ commit) MUST NOT be given access to host functions which change state.

For any guest functions which are permitted to change source chain state (init, recv\_remote\_signal, zome functions, and scheduled functions), the Ribosome MUST:

- 1. Prepare a context which includes the aforementioned host function access, as well as the current source chain state and a temporary "scratch space" into which to write new source chain state changes.
- 2. Check the state of the source chain; if it does not contain an InitZomesComplete action, run the init callback and remember any state changes in the scratch space.
- 3. If no init callbacks fail, proceed to call the guest function, remembering any state changes in the scratch space.
- 4. Transform the state changes in the scratch space into DHT operations.
- 5. Attempt to validate the DHT operations.

- 6. If all the DHT operations are valid, persist the Actions in the scratch space to the source chain.
- 7. If the called function was a zome function, return the zome function call's return value to the caller.
- 8. Spawn the post\_commit callback in the same Coordinator Zome as the called guest function and attempt to publish the DHT operations to the DHT.

State changes in a scratch space MUST be committed atomically to the source chain; that is, all of them MUST be written or fail as a batch.

#### HDI

The Holochain Deterministic Integrity (HDI) component of the Holochain architecture comprises the functions and capacities that are made available to app developers for building their Integrity Zomes.

**Integrity Zomes** provide the immutable portion of the app's code that:

- identifies the types of entries and links able to be committed in the app,
- defines the structure of data entries, and
- defines the validation code each node runs for DHT operations produced by actions to create, update, and delete the aforementioned entry types, as well as for a small number of system types.

The following data structures, functions and callbacks are necessary and sufficient to implement an HDI: *Core Holochain Data Types*

**The Action Data Type** All actions MUST contain the following data elements (with the exception of the Dna action which, because it indicates the creation of the first chain entry, does not include the action\_seq nor prev\_action data elements):

```
{
    author: AgentHash,
    timestamp: Timestamp,
    action_seq: u32,
    prev_action: ActionHash,
    ...
}
```

Additionally, the HDI MUST provide a signed wrapper data structure that allows integrity checking in validation:

```
struct Signed<T>
where T: serde::Serialize {
    signature: Signature,
    data: T,
}
// A signature is an Ed25519 public-key signature.
struct Signature([u8; 64]);
```

Implementation detail: Theoretically all actions could point via a hash to an entry that would contain the "content" of that action. But because many of the different actions entries are system-defined, and they thus have a known structure, we can reduce unnecessary data elements and gossip by embedding the entry data for system-defined entry types right in the action itself. However, for application-defined entry types, because the structure of the entry is not known at compile time for Holochain, the entry data must be in a separate data structure. Additionally there are a few system entry types (see below) that must be independently retrievable from the DHT, and thus have their own separate system-defined variant of the Entry enum type.

Many, though not all, actions comprise intentions to create, read, update, or delete (CRUD), data on the DHT. The action types and their additional data fields necessary are:

• Dna: indicates the DNA hash of the validation rules by which the data in this source chain agrees to abide.

```
struct Dna {
    ...
    hash: DNAHash,
}
```

• AgentValidationPkg: indicates the creation of an entry holding the information necessary for nodes to confirm whether an agent is allowed to participate in this DNA. This entry is contained in the action struct.

```
struct AgentValidationPkg {
    ...
    membrane_proof: Option<SerializedBytes>
}
```

- InitZomesComplete: indicates the creation of the final genesis entry that marks that all zome init functions have successfully completed (see the [HDK](#page-40-0) section for details), and the chain is ready for commits. Requires no additional data.
- Create: indicates the creation of an application-defined entry, or a system-defined entry that needs to exist as content-addressed data.

```
struct Create {
    ...
    entry_type: EntryType,
    entry_hash: EntryHash,
}
// See the section on Entries for the definition of `EntryType`.
```

• Update: Mark an existing entry and its creation action as updated by itself. In addition to referencing the new entry, the action data points to the old action and its entry. As this is an entry creation action like Create, it shares many of the same fields.

```
struct Update {
    ...
    original_action_address: ActionHash,
    original_entry_address: EntryHash,
    entry_type: EntryType,
    entry_hash: EntryHash,
}
```

• Delete: Marks an existing entry and its creation action as deleted. The entry containing the hashes of the action and entry to be deleted are contained in the action struct.

```
struct Delete {
    ...
    deletes_address: ActionHash,
    deletes_entry_address: EntryHash,
}
```

• CreateLink: Indicates the creation of a link.

```
struct CreateLink {
    ...
    base_address: AnyLinkableHash,
    target_address: AnyLinkableHash,
    zome_index: u8,
    link_type: u8,
    tag: Vec<u8>,
}
```

• DeleteLink: Indicates the marking of an existing link creation action as deleted.

```
struct DeleteLink {
    ...
    base_address: AnyLinkableHash,
    link_add_address: ActionHash,
}
```

• CloseChain: indicates the creation of a final chain entry with data about a new DNA version to migrate to.

```
struct CloseChain {
    ...
```

```
new_dna_hash: DnaHash,
}
```

• OpenChain: indicates the creation of an entry with data for migrating from a previous DNA version.

```
struct OpenChain {
    ...
    prev_dna_hash: DnaHash,
}
```

All of the CRUD actions MUST include data to implement rate-limiting so as to prevent malicious network actions. In our implementation, all CRUD actions have a weight field of the following type:

```
struct RateWeight {
    bucket_id: u8,
    units: u8,
}
```

An application may specify an arbitrary number of rate limiting 'buckets', which can be 'filled' by CRUD actions until they reach their capacity, after which point any further attempts to record an action to the Source Chain will fail until the bucket has drained sufficiently. Each bucket has a specified capacity and drain rate, which the Integrity Zome may specify using a rate\_limits callback.

The Integrity Zome may also weigh a given CRUD action using a weigh callback, which allows both the author and the validating authority to deterministically assign a weight to an action.

**Note:** This feature is not completed in the current implementation.

**The Entry Data Type** There are four main entry types, defined in an EntryType enum:

```
enum EntryType {
    AgentPubKey,
    App(AppEntryDef),
    CapClaim,
    CapGrant,
}
```

There is also an Entry enum that holds the entry data itself, with five variants that correspond to the four entry types:

```
enum Entry {
    Agent(AgentHash),
    App(SerializedBytes),
    CounterSign(CounterSigningSessionData, SerializedBytes),
    CapClaim(CapClaim),
    CapGrant(ZomeCallCapGrant),
}
```

(Note that the App and CounterSign variants are both intended for application-defined entries.)

- AgentPubKey is used in the second genesis record of the source chain, a Create action that publishes the source chain author's public key to the DHT for identification and verification of authorship.
- App indicates that the entry data contains arbitrary application data of a given entry type belonging to a given integrity zome:

```
struct AppEntryDef {
    entry_index: u8,
    zome_index: u8,
    visibility: EntryVisibility,
}
struct EntryVisibility {
    Public,
    Private,
}
```

Its entry data can be of either Entry::App or Entry::CounterSign, where the inner data is an arbitrary vector of bytes (typically a serialized data structure). If the data is Entry::CounterSign, the bytes are accompanied by a struct that gives the details of the countersigning session (this struct will be dealt with in the [Countersigning](#page-18-0) section).

Note that in both these cases the data is stored using a serialization that is declared by the entry\_defs() function of the HDI.

• CapClaim indicates that the entry data contains the details of a granted capability that are necessary to exercise such capability:

```
struct CapClaim {
    tag: String,
    grantor: AgentHash,
    secret: CapSecret,
}
```

• CapGrant indicates that the entry data contains the details of a capability grant in the following enum and the types upon which it depends:

```
struct ZomeCallCapGrant {
    tag: String,
    access: CapAccess,
    functions: GrantedFunctions,
}
enum CapAccess {
    Unrestricted,
    Transferable {
        secret: [u8; 64],
    },
    Assigned {
        secret: [u8; 64],
        assignees: BTreeSet<AgentHash>,
    },
}
enum GrantedFunctions {
    All,
    Listed(BTreeSet<(ZomeName, FunctionName), Global>),
}
struct ZomeName(str);
struct FunctionName(str);
```

**The Record Data Type** A record is just a wrapper for an Action and an Entry. Because an entry may not be present in all contexts or for all action types, the RecordEntry enum wraps the possible entry data in an appropriate status.

```
struct Record {
    action: SignedHashed<Action>,
    entry: RecordEntry,
}
enum RecordEntry {
    Present(Entry),
    Hidden,
    NA,
    NotStored,
}
```

**Links** A CreateLink action completely contains the relational graph information, which would be considered the link's entry data if it were to have a separate entry. Note that links are typed for performance purposes, such that when requesting links they can be retrieved by type. Additionally links have tags that can be used as arbitrary labels on-graph as per the application's needs. The zome\_index is necessary so that the system can find and dispatch the correct validation routines for that link, as a DNA may have multiple integrity zomes.

```
struct Link {
    base_address: AnyLinkableHash,
    target_address: AnyLinkableHash,
    zome_index: ZomeIndex,
    link_type: LinkType,
    tag: LinkTag,
}
struct LinkTag(Vec<u8>);
```

Comparing this structure to a Resource Description Framework (RDF) triple:

- The base\_address is the subject.
- The target\_address is the object.
- The zome\_index, link\_type, and tag as a tuple are the predicate.

**The Op Data Type** The Op types that hold the chain entry data that is published to different portions of the DHT (formally described in the Graph [Transformation](#page-20-0) section of Formal Design Elements) are listed below. The integrity zome defines a validation callback for the entry and link types it defines, and is called with an Op enum variant as its single parameter, which indicates the DHT perspective from which to validate the data. Each variant holds a struct containing the DHT operation payload:

• StoreRecord: executed by the record (action) authorities to store data. It contains the record to be validated, including the entry if it is public.

```
struct StoreRecord {
    record: Record,
}
```

• StoreEntry: executed by the entry authorities to store data for any entry creation action, if the entry is public. It contains both the entry and the action in a struct similar to Record, with the exception that the entry field is always populated.

```
struct StoreEntry {
    action: SignedHashed<EntryCreationAction>,
    entry: Entry,
}
// The following variants hold the corresponding Action struct.
enum EntryCreationAction {
    Create(Create),
    Update(Update),
}
```

• RegisterUpdate: executed by both the entry and record authorities for the *old* data to store metadata pointing to the *new* data. This op collapses both the RegisterUpdatedRecord and RegisterUpdatedContent operations into one for simplicity. It contains the update action as well as the entry, if it is public.

```
struct RegisterUpdate {
    update: SignedHashed<Update>,
    new_entry: Option<Entry>,
}
```

• RegisterDelete: executed by the entry authorities for the *old* entry creation and its entry to store metadata that tombstones the data. This opp collapses both the RegisterDeletedEntryAction and RegisterDeletedBy operations into one. It contains only the delete action.

```
struct RegisterDelete {
    delete: SignedHashed<Delete>,
}
```

• RegisterAgentActivity: executed by agent activity authorities (the peers responsible for the author's AgentID entry) to validate the action in context of the author's entire source chain. At the application developer's discretion, this operation can also contain the entry data.

```
struct RegisterAgentActivity {
    action: SignedHashed<Action>,
    cached_entry: Option<Entry>,
}
```

• RegisterCreateLink: executed by the authorities for the link's base address to store link metadata.

```
struct RegisterCreateLink {
    create_link: SignedHashed<CreateLink>,
}
```

• RegisterDeleteLink: executed by the authorities for the link's base address to store metadata that tombstones the link.

```
struct RegisterDeleteLink {
    delete_link: SignedHashed<DeleteLink>,
    create_link: CreateLink,
}
```

*Hash Data Structures* Holochain relies on being able to distinguish and use hashes of the various Holochain fundamental data types. The following hash types must exist:

- ActionHash: The Blake2b-256 hash of a serialized Action variant, used for DHT addressing.
- AgentHash: The Ed25519 public key of an agent, used for referencing the agent.
- DhtOpHash: The Blake2b-256 hash of a serialized DhtOp variant, used for comparing lists of held operations during syncing between authorities.
- DnaHash: The hash of all the integrity zomes and associated modifiers, when serialized in a consistent manner.
- EntryHash: The hash of the bytes of a Entry variant, according to the hashing rules of that variant (the Blake2b-256 hash of the serialized variant in all cases except Entry::Agent, which is the public key). Used for DHT addressing.
- ExternalHash: This type is used for creating links in the graph DHT to entities that are not actually stored in the DHT. It is simply an arbitrary 32 bytes.
- WasmHash: The Blake2b-256 hash of the WebAssembly bytecode of a zome, used by the Ribosome to look up and call zomes.

Furthermore, there are two composite hash types, which are unions of two or more of the preceding hash types:

- AnyDhtHash, the enum of EntryHash and ActionHash, is the union of all 'real' addressable content on the DHT; that is, content that can actually be written.
- AnyLinkableHash, the enum of EntryHash, ActionHash, and ExternalHash, is the union of all real and imaginary addressable content on the DHT; that is, it includes external hashes.

All of these hash types are derived from a generic struct, HoloHash<T>, which holds the three-byte hash type signifier and the 32 bytes of the hash (the 'core' of the hash), along with the 4-byte network location. For those hash types that are the basis of addressable content (AnyDhtHash), the hash alone is sufficient to uniquely identify a DHT basis from which a network location can be computed, while the type signifier ensures type safety in all struct fields and enum variant values that reference the hash. The four-byte network location is computed from the hash core and stored along with the preceding 36 bytes as a matter of convenience.

The three-byte type signifiers are as follows:

| Type       | Hexadecimal Base64 |      |
|------------|--------------------|------|
| ActionHash | 0x842924           | hCkk |
| AgentHash  | 0x842024           | hCAk |
| DhtOpHash  | 0x842424           | hCQk |
| DnaHash    | 0x842d24           | hC0k |
| EntryHash  | 0x842124           | hCEk |
|            |                    |      |

| Type                  | Hexadecimal Base64 |      |
|-----------------------|--------------------|------|
| ExternalHash 0x842f24 |                    | hC8k |
| WasmHash              | 0x842a24           | hCok |

*Application Type Definition Callbacks* In order for the Ribosome to successfully dispatch validation to the correct integrity zome, each integrity zome in a DNA should register the entry and link types it is responsible for validating. The HDI MUST allow the integrity zome to implement the following functions:

• entry\_defs(()) -> ExternResult<EntryDefsCallbackResult>: Called to declare the type and structure of the application's entry types. The return value is:

```
enum EntryDefsCallbackResult {
    Defs(EntryDefs),
}
struct EntryDefs(Vec<EntryDef>);
struct EntryDef {
    id: EntryDefId,
    visibility: EntryVisibility,
    required_validations: u8,
    cache_at_agent_activity: bool,
}
enum EntryDefId {
    App(str),
    CapClaim,
    CapGrant,
}
```

This function can be automatically generated using the #[hdk\_entry\_types] procedural macro on an enum of variants that each hold a type that can be serialized and deserialized.

• link\_types(()) -> ExternResult<Vec<u8>>: called to declare the link types that will be used by the application. This function can be automatically generated using the #[hdk\_link\_types] procedural macro on an enum of all link types.

Note: In our implementation these functions are automatically generated by Rust macros. This gives us the benefit of consistent, strongly typed entry and link types from the point of definition to the point of use. Thus it's very easy to assure that any application data that is being stored adheres to the entry and link type declarations.

*Functions Necessary for Application Validation* The HDI MUST allow for hApp developers to specify a validate(Op) -> ExternResult<ValidateCallbackResult> callback function for each integrity zome. This callback is called by the Ribosome in the correct context for the Op as described above in the graph DHT formalization, so that the data associated with the Op will only be stored if it meets the validation criteria.

The HDI MUST also allow for hApp developers to specify a genesis\_self\_check(GenesisSelfCheckData) -> ExternResult<ValidateCallbackResult> callback for each integrity zome. This callback is called by the Ribosome *before* attempting to join a network, to perform sanity checks on the genesis records. This callback is limited in its ability to validate genesis data, because it MUST NOT be able to make network calls. Nevertheless, it is useful to prevent a class of errors such as incorrect user entry of membrane proofs from inadvertently banning a new agent from the network. The input payload is defined as:

```
struct GenesisSelfCheckData {
    membrane_proof: Option<SerializedBytes>,
    agent_key: AgentHash,
}
```

The HDI MUST provide the following functions for application authors to retrieve dependencies in validation:

• must\_get\_agent\_activity(AgentPubKey, ChainFilter) -> ExternResult<Vec<RegisterAgentActivity>>: This function allows for deterministic validation of chain activity by making a hash-bounded range of an agent's chain into a dependency for something that is being validated. The second parameter is defined as:

```
struct ChainFilter {
    chain_top: ActionHash,
    filters: ChainFilters,
    include_cached_entries: bool
}
enum ChainFilters {
    ToGenesis,
    Take(u32),
    Until(HashSet<ActionHash>),
    Both(u32, HashSet<ActionHash>),
}
The vector element type in the return value is defined as:
struct RegisterAgentActivity {
    action: SignedHashed<Action>,
    cached_entry: Option<Entry>,
}
```

- must\_get\_action(ActionHash) -> ExternResult<SignedHashed<Action>: Get the Action at a given action hash, along with its author's signature.
- must\_get\_entry(EntryHash) -> ExternResult<HoloHashed<Entry>>: Get the Entry at a given hash.
- must\_get\_valid\_record(ActionHash) -> ExternResult<Record>: Attempt to get a *valid* Record at a given action hash; if the record is marked as invalid by any contacted authorities, the function will fail.

The HDI MUST implement two hashing functions that calculate the hashes of Actions and Entrys so that hash values can be confirmed in validation routines.

- hash\_action(Action) -> ActionHash
- hash\_entry(Entry) -> EntryHash

The HDI MUST implement two introspection functions that return data about the DNA's definition and context that may be necessary for validation:

• dna\_info() -> ExternResult<DnaInfo>: returns information about the DNA:

```
struct DnaInfo {
      name: String,
      hash: DnaHash,
      modifiers: DnaModifiers,
      zome_names: Vec<ZomeName>,
  }
  struct DnaModifiers {
      network_seed: String,
      properties: SerializedBytes,
      origin_time: Timestamp,
      quantum_time: Duration,
  }
• zome_info() -> ExternResult<ZomeInfo>: returns information about the integrity zome:
  struct ZomeInfo {
      name: ZomeName,
      id: ZomeIndex,
      properties: SerializedBytes,
      entry_defs: EntryDefs,
      extern_fns: Vec<FunctionName>,
      zome_types: ScopedZomeTypesSet,
  }
  struct ZomeIndex(u8);
```

```
struct ScopedZomeTypesSet {
    entries: Vec<(ZomeIndex, Vec<EntryDefIndex>)>,
    links: Vec<(ZomeIndex, Vec<LinkType>)>,
}
struct EntryDefIndex(u8);
struct LinkType(u8);
```

Note: properties consists of known application-specified data that is specified at install time (both at the DNA and zome levels) that may be necessary for validation or any other application-defined purpose. Properties are included when hashing the DNA source code, thus allowing parametrized DNAs and zomes.

The HDI MUST implement a function that validation code can use to verify cryptographic signatures:

• verify\_signature<I>(AgentPubKey, Signature, I) -> ExternResult<bool> where I: Serialize: Checks the validity of a signature (a Vec<u8> of bytes) upon the data it signs (any type that implements the Serialize trait, allowing it to be reproducibly converted into a vector of bytes, against the public key of the agent that is claimed to have signed it.

#### HDK

<span id="page-40-0"></span>The HDK contains all the functions and callbacks needed for Holochain application developers to build their Coordination Zomes. Note that the HDK is a superset of the HDI. Thus all of the functions and data types available in the HDI are also available in the HDK.

*Initialization* The HDK MUST allow application developers to define an init() -> ExternResult<InitCallbackResult> callback in each coordinator zome. All init callbacks in all coordinator zomes MUST complete successfully, and an InitZomesComplete action MUST be written to a cell's source chain, before zome functions (see [following](#page-40-1) section) may be called. Implementations SHOULD allow this to happen lazily; that is, a zome function is permitted to be called before initialization, and the call zome workflow runs the initialization workflow in-process if InitZomesComplete does not exist on the source chain yet.

The return value of the callback is defined as:

```
enum InitCallbackResult {
    Pass,
    Fail(String),
    UnresolvedDependencies(UnresolvedDependencies),
}
```

If the return value of all init callbacks is Pass, the actions in the scratch space prepared for the initialization workflow are written to the source chain, followed by the InitZomesComplete action, and execution of zome functions in the cell may proceed.

If the return value of at least one init callback is Fail, the cell is put into a permanently disabled state.

If the return value of at least one init callback is UnresolvedDependencies, the scratch space prepared for the initialization workflow is discarded, and the initialization workflow will be attempted upon next zome function call. This permits a cell to gracefully handle a temporary poorly connected state on cell instantiation.

<span id="page-40-1"></span>*Arbitrary API Functions (Zome Functions)* The HDK MUST allow application developers to define and expose functions in their Coordinator Zomes with arbitrary names, input payloads, and return payloads that serve as the application's API. While the content of the return payload of these functions may be arbitrary data, it MUST be wrapped in a Result<T, WasmError>, where T is the return payload.

As function calls across the host/guest interface only deal with arbitrary bytes stored in memory address ranges, the HDK SHOULD provide an abstraction to allow developers to define functions in a more natural manner, with typed input and return payloads. We have provided a #[hdk\_extern] procedural macro that facilitates this abstraction, wrapping the following function definition with the necessary machinery to load and deserialize the input data and serialize and store the return data.

The Conductor MUST also receive calls to these zome functions, enforce capability restrictions, dispatch the call to the correct WASM module, and handle side effects, error conditions, and the called function's return value. These calls MAY come from external clients, other zomes in the same cell, other cells in the same application, or other agents in the same DHT.

*Post-Commit Callback* The HDK MUST allow application developers to define a post\_commit(Vec<SignedAction>) -> ExternResult<()> callback in their Coordinator Zomes which receives a sequence of Actions committed to the source chain. The purpose of this callback is to provide a way of triggering follow-up activities when an atomic commit has definitively succeeded in persisting new Actions.

The Conductor MUST call this callback with all the Actions successfully committed in any guest function that is permitted to persist state changes to the source chain. The Conductor MUST NOT permit this callback to make further state changes, but it MAY allow it to access any other host functions, including calling or scheduling other functions which may make state changes in their own call contexts.

*Chain Operations* The HDK MUST implement the following functions that create source chain entries:

• create(CreateInput) -> ExternResult<ActionHash>: Records the creation of a new application entry. The CreateInput parameter is defined as:

```
struct CreateInput {
    entry_location: EntryDefLocation,
    entry_visibility: EntryVisibility,
    entry: Entry,
    chain_top_ordering: ChainTopOrdering,
}
enum EntryDefLocation {
    App(AppEntryDefLocation),
    CapClaim,
    CapGrant,
}
struct AppEntryDefLocation {
    zome_index: ZomeIndex,
    entry_def_index: EntryDefIndex,
}
enum ChainTopOrdering {
    Relaxed,
    Strict,
}
```

The EntryVisibility parameter specifies whether the entry is private or should be published to the DHT, and the ChainTopOrdering parameter specifies whether the call should fail if some other zome call with chain creation actions completes before this one, or whether it's ok to automatically replay the re-write the action on top of any such chain entries.

In our implementation, the create function accepts any value that can be converted to a CreateInput, allowing most of these fields to be populated by data that was generated by the #[hdk\_entry\_types] macro and other helpers. This is accompanied by convenience functions for create that accept app entries, capability grants, or capability claims.

• update(UpdateInput) -> ExternResult<ActionHash>: Records the marking of an existing entry and its creation action as updated. Requires the ActionHash that created the original entry to be provided. The UpdateInput parameter is defined as:

```
struct UpdateInput {
    original_action_address: ActionHash,
    entry: Entry,
    chain_top_ordering: ChainTopOrdering,
}
```

Many fields necessary for create are unnecessary for update, as the new entry is expected to match the entry type and visibility of the original. Similar to create, in our implementation there are convenience functions to help with constructing UpdateInputs for app entries and capability grants.

• delete(DeleteInput) -> ExternResult<ActionHash>: Records the marking of an entry and its creation action as deleted. The DeleteInput parameter is defined as:

```
struct DeleteInput {
    deletes_action_hash: ActionHash,
    chain_top_ordering: ChainTopOrdering,
}
```

- create\_link(AnyLinkableHash, AnyLinkableHash, ScopedLinkType, LinkTag) -> ExternResult<ActionHash>: Records the creation of a link of the given ScopedLinkType between the hashes supplied in the first and second arguments, treating the first hash as the base and the second as the target. The fourth LinkTag parameter is a struct containing a Vec<u8> of arbitrary application bytes.
- delete\_link(ActionHash) -> ExternResult<ActionHash>: Records the marking of a link creation action as deleted, taking the original link creation action's hash as its input.
- query(ChainQueryFilter) -> ExternResult<Vec<Record>>: search the agent's local source chain according to a query filter returning the Records that match. The ChainQueryFilter parameter is defined as:

```
struct ChainQueryFilter {
    sequence_range: ChainQueryFilterRange,
    entry_type: Option<Vec<EntryType>>,
    entry_hashes: Option<HashSet<EntryHash>>,
    action_type: Option<Vec<ActionType>>,
    include_entries: bool,
    order_descending: bool,
}
enum ChainQueryFilterRange {
    // Retrieve all chain actions.
    Unbounded,
    // Retrieve all chain actions between two indexes, inclusive.
    ActionSeqRange(u32, u32),
    // Retrieve all chain actions between two hashes, inclusive.
    ActionHashRange(ActionHash, ActionHash),
    // Retrieve the n chain actions up to and including the given hash.
    ActionHashTerminated(ActionHash, u32),
}
```

*Capabilities Management* The HDK includes convenience functions over create, update, and delete for operating on capability grants and claims:

- create\_cap\_grant(ZomeCallCapGrant) -> ExternResult<ActionHash>
- create\_cap\_claim(CapClaim) -> ExternResult<ActionHash>
- update\_cap\_grant(ActionHash, ZomeCallCapGrant) -> ExternResult<ActionHash>
- delete\_cap\_grant(ActionHash) -> ExternResult<ActionHash>

In addition to these, a function is provided for securely generating capability secrets:

• generate\_cap\_secret() -> ExternResult<[u8; 64]>

It is the application's responsibility to retrieve a stored capability claim using a host function such as query and supply it along with a remote call to another agent. As the Conductor at the receiver agent automatically checks and enforces capability claims supplied with remote call payloads, there is no need to retrieve and check a grant against a claim. *DHT Data Retrieval*

- <span id="page-42-0"></span>• get(AnyDhtHash, GetOptions) -> ExternResult<Option<Record>>: Retrieve a Record from the DHT by its EntryHash or ActionHash. The content of the record return is dependent on the type of hash supplied:
  - **–** If the hash is an Entry hash, the authority will return the entry content paired with its oldest-timestamped Action.
  - **–** If the hash is an Action hash, the authority will return the specified action.

The GetOptions parameter is defined as:

```
struct GetOptions {
    strategy: GetStrategy,
}
```

```
enum GetStrategy {
    Network,
    Local,
}
```

If strategy is GetStrategy::Network, the request will always go to other DHT authorities, unless the the requestor is an authority for that basis hash themselves. If strategy is GetStrategy::Local, the request will always favor the requestor's local cache and will return nothing if the data is not cached.

• get\_details(AnyDhtHash, GetOptions) -> ExternResult<Option<Details>>: Retrieve all of the addressable data and metadata at a basis hash. The return value is a variant of the following enum, depending on the data stored at the hash:

```
enum Details {
    Record(RecordDetails),
    Entry(EntryDetails),
}
struct RecordDetails {
    record: Record,
    validation_status: ValidationStatus,
    deletes: Vec<SignedHashed<Action>>,
    updates: Vec<SignedHashed<Action>>,
}
enum ValidationStatus {
    // The `StoreRecord` operation is valid.
    Valid,
    // The `StoreRecord` operation is invalid.
    Rejected,
    // Could not validate due to missing data or dependencies, or an
    // exhausted WASM execution budget.
    Abandoned,
    // The action has been withdrawn by its author.
    Withdrawn,
}
struct EntryDetails {
    entry: Entry,
    actions: Vec<SignedHashed<Action>>,
    rejected_actions: Vec<SignedHashed<Action>>,
    deletes: Vec<SignedHashed<Action>>,
    updates: Vec<SignedHashed<Action>>,
    entry_dht_status: EntryDhtStatus,
}
enum EntryDhtStatus {
    // At least one `StoreEntry` operation associated with the entry is
    // valid, and at least one entry creation action associated with it has
    // not been deleted.
    Live,
    // All entry creation actions associated with the entry have been marked
    // as deleted.
    Dead,
    // All `StoreEntry` operations are waiting validation.
    Pending,
    // All `StoreEntry` operations associated with the entry are invalid.
    Rejected,
    // All attempts to validate all `StoreEntry` operations associated with
    // the entry have been abandoned.
```

```
Abandoned,
    // All entry creation actions associated with the entry have been
    // withdrawn their authors.
    Withdrawn,
    // The entry data has been purged.
    Purged,
}
```

• get\_links(GetLinksInput) -> ExternResult<Vec<Link>>: Retrieve a list of links that have been placed on any base hash on the DHT, optionally filtering by the links' types and/or tags. The returned list contains only live links; that is, it excludes the links that have DeleteLink actions associated with them. The GetLinksInput parameter is defined as:

```
struct GetLinksInput {
    base_address: AnyLinkableHash,
    link_type: LinkTypeFilter,
    get_options: GetOptions,
    tag_prefix: Option<Vec<u8>>,
    after: Option<Timestamp>,
    before: Option<Timestamp>,
    author: Option<AgentHash>,
}
enum LinkTypeFilter {
    // One link type
    Types(Vec<(ZomeIndex, Vec<LinkType>)>),
    // All link types from the given integrity zome
    Dependencies(Vec<ZomeIndex>),
}
```

• get\_link\_details(AnyLinkableHash, LinkTypeFilter, Option<LinkTag>, GetOptions) -> ExternResult<LinkDetails>: Retrieve the link creation *and* deletion actions at a base. The return value is defined as:

```
struct LinkDetails(Vec<(SignedActionHashed, Vec<SignedActionHashed>)>);
```

where each element in the vector is a CreateLink action paired with a vector of any DeleteLink actions that apply to it.

- count\_links(LinkQuery) -> ExternResult<usize>: Retrieve only the count of live links matching the link query.
- get\_agent\_activity(AgentPubKey, ChainQueryFilter, ActivityRequest) -> ExternResult<AgentActivity>: Retrieve the activity of an agent from the agent's neighbors on the DHT. This functions similar to query, but operates on the source chain of an agent *other* than the requestor. The ActivityRequest parameter is defined as:

```
enum ActivityRequest {
    Status,
    Full,
}
The AgentActivity return value is defined as:
struct AgentActivity {
    valid_activity: Vec<(u32, ActionHash)>,
    rejected_activity: Vec<(u32, ActionHash)>,
    status: ChainStatus,
    highest_observed: Option<(u32, ActionHash)>,
    warrants: Vec<Warrant>,
}
enum ChainStatus {
    Empty,
```

```
Valid(ChainHead),
    Forked(ChainFork),
    Invalid(ChainHead),
}
struct ChainHead {
    action_seq: u32,
    hash: ActionHash,
}
struct ChainFork {
    fork_seq: u32,
    first_action: ActionHash,
    second_action: ActionHash,
}
```

Depending on the value of the ActivityRequest argument, status may be the only populated field.

• get\_validation\_receipts(GetValidationReceiptsInput) -> ExternResult<Vec<ValidationReceiptSet>>: Retrieve information about how 'persisted' the DHT operations for an Action are. This is meant to provide end-user feedback on whether an agent's authored data can easily be retrieved by other peers. The input argument is defined as:

```
struct GetValidationReceiptsInput {
         action_hash: ActionHash,
     }
    The return value is defined as a vector of:
     struct ValidationReceiptSet {
         // The DHT operation hash that this receipt is for.
         op_hash: DhtOpHash,
         // The type of the op that was validated. This represents the underlying
         // operation type and does not map one-for-one to the `Op` type used in
         // validation.
         op_type: String,
         // Whether this op has received the required number of receipts.
         receipts_complete: bool,
         // The validation receipts for this op.
         receipts: Vec<ValidationReceiptInfo>,
     }
Introspection
```

• agent\_info() -> ExternResult<AgentInfo>: Get information about oneself (that is, the agent currently executing the zome function) and one's source chain, where the return value is defined as:

```
struct AgentInfo {
    agent_initial_pubkey: AgentHash,
    agent_latest_pubkey: AgentHash,
    chain_head: (ActionHash, u32, Timestamp),
}
```

The initial and latest public key may vary throughout the life of the source chain, as an AgentPubKey is an entry which may be updated like other entries. Updating a key entry is normally handled through a DPKI implementation (see [Human](#page-13-0) Error section of System Correctness: Confidence).

• call\_info() -> ExternResult<CallInfo>: Get contextual information about the current zome call, where the return value is defined as:

```
struct CallInfo {
    provenance: AgentHash,
    function_name: FunctionName,
    // A snapshot of the source chain state at zome call time.
    as_at: (ActionHash, u32, Timestamp),
```

```
// The capability grant under which the call is permitted.
    cap_grant: CapGrant,
}
```

- dna\_info() -> ExternResult<DnaInfo> (see HDI)
- zome\_info() -> ExternResult<ZomeInfo> (see HDI)

*Modularization and Composition* Zomes are intended to be units of composition for application developers. Thus zome functions MUST be able to make calls to other zome functions, either in the same zome or in other zomes or even DNAs:

• call<I>(CallTargetCell, ZomeName, FunctionName, Option<CapSecret>, I) -> ZomeCallResponse where I: Serialize: Call a zome function in a local cell, supplying a capability and a payload containing the argument to the receiver. The CallTargetCell parameter is defined as:

```
enum CallTargetCell {
    // Call a function in another cell by its unique conductor-local ID, a
    // tuple of DNA hash and agent public key.
    OtherCell(CellId),
    // Call a function in another cell by the role name specified in the app
    // manifest. This role name may be qualified to a specific clone of the
    // DNA that fills the role by appending a dot and the clone's index.
    OtherRole(String),
    // Call a function in the same cell.
    Local,
}
```

**struct** CellId(DnaHash, AgentPubKey);

**struct** ClonedCell {

*Clone Management* The HDK SHOULD implement the ability for cells to modify the running App by adding, enabling, and disabling clones of existing DNA.

• create\_clone\_cell(CreateCloneCellInput) -> ExternResult<ClonedCell>: Create a clone of an existing DNA installed with the App, specifying new modifiers and optionally a membrane proof. The input parameter is defined as:

```
struct CreateCloneCellInput {
    // The ID of the cell to clone.
    cell_id: CellId,
    // Modifiers to set for the new cell. At least one of the modifiers must
    // be set to obtain a distinct hash for the clone cell's DNA.
    modifiers: DnaModifiersOpt<YamlProperties>,
    // Optionally set a proof of membership for the clone cell.
    membrane_proof: Option<MembraneProof>,
    // Optionally a name for the DNA clone.
    name: Option<String>,
}
struct DnaModifiersOpt<P> {
    network_seed: Option<String>,
    properties: Option<P>,
    origin_time: Option<Timestamp>,
    // The smallest size of time regions for historical gossip.
    quantum_time: Option<Duration>,
}
type MembraneProof = SerializedBytes;
Implementations MUST NOT enable the clone cell until enable_clone_cell is subsequently called.
The return value is defined as:
```

```
cell_id: CellId,
         // A conductor-local clone identifier.
         clone_id: CloneId,
         // The hash of the DNA that this cell was instantiated from.
         original_dna_hash: DnaHash,
         // The DNA modifiers that were used to instantiate this clone cell.
         dna_modifiers: DnaModifiers,
         // The name the cell was instantiated with.
         name: String,
         // Whether or not the cell is running.
         enabled: bool,
     }
  • disable_clone_cell(DisableCloneCellInput) -> ExternResult<()>: Disable an active clone cell in the
     current app. The input is defined as:
     struct DisableCloneCellInput {
         clone_cell_id: CloneCellId,
     }
     enum CloneCellId {
         // Clone ID consisting of role name and clone index.
         CloneId(CloneId),
         // Cell id consisting of DNA hash and agent key.
         CellId(CellId),
     }
     // A conductor-local unique identifier for a clone, consisting of the role
     // name from the app manifest and a clone index, delimited by a dot.
     struct CloneID(String);
  • enable_clone_cell(EnableCloneCellInput) -> ExternResult<ClonedCell>: Enable a cloned cell in the
     current app. The input is defined as:
     struct EnableCloneCellInput {
         clone_cell_id: CloneCellId,
     }
  • delete_clone_cell(DeleteCloneCellInput) -> ExternResult<()>: Delete an existing clone cell in the cur-
     rent app. The input is defined as:
     struct DeleteCloneCellInput {
         clone_cell_id: CloneCellId,
     }
Scheduling The HDK SHOULD implement the ability for zome calls to be scheduled for calling in the future, which
```

allows for important application functionality like automatic retries.

• schedule(str) -> ExternResult<()>: Schedule a function for calling on the next iteration of the conductor's scheduler loop, and thereafter on a schedule defined by the called function. To be schedulable, a function must have the signature (Schedule) -> Option<Schedule>, receiving the schedule on which it was called and returning the schedule (if any) on which it wishes to continue to be called. A Schedule is defined as:

```
enum Schedule {
    Persisted(String),
    Ephemeral(Duration),
}
```

Where the value of Persisted is a UNIX crontab entry and the value of Ephemeral is a duration until the next time. Persisted schedules survive conductor restarts and unrecoverable errors, while ephemeral schedules will not. If None is returned instead of Some(Schedule), the function will be unscheduled.

A scheduled function MUST also be **infallible**; that is, it must be marked with the macro #[hdk\_ extern(infallible)] and return an Option<Schedule> rather than an ExternResult<Option<Schedule>>. This is because there is no opportunity for user interaction with the result of a scheduled function.

*P2P Interaction* Agents MUST be able to communicate directly with other agents. They do so simply by making zome calls to them. Holochain systems MUST make this possible by sending a call requests over the network and awaiting a response. For performance reasons the HDK SHOULD also make possible sending of best-effort in parallel signals for which no return result is awaited.

• call\_remote<I>(AgentPubKey, ZomeName, FunctionName, Option<CapSecret>, I) -> ExternResult<ZomeCallResponse> where I: Serialize: Call a zome function on a target agent and zome, supplying a capability secret and an arguments payload. The return value is defined as:

```
enum ZomeCallResponse {
    Ok(ExternIO),
    Unauthorized(ZomeCallAuthorization, CellId, ZomeName, FunctionName, AgentHash),
    NetworkError(String),
    CountersigningSession(String),
}
enum ZomeCallAuthorization {
    Authorized,
    BadSignature,
    BadCapGrant,
    BadNonce(String),
    BlockedProvenance,
}
```

• send\_remote\_signal<I>(Vec<AgentPubKey>, I) -> ExternResult<()> where I: Serialize: Send a besteffort signal to a list of agents. Implementations SHOULD provide this function, SHOULD implement it by convention as a workflow that sends messages to the receivers as a remote call to a zome function with the signature recv\_remote\_signal(SerializedBytes) -> ExternResult<()> in the same coordinator zome as the function that calls this host function, and MUST NOT await responses from the receivers. Implementations MUST spawn a separate thread to send the signals in order to avoid blocking execution of the rest of the zome function call.

*Countersigning* In order to safely facilitate the peer interaction necessary to complete a countersigning among multiple agents, the Ribosome and HDK MUST implement the following functions:

• accept\_countersigning\_preflight\_request(PreflightRequest) -> ExternResult<PreflightRequestAcceptance>: Lock the local chain to commence a countersigning session. The PreflightRequestAcceptance MUST be sent back to the session initiator so that the corresponding entry can be built for everyone to sign. This function MUST be called by every signer in the signing session. The details of how are left to the application developer (although concurrent remote calls are probably the simplest mechanism to distribute and accept preflight requests before the session times out). The preflight request is defined as (see discussion above on countersigning):

```
struct PreflightRequest {
    // The hash of the app entry, as if it were not countersigned. The final
    // entry hash will include the countersigning session data.
    app_entry_hash: EntryHash,
    // The agents that are participating in this countersignature session.
    signing_agents: Vec<(AgentHash, Vec<Role>)>,
    // The optional additional M of N signers. If there are additional
    // signers then M MUST be the majority of N. If there are additional
    // signers then the enzyme MUST be used and is the first signer in BOTH
    // signing_agents and optional_signing_agents.
    optional_signing_agents: Vec<(AgentHash, Vec<Role>)>,
    // The M in the M of N signers. M MUST be strictly greater than than
    // N / 2 and NOT larger than N.
    minimum_optional_signing_agents: u8,
    // The first signing agent (index 0) is acting as an enzyme. If true AND
    // optional_signing_agents are set then the first agent MUST be the same
    // in both signing_agents and optional_signing_agents.
    enzymatic: bool,
    // The window in which countersigning must complete. Session actions
    // MUST all have the same timestamp, which is the session offset.
```

```
session_times: CounterSigningSessionTimes,
    // The action information that is shared by all agents. Contents depend
    // on the action type, create, update, etc.
    action_base: ActionBase,
    // Optional arbitrary bytes that can be agreed to.
    preflight_bytes: PreflightBytes,
}
struct CounterSigningSessionTimes {
    start: Timestamp,
    end: Timestamp,
}
enum ActionBase {
    Create(CreateBase),
    Update(UpdateBase),
}
struct CreateBase {
    entry_type: EntryType,
}
struct UpdateBase {
    original_action_address: ActionHash,
    original_entry_address: EntryHash,
    entry_type: EntryType,
}
// An arbitrary application-defined role in a session.
struct Role(u8);
The return value is defined as:
enum PreflightRequestAcceptance {
    Accepted(PreflightResponse),
    UnacceptableFutureStart,
    UnacceptableAgentNotFound,
    Invalid(String),
}
struct PreflightResponse {
    request: PreflightRequest,
    agent_state: CounterSigningAgentState,
    signature: Signature,
}
struct CounterSigningAgentState {
    // The index of the agent in the preflight request agent vector.
    agent_index: u8,
    // The current (frozen) top of the agent's local chain.
    chain_top: ActionHash,
    // The action sequence of the agent's chain top.
    action_seq: u32,
}
```

• session\_times\_from\_millis(u64) -> ExternResult<CounterSigningSessionTimes>: Create the session times that are included in the PreflightRequest and bound the countersigning session temporally. This function returns a session start timestamp is "now" from the perspective of the system clock of the session initiator calling this function, and a session end timestamp that is "now" plus the given number of milliseconds. The countersigning parties will check these times against their own perspectives of "now" as part of accepting

the preflight request, so all system clocks need to be roughly aligned, and the ambient network latency must fit comfortably within the session duration.

*Cryptography* The HDK MUST provide mechanisms for agents to sign and check the signatures of data. It SHOULD provide mechanisms to encrypt and decrypt data and return pseudo-random data:

- sign<D>(AgentPubKey, D) -> ExternResult<Signature> where D: Serialize: Given a public key, request from the key-management system a signature for the given data by the corresponding private key.
- verify\_signature<I>(AgentPubKey, Signature, I) -> ExternResult<bool> where I: Serialize: (see HDI)
- x\_salsa20\_poly1305\_shared\_secret\_create\_random(Option<XSalsa20Poly1305KeyRef>) -> ExternResult<XSalsa20Poly1305KeyRef>: Generate a secure random shared secret suitable for encrypting and decrypting messages using NaCl's secretbox[27](#page-50-0) encryption algorithm, and store it in the key-management system. An optional key reference ID may be given; if this ID already exists in the key-management system, an error will be returned. If no ID is given, one will be generated and returned. The key reference is defined as:

```
struct XSalsa20Poly1305KeyRef(u8);
```

• x\_salsa20\_poly1305\_encrypt(XSalsa20Poly1305KeyRef, Vec<u8>) -> ExternResult<XSalsa20Poly1305EncryptedData>: Given a reference to a symmetric encryption key stored in the key-management service, request the encryption of the given bytes with the key. The return value is defined as:

```
struct XSalsa20Poly1305EncryptedData {
    nonce: [u8; 24],
    encrypted_data: Vec<u8>,
}
```

- x\_salsa20\_poly1305\_decrypt(XSalsa20Poly1305KeyRef, XSalsa20Poly1305EncryptedData) -> ExternResult<Option<Vec<u8>>: Given a reference to a symmetric encryption key, request the decryption of the given bytes with the key.
- create\_x25519\_keypair() -> ExternResult<X25519PubKey>: Create an X25519 key pair suitable for encrypting and decrypting messages using NaCl's box[28](#page-50-1) algorithm, and store it in the key-management service. The return value is defined as:

```
struct X25519PubKey([u8; 32]);
```

- x\_25519\_x\_salsa20\_poly1305\_encrypt(X25519PubKey, X25519PubKey, Vec<u8>) -> ExternResult<XSalsa20Poly1305EncryptedData>: Given X25519 public keys for the sender and recipient, attempt to encrypt the given bytes via the box algorithm using the sender's private key stored in the key-management service and the receiver's public key.
- x\_25519\_x\_salsa20\_poly1305\_decrypt(X25519PubKey, X25519PubKey, Vec<u8>) -> ExternResult<XSalsa20Poly1305EncryptedData>: Given X25519 public keys for the recipient and sender, attempt to decrypt the given bytes via the box algorithm using the sender's public key and the receiver's private key stored in the key-management service.
- ed\_25519\_x\_salsa20\_poly1305\_encrypt(AgentPubKey, AgentPubKey, XSalsa20Poly1305Data) -> ExternResult<XSalsa20Poly1305EncryptedData>: Attempt to encrypt a message using the box algorithm, converting the Ed25519 signing keys of the sender and recipient agents into X25519 encryption keys. This procedure is not recommended[29](#page-50-2) by the developers of libsodium, the NaCl implementation used by Holochain.
- ed\_25519\_x\_salsa20\_poly1305\_decrypt(AgentHash, AgentHash, XSalsa20Poly1305EncryptedData) -> ExternResult<XSalsa20Poly1305Data>: Attempt to decrypt a message using the box algorithm, converting the Ed25519 signing keys of the recipient and sender agents into X22519 encryption keys. This procedure is not recommended by the developers of libsodium, the NaCl implementation used by Holochain.

*User Notification* The HDK SHOULD provide a way for zome code to notify the application user of events. To start with we have implemented a system where signals can be emitted from a zome:

• emit\_signal<I>(I) -> ExternResult<()> where I: Serialize: Emit the bytes as a signal to listening clients.

<span id="page-50-0"></span><sup>27</sup> See [https://nacl.cr.yp.to/secretbox.html.](https://nacl.cr.yp.to/secretbox.html)

<span id="page-50-1"></span><sup>28</sup> See [https://nacl.cr.yp.to/box.html.](https://nacl.cr.yp.to/box.html)

<span id="page-50-2"></span><sup>29</sup> See [https://doc.libsodium.org/quickstart#how-can-i-sign-and-en](https://doc.libsodium.org/quickstart#how-can-i-sign-and-encrypt-using-the-same-key-pair)[crypt-using-the-same-key-pair.](https://doc.libsodium.org/quickstart#how-can-i-sign-and-encrypt-using-the-same-key-pair)

*Anchors and Paths* A content-addressable store, accessible only by the hashes of stored items, is difficult to search because of the sparse nature of the hashes. Holochain's graph DHT makes it much easier to retrieve related information via the affordance of links that can be retrieved from a given hash address. A powerful pattern that can be built on top of links is what we call anchors and, more generally, paths. These patterns rely on the idea of starting from a known hash value that all parties can compute, and placing links from that hash to relevant entries. So, for example, one could take the hash of the string #funnycats and add links on that hash to all posts in a social media app that contain that hashtag. This pattern, the anchor pattern, affords the discovery of arbitrary collections or indexes of content-addressed data. The path pattern simply generalizes this to creating an arbitrary hierarchical tree of known values off of which to create links in the DHT.

A note about efficiency: Because every attempt to create an entry or link results in another record that needs to be validated and stored, implementations of this pattern SHOULD attempt to be idempotent when creating anchors or tags; that is, they should check for the prior existence of the links and entries that would be created before attempting to create them. It is both semantically and practically appropriate to hash the anchor or path string in-memory and wrap it in an ExternalHash for link bases and targets, as this avoids the the overhead of creating an entry, and the hash, which exists only in memory, can truly be said to be external to the DHT.

**Anchors** The HDK MAY provide functions to compute hashes from, and attach links to, known strings using the anchor pattern, which creates a two-level hierarchy of anchor types and anchors from which to link entries:

- anchor(ScopedLinkType, String, String) -> ExternResult<EntryHash>: Create an anchor type and/or anchor, linking from the 'root' anchor to the anchor type, and from the type to the anchor (if given). Return the anchor's hash.
- list\_anchor\_type\_addresses(ScopedLinkType) -> ExternResult<Vec<AnyLinkableHash>>: Retrieve the hashes of all anchor types created in the DHT. This permits ad-hoc runtime creation and discovery of anchor types.
- list\_anchor\_addresses(LinkType, String) -> ExternResult<Vec<AnyLinkableHash>>: Retrieve the hashes of all anchors for a given type.

**Paths** The HDK MAY provide functions to compute hashes from, and attach links to, known strings using the path pattern, which affords an arbitrary hierarchy of known hashes off of which to link entries:

```
struct Path(Vec<Component>);
struct Component(Vec<u8>);
struct TypedPath {
    link_type: ScopedLinkType,
    path: Path,
}
```

- root\_hash() -> ExternResult<AnyLinkableHash>: Compute and return the root hash of the path hierarchy, from which one can search for any previously registered paths; e.g. path\_children(path\_root()) will find all top-level paths. The bytes that make up the root node SHOULD be reasonably unique and well-known in order to avoid clashes with application data; our implementation uses the bytes [0x00, 0x01].
- Path::path\_entry\_hash() -> ExternResult<EntryHash>: Return the hash of a given path, which can then be used to search for items linked from that part of the path tree. Note that, in our implementation, entries are generated in memory and hashed but not recorded to the DHT.
- TypedPath::ensure() -> ExternResult<()>: Create links for every component of the path, if they do not already exist. This method SHOULD attempt to be idempotent.
- TypedPath::exists() -> ExternResult<bool>: Look for the existence in the DHT of all the path's components, and return true if all components exist.
- TypedPath::children() -> ExternResult<Vec<Link>>: Retrieve the links to the path's direct descendants. Note that these are *not* links to app-defined data but to nodes in the path hierarchy. App-defined data is expected to be linked to and retrieved from the path node's hash via the HDK's create\_link and get\_links functions.
- TypedPath::children\_details() -> ExternResult<Vec<LinkDetails>>: Retrieve details about the links to the path's direct descendants. This is equivalent to the HDK's get\_link\_details function.

• TypedPath::children\_paths() -> ExternResult<Vec<TypedPath>>: Retrieve the path's direct descendant nodes in the hierarchy as TypedPath values.

#### State Management via Workflows

The previous section describes the functions exposed to, and callable from, DNA code, such that developers can implement the integrity of a DNA (its structure and validation rules) and the functions that can be called on that integrity for authoring source chain entries and coherently retrieving that information from the application's DHT. This section describes the implementation requirements for recording and storing all aspects of Holochain's state. This includes agents' source-chain entries, the portion of the DHT data a node is holding, configuration data, caches, etc.

### Ontology of Workflows

While a properly defined and implemented Holochain system must necessarily be robust enough to handle data from an incorrectly operating peer, it is nevertheless a more productive experience for everyone if all nodes in a network change their states according to the same process. There are also cases in which an incorrect implementation may result in unrecoverable corruption to state.

Hence, we must define an **ontology of workflows**. A Workflow is defined ontologically as a process which:

- 1. Accesses and potentially changes Holochain state,
- 2. Receives an ephemeral input context necessary to do its job,
- 3. Optionally triggers other workflows to follow up on the newly changed state, potentially including another iteration of itself, and
- 4. Optionally returns a value which can be passed to a waiting receiver.

It is important to note that Workflows are reifications of the inherent physics of Holochain; that is, the concept of a Workflow is demanded by the kinds of state changes a Holochain implementation is expected to make.

The properties which hold for all Workflows are:

- A Workflow MUST operate only on an aspect of local Holochain state, and MUST NOT make assumptions about the value of any aspects of Holochain state it does not operate on, whether local or remote.
- A Workflow MUST NOT leave the state it operates on in a corrupt condition it fails for any reason, whether the failure is expected (such as validation failure) or unexpected (such as hardware malfunction). This means that it MUST either make an atomic and valid state change or make no state change at all.
  - **–** Corollary: a Workflow MUST treat the Holochain state upon which it operates as the ultimate source of truth about itself, which means that any other state it builds up during execution MUST be treated as incidental and disposable; that is, it MUST able to successfully recover from a failure and correctly change cryptographic state even if incidental state is lost.
- A Workflow MUST have direct access to the state it is manipulating so that it may observe it immediately before changing it, to avoid race conditions between Workflows that operate on the same state.
- A Workflow MUST operate on only one aspect of Holochain state, an aspect being defined as a portion of state which can be changed independently of other aspects.
- A change to Holochain state MUST be expressed monotonically. (This is merely a restatement of the fact that all changes of Holochain state are by nature monotonic.)
- If a Workflow operates on a contentious aspect of state, it MUST either:
  - **–** Be a singleton (that is, only one instance of the Workflow is permitted to run at any time), or
  - **–** Be permitted to run concurrently with another instance of itself and:
    - 1. Take a snapshot of the current value of the state when it begins to build a state change to be written,
    - 2. Check the current value of the state immediately before attempting to write a change, and
    - 3. Discard its attempted state change if the value of the state is now different from the snapshot.

We intend to publish an addendum which enumerates the necessary workflows, the aspects of Holochain state upon which they operate, and the ways in which they operate. In the meantime, the following diagram is a simplified overview.

![](_page_53_Figure_1.jpeg)

Shared Data (rrDHT)

In this section we detail some important implementation details of Holochain's graph DHT.
