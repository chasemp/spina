---
images: []
order: 17
title: Bundle Formats
---

Holochain implementations must be able to load Holochain applications that have been serialized, either to disk or for transmission over a network. Holochain uses a bundling format that allows for specification of properties along with other resources in a manifest that can include recursively bundled elements of the same general bundling format but adapted for different component types. The bundling format can also store the resources themselves within the same file; any of the sub-bundles can be specified by "location", which may be specified to be in the same bundle, in a separate file, or at a network address. Thus we have Zomes, DNAs, Apps, UIs, and WebApps that can all be wrapped up in a single bundle, or can reference components stored elsewhere.[32](#page-74-0) The manifests for each of the type of bundles that MUST be implemented are specified as follows:

*DNA Bundle Manifest* A DNA bundle manifest specifies the components that are critical to the operation of the DNA and affect its hash (the IntegrityManifest property) as well as the components that are supplied to facilitate the operation of a cell (the CoordinatorManifest property).

```
struct DnaManifestV1 {
    // A user-facing label for the DNA.
    name: String,
    integrity: IntegrityManifest,
    coordinator: CoordinatorManifest,
    // A list of ancestors of this DNA, used for satisfying dependencies on
    // prior versions of this DNA. The application's Coordinator interface is
    // expected to be compatible across the list of ancestors.
    lineage: Vec<DnaHashB64>,
}
struct IntegrityManifest {
    // A network seed for uniquifying this DNA.
    network_seed: Option<Vec<u8>>,
    // Any arbitrary application properties can be included in this object.
    // They may be accessed by DNA code to affect runtime behavior.
    properties: Option<YamlProperties>,
    // The time used to denote the origin of the network, used to calculate time
    // windows during gossip. All Action timestamps must come after this time.
    origin_time: HumanTimestamp,
    // An array of integrity zome manifests associated with the DNA. The order
    // is significant: it determines initialization order and affects the DNA
    // hash.
    zomes: Vec<ZomeManifest>,
}
struct CoordinatorManifest {
    // Coordinator zomes to install with this DNA.
    zomes: Vec<ZomeManifest>,
}
struct ZomeManifest {
    // A user-facing label for the zome.
    name: ZomeName,
    // The hash of the WebAssembly bytecode which defines this zome.
    hash: Option<WasmHashB64>,
    // The location of the wasm for this zome.
    location: Location,
    // The integrity zomes this zome depends on. The order of these MUST match
    // the order the types are used in the zome.
    dependencies: Option<Vec<ZomeName>>,
}
```

<span id="page-74-0"></span><sup>32</sup> The "meta bundle" format can be seen here: [https://github.com/holochain/holochain/tree/develop/crates/mr\\_](https://github.com/holochain/holochain/tree/develop/crates/mr_bundle) [bundle.](https://github.com/holochain/holochain/tree/develop/crates/mr_bundle)

```
enum Location {
    Bundled(PathBuf),
    // Get the file from the local filesystem (not bundled).
    Path(PathBuf),
    // Get the file from a URL.
    Url(String),
}
```

*App Bundle Manifest* An AppBundle combines together a set of DNAs paired with "Role" identifiers and instructions for how/when the Conductor should instantiate DNAs to make cells in the bundle. The "role" of DNA is useful for application developers to be able to specify a DNA by a semantically accessible name rather than just its hash. This also allows for "late-binding" as DNAs may be used in different ways in applications, and thus we can think of the DNA's name by the role it plays in a given application.

There is a number of ways that application developers MUST be able to specify conditions under which DNAs are instantiated into Cells in the Conductor:

- The basic use case is simply that a DNA is expected to be instantiated as a Cell. There MUST be an option to defer instantiation of the installed DNA until a later time, thus implementing a "lazy loading" strategy.
- There is a number of use cases where a Holochain application will also expect a Cell of a given DNA to already have instantiated and relies on this behavior, and fail otherwise. Thus, there MUST be a provisioning option to specify this use case. There also SHOULD be a way of signalling to the conductor that the dependency SHOULD NOT be disabled or uninstalled until the dependent app is uninstalled.
- Holochain Conductors MUST also implement a "cloning" mechanism to allow applications to dynamically create new Cells from an existing DNA via the App interface (see Conductor API below). Cloned cells are intended to be used for such use cases as adding private workspaces to apps where only a specific set of agents are allowed to join the DHT of that DNA, such as private channels; or for creating DHTs that have temporary life-spans in app, like logs that get rotated. DNAs that are expected to be cloned MUST be specified as such in the DNA Bundle so that the Conductor can have cached and readied the WASM code for that DNA.
- Finally, Conductors MUST provide a way for an App to be installed without supplying membrane proofs and instantiating Cells, in cases where membrane proof values are dependent on the agent's public key which is generated at application installation time. This MUST be accompanied by a method of supplying those membrane proofs when they become available. (Note that this method of deferred instantiation is distinct from the deferred option for the preceding strategies in two ways: first, its purpose is to enable an instantiation process which requires information that isn't available until after installation rather than to enable lazy loading, and second, the Cells are instantiated but not active.)

```
struct AppManifestV1 {
    // User-facing name of the App. This may be used as the `installed_app_id`
    // in the Admin API.
    name: String,
    // User-facing description of the app.
    description: Option<String>,
    // The roles that need to be filled (by DNAs) for this app.
    roles: Vec<AppRoleManifest>,
    // If true, the app should be installed without needing to specify membrane
    // proofs. The app's cells will be in an incompletely instantiated state
    // until membrane proofs are supplied for each.
    membrane_proofs_deferred: bool,
}
struct AppRoleManifest {
    // The ID which will be used to refer to:
    // * this role,
    // * the DNA which fills it,
    // * and the cell(s) created from that DNA
```

```
name: RoleName,
    // Determines if, how, and when a Cell will be provisioned.
    provisioning: Option<CellProvisioning>,
    // The location of the DNA bundle resource, and options to modify it before
    // instantiating in a Cell.
    dna: AppRoleDnaManifest,
}
type RoleName = String;
enum CellProvisioning {
    // Always create a new Cell when installing this App.
    Create { deferred: bool },
    // Require that a Cell be already installed which matches the DNA
    // `installed_hash` spec, and which has an Agent that's associated with
    // this App's agent via DPKI. If no such Cell exists, *app installation MUST
    // fail*. The `protected` flag indicates that the Conductor SHOULD NOT allow
    // the dependency to be disabled or uninstalled until all cells using this
    // DNA are uninstalled.
    UseExisting { protected: bool },
    // Install or locate the DNA, but do not instantiate a Cell for it. Clones
    // may be instantiated later. This requires that `clone_limit` > 0.
    CloneOnly,
}
struct AppRoleDnaManifest {
    // Where to find this DNA.
    location: Option<Location>,
    // Optional default modifier values, which override those found in the DNA
    // manifest and may be overridden during installation.
    modifiers: DnaModifiersOpt<YamlProperties>,
    // The expected hash of the DNA's integrity manifest. If specified,
    // installation MUST fail if the hash does not match this. Also allows this
    // DNA to be targeted as a dependency in `AppRoleManifest`s that specify
    // `UseExisting` or `CreateIfNotExists` provisioning strategies.
    installed_hash: Option<DnaHashB64>,
    // Allow up to this many "clones" to be created at runtime.
    clone_limit: u32,
}
WebApp Bundle A WebAppBundle combines together a specific user interface together with an AppBundle as follows:
struct WebAppManifestV1 {
    // Name of the App. This may be used as the `installed_app_id`.
    name: String,
    // Web UI used for this app, packaged in a .zip file.
    ui: Location,
    // The AppBundle location.
    happ_manifest: Location,
}
```

A Holochain Conductor MUST provide access for user action through an Admin API to manage Apps and DNAs (install/uninstall, enable/disable, etc) and through an App API to make zome calls to specific DNAs in specific Apps, create cloned DNAs, supply deferred membrane proofs, and introspect the App. In our implementation, these API is defined as a library so that these calls can be made in-process, but they are also implemented over a WebSocket interface so they can be called by external processes.

In the WebSocket implementation of this API, requests and responses are wrapped in an "envelope" format that contains a nonce to match requests with response, then serialized and sent as WebSocket messages. The request message types are defined as variants of an AdminRequest or AppRequest enum, as are their corresponding responses (AdminResponse and AppResponse respectively). Hence, in the API definitions below, the enum name of the function name or return value type is implied.

Both response enums MUST define an Error(e) variant to communicate error conditions, where e is a variant of the enum:

```
enum ExternalApiWireError {
    // Any internal error.
    InternalError(String),
    // The input to the API failed to deserialize.
    Deserialization(String),
    // The DNA path provided was invalid.
    DnaReadError(String),
    // There was an error in the ribosome.
    RibosomeError(String),
    // Error activating app.
    ActivateApp(String),
    // The zome call is unauthorized.
    ZomeCallUnauthorized(String),
    // A countersigning session has failed.
    CountersigningSessionError(String),
}
```

*Admin API* Below is a list of the Admin API functions that MUST be implemented along with any details of function arguments and return values, as well as any contextual notes on functional constraints or other necessary implementation details.

For error conditions, the AppResponse::Error(e) variant MUST be used, where e is a variant of the ExternalApiWireError enum.

- AddAdminInterfaces(Vec<AdminInterfaceConfig>) -> AdminInterfacesAdded: Set up and register one or more new admin interfaces as specified by a list of configurations.
  - **– Arguments**: The AdminInterfaceConfig SHOULD be a generalized data structure to allow creation of an interface of whatever types are contextually appropriate for the system on which the conductor runs:

```
struct AdminInterfaceConfig {
    driver: InterfaceDriver,
}
enum InterfaceDriver {
    Websocket {
        port: u16,
        // The allowed values of the `Origin` HTTP header.
        allowed_origins: AllowedOrigins,
    }
}
enum AllowedOrigins {
    Any,
    Origins(HashSet<String>),
}
```

- RegisterDna(RegisterDnaPayload) -> DnaRegistered(DnaHash) : Install a DNA for later use in an App.
  - **– Notes**: This call MUST store the given DNA into the Holochain DNA database. This call exists separately from InstallApp to support the use case of adding a DNA into a conductor's DNA database once, such that the transpilation of WASM to machine code happens only once and gets cached in the conductor's WASM store.
  - **– Arguments**: A struct of the following type:

```
struct RegisterDnaPayload {
    // Override the DNA modifiers specified in the app and/or DNA bundle
    // manifest(s).
    modifiers: DnaModifiersOpt<YamlProperties>,
    source: DnaSource,
}
enum DnaSource {
    Path(PathBuf),
    Bundle(DnaBundle),
    // Register the DNA from an existing DNA registered via a prior
    // `RegisterDna` call or an `InstallApp` call.
    Hash(DnaHash),
}
```

- **– Return value**: If the DNA cannot be located at the specified path, AdminResponse::Error(ExternalApiWireError::DnaReadError(s)) MUST be returned, where s is an error message to be used for troubleshooting.
- GetDnaDefinition(DnaHash) -> DnaDefinitionReturned(DnaHash): Get the definition of a DNA.
  - **– Return Value**: This function MUST return all of the data that specifies a DNA as installed as follows:

```
struct DnaDef {
    name: String,
    modifiers: DnaModifiers,
    integrity_zomes: Vec<ZomeName>,
    coordinator_zomes: Vec<ZomeName>,
    lineage: HashSet<DnaHash>,
}
```

- UpdateCoordinators(UpdateCoordinatorsPayload) -> CoordinatorsUpdated: Update coordinator zomes for an already installed DNA.
  - **– Notes**: This call MUST replace any installed coordinator zomes with the same zome name. If the zome name doesn't exist then the coordinator zome MUST be appended to the current list of coordinator zomes.
  - **– Arguments**: A struct defined as:

```
struct UpdateCoordinatorsPayload {
    dna_hash: DnaHash,
    source: CoordinatorSource,
}
enum CoordinatorSource {
    // Load coordinators from a bundle file.
    Path(PathBuf),
    Bundle(Bundle<Vec<ZomeManifest>>),
}
```

- InstallApp(InstallAppPayload) -> AppInstalled(AppInfo): Install an app using an AppBundle.
  - **– Notes**: An app is intended for use by one and only one Agent, and for that reason it takes an AgentPubKey and instantiates all the DNAs bound to that AgentPubKey as new Cells. The new app should not be enabled automatically after installation, and instead must explicitly be enabled by calling EnableApp.
  - **– Arguments**: InstallAppPayload is defined as:

```
struct InstallAppPayload {
      source: AppBundleSource,
      // The agent to use when creating Cells for this App.
      agent_key: AgentPubKey,
      // The unique identifier for an installed app in this conductor.
      // If not specified, it will be derived from the app name in the
      // bundle manifest.
      installed_app_id: Option<String>,
      // Optional proof-of-membrane-membership data for any cells that
      // require it, keyed by the `RoleName` specified in the app bundle
      // manifest.
      membrane_proofs: HashMap<RoleName, MembraneProof>,
      // Optional: overwrites all network seeds for all DNAs of Cells
      // created by this app. This does not affect cells provisioned by
      // the `UseExisting` strategy.
      network_seed: Option<Vec<u8>>,
      // If app installation fails due to genesis failure, normally the
      // app will be immediately uninstalled. When this flag is set, the
      // app is left installed with empty cells intact. This can be useful
      // for using `GraftRecordsOntoSourceChain` or diagnostics.
      ignore_genesis_failure: bool,
 }
– Return Value: The returned value MUST contain the AppInfo data structure (which is also retrievable
 after installation via the GetAppInfo API), and is defined as:
 struct AppInfo {
      installed_app_id: String,
      cell_info: HashMap<RoleName, Vec<CellInfo>>,
      status: AppInfoStatus,
 }
 enum CellInfo {
      // Cell provisioned at app installation as defined in the bundle.
      Provisioned(ProvisionedCell),
      // Cell created at runtime by cloning a DNA.
      Cloned(ClonedCell),
      // Potential cell with deferred installation as defined in the
      // bundle.
      Stem(StemCell),
 }
 struct ProvisionedCell {
      cell_id: CellId,
      dna_modifiers: DnaModifiers,
      name: String,
 }
 struct StemCell {
      // The hash of the DNA that this cell will be instantiated from.
      original_dna_hash: DnaHash,
      // The DNA modifiers that will be used when instantiating the cell.
      dna_modifiers: DnaModifiers,
      // An optional name to override the cell's bundle name when
```

```
// instantiating.
    name: Option<String>,
}
enum AppInfoStatus {
    // The app is paused due to a recoverable error. There is no way to
    // manually pause an app.
    Paused { reason: PausedAppReason },
    // The app is disabled, and may be restartable depending on the
    // reason.
    Disabled { reason: DisabledAppReason },
    Running,
    AwaitingMemproofs,
}
enum PausedAppReason {
    Error(String);
}
enum DisabledAppReason {
    // The app is freshly installed, and has not been started yet.
    NeverStarted,
    // The app is fully installed and deferred memproofs have been
    // provided by the UI, but the app has not been started yet.
    NotStartedAfterProvidingMemproofs,
    // The app has been disabled manually by the user via an admin
    // interface.
    User,
    // The app has been disabled due to an unrecoverable error.
    Error(String),
}
```

- UninstallApp { installed\_app\_id: InstalledAppId } -> AppUninstalled : Uninstall the app specified by the argument installed\_app\_id from the conductor.
  - **– Notes**: The app MUST be removed from the list of installed apps, and any cells which were referenced only by this app MUST be disabled and removed, clearing up any persisted data. Cells which are still referenced by other installed apps MUST NOT be removed.
- ListDnas -> DnasListed(Vec<DnaHash>) : List the hashes of all installed DNAs.
- GenerateAgentPubKey -> AgentPubKeyGenerated(AgentPubKey) : Generate a new Ed25519 key pair.
  - **– Notes**: This call MUST cause a new key pair to be added to the key store and return the public part of that key to the caller. This public key is intended to be used later when installing an App, as a Cell represents the agency of an agent within the space created by a DNA, and that agency comes from the power to sign data with a private key.
- ListCellIds -> CellIdsListed<Vec<CellId>>: List all the cell IDs in the conductor.
- ListApps { status\_filter: Option<AppStatusFilter> } -> AppsListed(Vec<AppInfo>): List the apps and their information that are installed in the conductor.
  - **– Notes**: If status\_filter is Some(\_), it MUST return only the apps with the specified status.
  - **– Arguments**: The value of status\_filter is defined as:

```
enum AppStatusFilter {
    // Filter on apps which are Enabled, which can include both Running
    // and Paused apps.
    Enabled,
    // Filter only on apps which are Disabled.
    Disabled,
    // Filter on apps which are currently Running (meaning they are also
```

```
// Enabled).
Running,
// Filter on apps which are Stopped, i.e. not Running. This includes
// apps in the Disabled status, as well as the Paused status.
Stopped,
// Filter only on Paused apps.
Paused,
```

- EnableApp { installed\_app\_id: InstalledAppId } -> AppEnabled { app: AppInfo, errors: Vec<(CellId, String)> }: Change the specified app from a disabled to an enabled state in the conductor.
  - **– Notes**: Once an app is enabled, zome functions of all the Cells associated with the App that have a Create or CreateIfNotExists provisioning strategy MUST immediately be callable. Previously enabled Applications MUST also be loaded and enabled automatically on any reboot of the conductor.
  - **– Return value**: If the attempt to enable the app was successful, AdminResponse::Error(ExternalApiWireError::ActivateApp(s)) MUST be returned, where s is an error message to be used for troubleshooting purposes.
- DisableApp { installed\_app\_id: InstalledAppId } -> AppDisabled: Changes the specified app from an enabled to a disabled state in the conductor.
  - **– Notes**: When an app is disabled, calls to zome functions of all the Cells associated with the App MUST fail, and the app MUST not be loaded on a reboot of the conductor. Note if cells are associated with more than one app, they MUST not be disabled unless all of the other apps using the same cells have also been disabled.
- AttachAppInterface { port: Option<u16>, allowed\_origins: AllowedOrigins, installed\_app\_id: Option<InstalledAppID> } -> AppInterfaceAttached { port: u16 }: Open up a new WebSocket interface for processing AppRequests.
  - **– Notes**: All active apps, or the app specified by installed\_app\_id, if active, MUST be callable via the attached app interface. If an app is specified, all other apps MUST NOT be callable via the attached app interface. If the allowed\_origins argument is not Any, the Conductor MUST reject any connection attempts supplying an HTTP Origin header value not in the list. Optionally a port parameter MAY be passed to this request. If it is None, a free port SHOULD be chosen by the conductor. The response MUST contain the port chosen by the conductor if None was passed.
  - **– Arguments**: The allowed\_origins field is a value of the type:

```
enum AllowedOrigins {
    Any,
    Origins(HashSet<String>),
}
```

}

