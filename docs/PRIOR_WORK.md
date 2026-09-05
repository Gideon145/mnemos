# Prior Work Declaration

Mnemos is an original build by The Muses for the Sibyl Labs Hackathon.

- **Core implementation:** written from scratch during the build window.
- **Memory layer:** Sibyl Memory (organizer-provided infrastructure).
- **Blockchain/payment primitives:** Base + x402 standards, used per their
  public documentation and SDKs.
- **Agent runtime:** Virtuals Protocol, used per its public documentation.

No third-party application codebase was copied or forked. Standard open-source
libraries used are declared in dependency manifests, each under its own license.

## Research context for `revise`

The revision primitive (correct a fact, then taint and gate everything that
depended on it) was designed against published research. The closest academic
work found is:

- Dong et al., "From Faulty Memories to Corrected Actions: Dependency-Guided
  Rollback" (arXiv:2608.10502, Aug 2026). It builds a typed memory-to-action
  graph from runtime provenance and selectively replays answer-relevant
  computation after a memory fault. It is a *post-failure computation
  recovery* technique for benchmarks; it does not govern future actions, has
  no suspect/reconsideration state, and ships no product.

No shipped product implementing correction -> dependency walk -> execution
gating was found. Mnemos implements that loop natively on the Sibyl journal:
the dependency walk reads only the journal and entity links already recorded,
and the payment gate is the deterministic enforcement point. All code is
original; the paper influenced the problem framing, not the implementation.

— The Muses, Sep 2026
