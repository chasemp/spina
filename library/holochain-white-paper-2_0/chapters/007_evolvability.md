---
images: []
order: 7
title: Evolvability
---

For large-scale systems to work well over time, we contend that specific architectural elements and affordances make a significant difference in their capacity to evolve while maintaining overall coherence as they do so:

1. **Subsidiarity:** From the Wikipedia definition:

Subsidiarity is a principle of social organization that holds that social and political issues should be dealt with at the most immediate (or local) level that is consistent with their resolution.

Subsidiarity enhances evolvability because it insulates the whole system from too much change, while simultaneously allowing change where it is needed.

<span id="page-13-1"></span><sup>17</sup> See [https://github.com/holochain/deepkey/blob/main/docs/2023/README.md.](https://github.com/holochain/deepkey/blob/main/docs/2023/README.md)

Architecturally, however, subsidiarity is not easy to implement because it is rarely immediately obvious what level of any system is consistent with an issue's resolution.

In Holochain, the principle of subsidiarity is embodied in many ways, but crucially in the architecture of app instances having fully separate DNAs running on their own separate networks, each also having clear and differentiable Integrity and Coordination specifications. This creates very clear loci of change, both at the level of when the integrity rules of a DNA need to change, and at the level of how one interacts with a DNA. This allows applications to evolve exactly in the necessary area by updating only the DNA and DNA portion necessary for changing the specific functionality that needs evolving.

2. **Grammatic**[18](#page-14-1) **composability:** Highly evolvable systems are built of grammatic elements that compose well with each other both "horizontally", which is the building of a vocabulary that fills out a given grammar, and "vertically" which is the creation of new grammars out of expressions of a lower level grammar. There is much more that can be said about grammatics and evolvability, but that is out of scope for this paper. However, we contend that the system as described above lives up to these criteria of having powerful grammatical elements that compose well as described. DNAs are essentially API definitions that can be used to create a large array of micro-services that can be assembled into small applications. Applications themselves can be assembled at the User Interface level. A number of frameworks in the Holochain ecosystem are already building off of this deep capacity for evolvability that is built into the system's architecture[19](#page-14-2) .