- ListAppInterfaces -> AppInterfacesListed(Vec<AppInterfaceInfo>): List all the app interfaces currently attached with AttachAppInterface, which is a list of WebSocket ports that can process AppRequest()s.
  - **– Return value**: The app interface info is defined as:

```
struct AppInterfaceInfo {
    port: u16,
    allowed_origins: AllowedOrigins,
    installed_app_id: Option<InstalledAppId>,
}
```

- **Debugging and introspection dumps**: The following functions are for dumping data about the state of the Conductor. Implementations MAY implement these functions; there is no standard for what they return, other than that they SHOULD be self-describing JSON blobs of useful information that can be parsed by diagnostic tools.
  - **–** DumpState { cell\_id: CellId } -> StateDumped(String): Dump the state of the cell specified by the argument cell\_id, including its chain.

- **–** DumpConductorState -> ConductorStateDumped(String): Dump the configured state of the Conductor, including the in-memory representation and the persisted state, as JSON. State to include MAY include status of Applications and Cells, networking configuration, and app interfaces.
- **–** DumpFullState { cell\_id: CellId, dht\_ops\_cursor: Option<u64> } -> FullStateDumped(FullStateDump): Dump the full state of the specified Cell, including its chain, the list of known peers, and the contents of the DHT shard for which it has claimed authority.
  - ∗ **Notes**: The full state including the DHT shard can be quite large.
  - ∗ **Arguments**: The database cursor of the last-seen DHT operation row can be supplied in the dht\_ ops\_cursor field to dump only unseen state. If specified, the call MUST NOT return DHT operation data from this row and earlier.
  - ∗ **Return value**: Unlike other dump functions, this one has some explicit structure defined by Rust types, taking the form:

