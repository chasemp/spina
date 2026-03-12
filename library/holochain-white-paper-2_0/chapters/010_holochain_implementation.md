---
images: []
order: 10
title: Holochain Implementation
---

Given the above formal description of our local state model (Source Chain) and shared data model (Graph DHT) we can now present a high-level implementation specification of different components of the Holochain architecture. The components include:

- App Virtual Machine (Ribosome)
- State Management (Workflows)
- P2P Networking (Kitsune and Holochain P2P)
- Application Interface (Conductor API)
- Secure Private Key Management (lair-keystore)

Please see the [Implementation](hwp_A_implementation_spec.md) Spec (Appendix A) for details.
