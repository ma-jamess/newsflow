# Source expansion ledger — plan: docs/superpowers/plans/2026-11-02-free-news-sources.md

2026-11-02: user requested adding free sources and confirmed Chinese-first with international Chinese news. First protected local audit examined 67 candidates; 21 returned recent Chinese items. Several international official feeds timed out locally, so GitHub-network evidence is required before selection.

Pre-flight: feed catalogue -> NewsStore -> publication snapshot -> PublicBackend. Existing 20-source client/restoration bounds must be expanded together. Existing personal preferences are keyed by stable source ID and must not be reset.

Ruling: this is an expansion of the already authorized public reader; retain delivery/model architecture and use the existing clean source-export repository on a feature branch. The original mixed local repository and personal runtime remain untouched.