```
struct FullStateDump {
    // Information from the Kitsune networking layer about the
    // agent, the DHT space, and their known peers.
    peer_dump: P2pAgentsDump,
    // The cell's source chain.
    source_chain_dump: SourceChainDump,
    // The dump of the DHT shard for which the agent is responsible.
    integration_dump: FullIntegrationStateDump,
}
struct P2pAgentsDump {
    // Information about this agent's cell.
    this_agent_info: Option<AgentInfoDump>,
    // Information about this DNA itself at the level of Kitsune
    // networking.
    this_dna: Option<(DnaHash, KitsuneSpace)>,
    // Information about this agent at the level of Kitsune
    // networking.
    this_agent: Option<(AgentPubKey, KitsuneAgent)>,
    // Information about the agent's known peers.
    peers: Vec<AgentInfoDump>,
}
// Agent info dump with the agent, space, signed timestamp, and
// expiry of last self-announced info, printed in a pretty way.
struct AgentInfoDump {
    kitsune_agent: KitsuneAgent,
    kitsune_space: KitsuneSpace,
    dump: String,
}
struct SourceChainDump {
    records: Vec<SourceChainDumpRecord>,
    published_ops_count: usize,
}
struct SourceChainDumpRecord {
    signature: Signature,
    action_address: ActionHash,
    action: Action,
    entry: Option<Entry>,
}
struct FullIntegrationStateDump {
```

