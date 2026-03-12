---
images: []
order: 12
title: 'Appendix A: Holochain Implementation Spec v0.3.0 Beta'
---

So far we have described the necessary components of a scalable coordination and collaboration system. We have built an "industrial strength" implementation of this pattern suitable for real-world deployment, under the name Holochain. Here we describe the technical implementation details that achieve the various requirements described above.

This specification assumes that the reader has understood context and background provided in the [Holochain](hwp_4_formal.md) [Formalization.](hwp_4_formal.md)

Given the formal description from that document of our local state model (Source Chain) and shared data model (Graph DHT) we can now present a high-level implementation specification of the different components of the Holochain architecture:

- App Virtual Machine (Ribosome)
- Workflows
- P2P Networking (Kitsune)
- The Conductor
- Secure Private Key Management (lair-keystore)

**Note on code fidelity**: The code in this appendix may diverge somewhat from the actual implementation, partially because the implementation may change and partially to make the intent of the following code clearer and simpler. For instance, specialized value types that are merely wrappers around a vector of bytes are frequently replaced with Vec<u8>.

### Ribosome: The Application "Virtual Machine"

We use the term **Ribosome** to the name of part of the Holochain system that runs the DNA's application code. Abstractly, a Ribosome could be built for any programming language as long as it's possible to deterministically hash and run the code of the DNA's Integrity Zome such that all agents who possess the same hash can rely on the validation routines and structure described by that Integrity Zome operating identically for all. (In our implementation we use WebAssembly (WASM) for DNA code, and Wasmer[23](#page-30-0) as the runtime that executes it.)

The Ribosome, as an application host, must expose a minimal set of functions to guest applications to allow them to access Holochain functionality, and it should expect that guest applications implement a minimal set of callbacks that allow the guest to define its entry types, link types, validation functions, and lifecycle hooks for both Integrity and Coordinator Zomes. We will call this set of provisions and expectations the Ribosome Host API.

Additionally, it is advantageous to provide software development kits (SDKs) to facilitate the rapid development of Integrity and Coordinator Zomes that consume the Ribosome's host functions and provide the callbacks it expects.

In our implementation we provide SDKs for Integrity and Coordinator Zomes written in the Rust programming language[24](#page-30-1) as Rust crates: the Holochain Deterministic Integrity (HDI) crate[25](#page-30-2) facilitates the development of Integrity Zomes, while the Holochain Development Kit (HDK) crate[26](#page-30-3) facilitates the development of Coordinator Zomes.
