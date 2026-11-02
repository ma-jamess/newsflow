# Source expansion ledger — plan: docs/superpowers/plans/2026-11-02-free-news-sources.md

2026-11-02: user requested adding free sources and confirmed Chinese-first with international Chinese news. First protected local audit examined 67 candidates; 21 returned recent Chinese items. Several international official feeds timed out locally, so GitHub-network evidence is required before selection.

Pre-flight: feed catalogue -> NewsStore -> publication snapshot -> PublicBackend. Existing 20-source client/restoration bounds must be expanded together. Existing personal preferences are keyed by stable source ID and must not be reset.

Ruling: this is an expansion of the already authorized public reader; retain delivery/model architecture and use the existing clean source-export repository on a feature branch. The original mixed local repository and personal runtime remain untouched.

Task 1: complete — protected audit tests observed RED then GREEN; GitHub audit run 41405334588 checked 91 candidates, found 43 recent Chinese feeds and three with unknown publication time. Forty-five candidates failed. Collapse cnBeta duplicate addresses and BBC simplified/traditional alternatives to select 44 channels; preserve all six original source IDs. Dated report: docs/source-audit-2026-11-02.json. Manual check-sources.yml has contents/read only and no Pages deployment job.

Task 2 RED: catalogue module missing (six cases), more than 20 prior sources lost a late source's last_success_at, expanded browser data was rejected, and 1,200 high-volume articles excluded a quiet source's recent article. Existing oversized-source protection was already passing and was retained.

Task 2 implementation: validate an editable 1–128 source catalogue without resolving DNS at import; real fetches retain numeric public-address checks, bounded redirects, three workers and 1 MiB RSS limit. Restore up to 128 previous source timestamps. When there are more than 1,000 articles, query each source's latest rows first, reserve up to ten per source (reduced to fit capacity), then fill by global recency. This avoids truncating a quiet source before reservation and retains the 1,000 output cap.

Task 2: complete — focused Python 23/23 and Node 10/10 passed. Full python -m pytest -q: 102 passed (one upstream pytz deprecation warning); full Node suite: 41 passed. Python/JS syntax and git diff --check passed. Local real-feed build: 44 channels, 931 rows, 2,305,661 bytes, partial status with 18 source network errors; cloud audit, rather than local connectivity, controls international source selection. Edge desktop/mobile: all 44 choices, filtering a source beyond position 20 (机核, 20 visible rows), final-source toggle round trip and no page/dialog horizontal overflow or JS errors.

Publication checkpoint: in a separate persistent Edge test profile, bookmarked and corrected an article from the five-source production site, hid IT之家, then reloaded and verified the baseline state. That profile is reserved for testing continuity across the upcoming deployment; the user's live browser profile is not edited.

Pages workflow: restored exactly to main after the temporary feature-branch cloud audit. Final whole-change review and public deployment pending.

Final review: one fresh reviewer on 014f792..42408aa identified two Important findings: the enabled Sina finance feed was a 2008 archive, and a stale-plus-undated feed could be incorrectly marked current. No Critical, Minor or declined findings. Both grades stand because they affect the recent-news admission requirement.

Final: fixed historical archive admission — exclude the known Sina feed from the catalogue and reject undated articles with an explicitly old date folder in their URL, both during live ingestion and previous-snapshot restoration. The URL is used only as evidence for exclusion; published_at is never inferred or filled. Two publication regressions and the real Sina audit regression observed RED→GREEN. A real follow-up read classified all 40 Sina items as archival/old, available=false; record docs/source-audit-sina-2026-11-02.json.

Final: fixed mixed-date admission — count actually recent dated items separately from undated items. Only a dated item inside the allowed window can produce current; dated feeds with no recent dated item are old, while wholly undated feeds without archival evidence remain unknown_time. Two mixed-date regression cases observed RED→GREEN. Final suite: Python 107/107, Node 41/41; syntax and diff checks passed. No second review requested, as the execution plan requires one fix pass verified by regressions and the green suite.

Final selection: 43 channels; initial 46 readable feeds minus two duplicate alternatives and the confirmed archive. Preserve the original audit as historical evidence and record the final decision in docs/source-selection-2026-11-02.json. Actual rebuilt local snapshot: 920 rows, 2,315,043 bytes, 43 sources, zero /20080612/ articles. Edge desktop/mobile recheck: all 43 source choices, 20 filtered 机核 rows, final-source toggles, no horizontal overflow or JS errors. Publication and production continuity checks remain pending.