```
// Ops in validation limbo awaiting sys or app validation.
    validation_limbo: Vec<DhtOp>,
    // Ops waiting to be integrated.
    integration_limbo: Vec<DhtOp>,
    // Ops that are integrated. This includes rejected ops.
    integrated: Vec<DhtOp>,
    // Database row ID for the latest DhtOp that we have seen.
    // Useful for subsequent calls to `FullStateDump` to return only
    // what they haven't seen.
    dht_ops_cursor: u64,
}
```

- **–** DumpNetworkMetrics { dna\_hash: Option<DnaHash> } -> NetworkMetricsDumped(String): Dump the network metrics tracked by Kitsune.
  - ∗ **Arguments**: If the dna\_hash argument is supplied, the call MUST limit the metrics dumped to a single DNA hash space.
- **–** DumpNetworkStats -> NetworkStatsDumped(String): Dump network statistics from the back-end networking library. This library operates on a lower level than Kitsune and Holochain P2P, translating the P2P messages into protocol communications in a form appropriate for the physical layer. Our implementation currently includes a WebRTC library.
- AddAgentInfo { agent\_infos: Vec<AgentInfoSigned> } -> AgentInfoAdded: Add a list of agents to this conductor's peer store.
  - **– Notes**: Implementations MAY implement this function. It is intended as a way of shortcutting peer discovery and is useful for testing. It is also intended for use cases in which it is important for agent existence to be transmitted out-of-band.
- GetAgentInfo { dna\_hash: Option<DnaHash> } -> AgentInfoReturned(Vec<AgentInfoSigned>): Request information about the agents in this Conductor's peer store; that is, the peers that this Conductor knows about.
  - **– Notes**: Implementations MAY implement this function. It is useful for testing across networks. It is also intended for use cases in which it is important for peer info to be transmitted out-of-band.
  - **– Arguments**: If supplied, the dna\_hash argument MUST constrain the results to the peers of the specified DNA.
- GraftRecords { cell\_id: CellId, validate: bool, records: Vec<Record> } -> RecordsGrafted: "Graft" Records onto the source chain of the specified CellId.
  - **– Notes**: Implementations MAY implement this function. This admin call is provided for the purposes of restoring chains from backup. All records must be authored and signed by the same agent; if they are not, the call MUST fail. Caution must be exercised to avoid creating source chain forks, which will occur if the chains in the Conductor store and the new records supplied in this call diverge and have had their RegisterAgentActivity operations already published.
  - **– Arguments**:
    - ∗ If validate is true, then the records MUST be validated before insertion. If validate is false, then records MUST be inserted as-is.
    - ∗ Records provided are expected to form a valid chain segment (ascending sequence numbers and valid prev\_action references). If the first record contains a prev\_action which matches an existing record, then the new records MUST be "grafted" onto the existing chain at that point, and any other records following that point which do not match the new records MUST be discarded. See the note above about the risk of source chain forks when using this call.
    - ∗ If the DNA whose hash is referenced in the cell\_id argument is not already installed on this conductor, the call MUST fail.
- GrantZomeCallCapability(GrantZomeCallCapabilityPayload) -> ZomeCallCapabilityGranted: Attempt to store a capability grant on the source chain of the specified cell, so that a client may make zome calls to that cell.
  - **– Notes**: Callers SHOULD construct a grant that uses the strongest security compatible with the use case; if a client is able to construct and store an Ed25519 key pair and use it to sign zome call payloads, a grant

using CapAccess::Assigned with the client's public key SHOULD be favored.

**– Arguments**: The payload is defined as:

```
struct GrantZomeCallCapabilityPayload {
    // Cell for which to authorize the capability.
    cell_id: CellId,
    // Specifies the capability, consisting of zomes and functions to
    // allow signing for as well as access level, secret and assignees.
    cap_grant: ZomeCallCapGrant,
}
```

- DeleteCloneCell(DeleteCloneCellPayload) -> CloneCellDeleted: Delete a disabled cloned cell.
  - **– Notes**: The conductor MUST return an error if the specified cell cannot be disabled.
  - **– Arguments**: The payload is defined as: **struct** DeleteCloneCellPayload { app\_id: InstalledAppId, clone\_cell\_id: CloneCellID, }
- GetStorageInfo -> StorageInfoReturned(StorageInfo): Request storage space consumed by the Conductor.
  - **– Notes**: Implementations MAY implement this function to allow resource consumption to be displayed. If implemented, all runtime resources consumption MUST be reported.
  - **– Return Value**: Storage consumption info, defined as:

```
struct StorageInfo {
    blobs: Vec<StorageBlob>,
}
enum StorageBlob {
    Dna(DnaStorageInfo),
}
// All sizes are in bytes. Fields ending with `_on_disk` contain the
// actual file size, inclusive of allocated but empty space in the file.
// All other fields contain the space taken up by actual data.
struct DnaStorageInfo {
    // The size of the source chain data.
    authored_data_size: usize,
    authored_data_size_on_disk: usize,
    // The size of the DHT shard data for which all local cells are
    // authorities.
    dht_data_size: usize,
    dht_data_size_on_disk: usize,
    // The size of retrieved DHT data for which local cells are not
    // authorities.
    cache_data_size: usize,
    cache_data_size_on_disk: usize,
    // The ID of the app to which the above data applies.
    used_by: Vec<InstalledAppId>,
}
```

- IssueAppAuthenticationToken(IssueAppAuthenticationTokenPayload) -> AppAuthenticationTokenIssued(AppAuthenticationTokenIssued): Request an authentication token for use by a client that wishes to connect to the app WebSocket.
  - **– Notes**: Implementations MUST expect a client to supply a valid token in the initial HTTP request that establishes the WebSocket connection, and MUST reject connection attempts that do not supply a valid token. An invalid token is defined as either one that was never issued or one that is no longer usable. The latter happens in four different cases:

- ∗ The token had an expiry set and the expiry timeout hsa passed,
- ∗ The token was single-use and has been used once,
- ∗ The token was revoked,
- ∗ The conductor has been restarted since the token was issued (implementations MAY implement this case).

Implementations MUST bind the WebSocket connection to the app for which the token was issued, excluding the possibility of a client accessing the functionality, status, and data of an app other than the one the token is bound to. Implementations SHOULD NOT terminate an established WebSocket connection once the token has expired; the expiry is to be enforced at connection establishment time.

**– Arguments**: The payload is defined as:

```
struct IssueAppAuthenticationTokenPayload {
      // The app to bind the token to.
      installed_app_id: InstalledAppID,
      // MAY be set to a reasonable default such as 30 seconds if not
      // specified; MUST NOT expire if set to 0.
      expiry_seconds: u64,
      // MAY default to true.
      single_use: bool,
 }
– Return type: The payload is defined as:
 struct AppAuthenticationTokenIssued {
      token: Vec<u8>,
      expires_at: Option<Timestamp>,
 }
```

The generated token MUST be unguessable; that is, it MUST be sufficiently strong to thwart brute-force attempts and sufficiently random to thwart educated guesses.

- RevokeAppAuthenticationToken(AppAuthenticationToken) -> AppAuthenticationTokenRevoked: Revoke a previously issued app interface authentication token.
  - **– Notes**: Implementations MUST reject all WebSocket connection attempts using this token after the call has completed.
- GetCompatibleCells(DnaHash) -> CompatibleCellsReturned(BTreeSet<(InstalledAppId, BTreeSet<CellId>)>): Find installed cells which use a DNA that is forward-compatible with the given DNA hash, as defined in the contents of the lineage field in the DNA manifest.
  - **– Notes**: Implementations SHOULD search DNAs installed by all applications, as well as DNAs installed ad-hoc via RegisterDna.

*App API* An App interface MUST expose the following API for all the apps to which it is bound. However, it MUST also enforce the use of valid Origin headers and authentication tokens for each WebSocket connection establishment attempt, and MUST bind the connection to the app for which the token was issued.

As with the Admin API, the following are expressed as variants of an AppRequest enum and a corresponding AppResponse enum.

For error conditions, the AppResponse::Error(e) variant MUST be used, where e is a variant of the following enum:

```
enum ExternalApiWireError {
    // Any internal error.
    InternalError(String),
    // The input to the API failed to deserialize.
    Deserialization(String),
    // The DNA path provided was invalid.
    DnaReadError(String),
    // There was an error in the ribosome.
    RibosomeError(String),
    // Error activating app.
    ActivateApp(String),
```

```
// The zome call is unauthorized.
ZomeCallUnauthorized(String),
// A countersigning session has failed.
CountersigningSessionError(String),
```

}

- GetAppInfo -> AppInfoReturned(Option<AppInfo>): Get info about the app, including info about each cell instantiated by this app. See above for the definition of AppInfo.
- CallZome(ZomeCall) -> ZomeCalled(ExternIO): Call a zome function.
  - **– Notes**: Implementations MUST enforce a valid capability for the function being called. This means that if the function is covered by a transferrable or assigned grant, the secret MUST be provided and valid; and if the function is covered by an assigned grant, the provenance MUST be valid. Regardless of the grant's access type, implementations MUST enforce that the provided signature matches the provided provenance. Implementations also MUST prevent replay attacks by rejecting a call that supplies a nonce that has been seen before or an expiry timestamp that has passed. Finally, the provenance (source) of the call MUST match the signature.
  - **– Arguments**: The payload is defined as:

```
struct ZomeCall {
    // The ID of the cell containing the zome to be called.
    cell_id: CellId,
    // The zome containing the function to be called.
    zome_name: ZomeName,
    // The name of the zome function to call.
    fn_name: FunctionName,
    // The serialized data to pass as an argument to the zome function
    // call.
    payload: ExternIO,
    // The secret necessary for exercising a claim against the granted
    // capability, if the capability is `CapAccess::Transferable` or
    // `CapAccess::Assigned`.
    cap_secret: Option<CapSecret>,
    provenance: AgentPubKey,
    // The signature on a serialized `ZomeCallUnsigned` struct with the same field values as this struct instance, but without the `signature` field. See below.
    signature: Signature,
    nonce: Nonce256Bits,
    expires_at: Timestamp,
}
```

The payload property is a MsgPack-encoded data structure provided to the zome function. This structure MUST be matched against the parameter defined by the zome function, and the zome function MUST return a serialization error if it fails.

- **– Return Value**: The payload MUST be AppResponse::ZomeCalled containing a MsgPack serialization of the zome function's return value if successful, or AppResponse::Error containing one of the following errors:
  - ∗ For unauthorized zome calls, ExternalApiWireError::ZomeCallUnauthorized(s), where s is a message that describes why the call was unauthorized.
  - ∗ For zome calls that attempt to initiate, process, or commit a countersigned entry, ExternalApiWireError::CountersigningSessionError(s), where s is a message that describes the nature of the failure.
  - ∗ For all other errors, including errors returned by the zome function itself, ExternalApiWireError::InternalError(s), where s describes the nature of the error.
- CreateCloneCell(CreateCloneCellPayload) -> CloneCellCreated(ClonedCell): Clone a DNA, thus creating a new Cell.
  - **– Notes:** This call specifies a DNA to clone by its role\_id as specified in the app bundle manifest. The function MUST register a new DNA with a unique ID and the specified modifiers, create a new cell from this cloned DNA, and add the cell to the specified app. If at least one modifier is not distinct from the

original DNA, or the act of cloning would result in a clone with the same DNA hash as an existing cell in the app, the call MUST fail.

**– Arguments**: The payload is defined as:

```
struct CreateCloneCellPayload {
      // The DNA to clone, by role name.
      role_name: RoleName,
      // Modifiers to set for the new cell.
      // At least one of the modifiers must be set to obtain a distinct
      // hash for the clone cell's DNA.
      modifiers: DnaModifiersOpt<YamlProperties>,
      // Optionally set a proof of membership for the clone cell.
      membrane_proof: Option<MembraneProof>,
      // Optionally set a human-readable name for the DNA clone.
      name: Option<String>,
 }
– Return value: The payload is defined as:
 struct ClonedCell {
      cell_id: CellId,
      // A conductor-local clone identifier.
      clone_id: CloneId,
      original_dna_hash: DnaHash,
      // The DNA modifiers that were used to instantiate this clone cell.
      dna_modifiers: DnaModifiers,
      // The name the cell was instantiated with.
      name: String,
      // Whether or not the cell is running.
      enabled: bool,
 }
```

- DisableCloneCell(DisableCloneCellPayload) -> CloneCellDisabled: Disable a clone cell.
  - **– Notes:** When the clone cell exists, it is disabled, after which any zome calls made to the cell MUST fail and functions scheduled by the cell MUST be unscheduled. Additionally, any API calls that return AppInfo should show a disabled status for the given cell. If the cell doesn't exist or is already disabled, the call MUST be treated as a no-op. Deleting a cloned cell can only be done from the Admin API, and cells MUST be disabled before they can be deleted.
  - **– Arguments**: The payload is defined as: **struct** DisableCloneCellPayload { clone\_cell\_id: CloneCellId, }
- EnableCloneCell(EnableCloneCellPayload) -> CloneCellEnabled(ClonedCell): Enabled a clone cell that was previously disabled or not yet enabled.
  - **– Notes:** When the clone cell exists, it MUST be enabled, after which any zome calls made to the cell MUST be attempted. Additionally any API functions that return AppInfo should show an enabled status for the given cell. If the cell doesn't exist, the call MUST be treated as a no-op.
  - **– Arguments:** The payload is defined as: **struct** EnableCloneCellPayload { clone\_cell\_id: CloneCellId, }
- GetNetworkInfo(NetworkInfoRequestPayload) -> NetworkInfoReturned(Vec<NetworkInfo>): Get information about networking processes.
  - **– Arguments**: The payload is defined as: **struct** NetworkInfoRequestPayload { *// Get gossip info for these DNAs.*

```
// Implementations MUST restrict results to DNAs that are part of
      // the app.
      dnas: Vec<DnaHash>,
      // Timestamp in milliseconds since which received amount of bytes
      // from peers will be returned. Defaults to UNIX_EPOCH.
      last_time_queried: Option<Timestamp>,
 }
– Return value: The payload is defined as:
 struct NetworkInfo {
      fetch_pool_info: FetchPoolInfo,
      current_number_of_peers: u32,
      arc_size: f64,
      total_network_peers: u32,
      bytes_since_last_time_queried: u64,
      completed_rounds_since_last_time_queried: u32,
 }
 struct FetchPoolInfo {
      // Total number of bytes expected to be received through fetches.
      op_bytes_to_fetch: usize,
      // Total number of ops expected to be received through fetches.
      num_ops_to_fetch: usize,
 }
```

- ListWasmHostFunctions -> ListWasmHostFunctions(Vec<String>): List all the host functions supported by this conductor and callable by WASM guests.
- ProvideMembraneProofs(HashMap<RoleName, MembraneProof) -> Ok: Provide the deferred membrane proofs that the app is awaiting.
  - **– Arguments**: The input is supplied as a mapping of role names to the corresponding membrane proofs.
  - **– Return value**: Implementations MUST return AppResponse::Error with an informative message if the application is already enabled.
- EnableApp -> Ok: Enable an app which has been awaiting, and has received, deferred membrane proofs.
  - **– Notes**: If the app is awaiting deferred membrane proofs, implementations MUST NOT allow an app to be enabled until the membrane proofs has been provided.
  - **– Return value**: If this call is attempted on an already running app or an app that is still awaiting membrane proofs, implementations MUST return AppResponse::Error with an informative message.
