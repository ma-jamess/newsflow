# SDD ledger — plan: docs/superpowers/plans/2026-10-31-newsflow-live.md

Spec: docs/superpowers/specs/2026-10-31-newsflow-live-design.md

Baseline: Python 47 passed (one existing pytz deprecation warning), Node 15 passed. Original 1.3 working files snapshotted before editing; local algorithms, training data and reports are the baseline.

Pre-flight: Task 1 produces NewsStore and LiveNewsService consumed by Task 2; Task 2 exposes news routes and assets consumed by Task 3 delivery. Types and paths agree. No paid model calls belong to the refresh path.

Ruling: Native worktree tool rejects the source outside attached workspace roots; use a full pre-edit source snapshot and the existing feature branch. Cost: changes share the source checkout, so only scoped files are edited and the snapshot is retained for recovery.

User authorized redesign and current-news integration; architecture remains Python/native web. This is a small local tool, with practical browsing first and experimental evaluation in its own page.

Task 1: complete. RSS/Atom, public URL validation, deduplication, bookmark/correction persistence, source freshness, injected feed + actual local model, partial failure, cooldown and lifecycle tests observed RED→GREEN; focused 17/17, full Python 64/64 at that gate.

Task 2: complete; the initial integration gate follows, with final-review fixes recorded below. HTTP routes and frontend helpers observed RED→GREEN, then 5 request-order/pagination/write-failure controller tests RED→GREEN. Full Python 71/71, Node 25/25; JavaScript syntax checks passed. Edge desktop 1440×1000 and mobile 390×844 flows passed: detail, original link, five probability bars, bookmark/reload, human category, CSV, transfer without paid submission, local single/batch, experiments/history/method/help, combined search/source/category, empty state, source toggles/custom public source, private source rejection, mobile overlay/close and no document overflow. Browser work uses CLI (the Edge connector is unavailable) and an independent QA cache; the personal runtime is untouched by test mutations.

Ruling: Preserve the existing uncommitted 1.3 edits and leave this task's checkout changes reviewable without creating mixed-scope commits. Complete source snapshots, the manifest and verification ledger retain the recovery record. Cost: task steps are recorded by files and evidence instead of individual Git commits.

Task 3: initial delivery checkpoint (subsequently completed below). New source archive identity and private/cache/QA exclusions observed RED→GREEN (2/2 packaging checks). MIT, English quickstart, news guide and revised main README saved. Whole-change review and independent archive extraction remain.

Pre-review robustness: four backend regressions observed RED→GREEN for numeric-IP connection pinning, DNS rebinding after URL validation, statistics beyond 5000 rows, and stop during manual-thread creation. Human pending-review wording observed RED→GREEN. Full suite now Python 76/76 (one existing pytz warning), Node 26/26; all JavaScript syntax and git whitespace checks passed. Five sources re-probed using the final direct HTTPS transport on 2026-10-31 18:19 Asia/Shanghai; all returned recent items. Restarted the task-owned runtime with final modules; personal cache stayed intact and the default view showed 146 current articles.

Final review: independent reviewer /root/newsflow_final_review completed one whole-change review. Critical: none. Important: stale pre-mutation article details and stale initial source reads. Four regressions observed RED→GREEN; successful bookmark/category writes invalidate and refetch details, source reads use generations and pending-write guards. No second reviewer is dispatched; regression evidence and the green suite verify this final fix pass.

Final: fixed stale detail overwrite after bookmark/category save — two news-controller regressions RED→GREEN; fixed stale source GET overwrite after toggle/add — two news-sources-controls regressions RED→GREEN. Desktop and mobile Edge flows passed again after these fixes.

Final gate: the full Python run exposed an intermittent WinError 10053 on unauthorized POST. Diagnosis reproduced reset/abort in 5 of 30 larger rejected bodies, while authorized bodies succeeded. Consuming the body before the original rejection yielded 50/50 complete HTTP 403 responses. Three bounded 1 MiB integration cases (bad token, other Origin, bad media type) observed RED→GREEN; JSON parsing and mutations remain after authentication. Final full suite: Python 79/79 in 21.40 seconds (existing pytz warning), Node 30/30; syntax and whitespace checks passed.

Final: minor (deferred): fullTime omits the year for old bookmarks/source dates; complete timestamps and sorting are retained.

Final: Ruling: existing DeepSeek implementation/model choice remains prior 1.3 scope — users still explicitly submit a single title and auto news never uses the provider — cost if wrong: provider compatibility needs separate maintenance, not hidden automatic spend.

Final: Ruling: current-news accuracy/out-of-domain evaluation is separate research — historical test metrics stay labeled as historical, current news permits human correction — cost if wrong: new-topic misclassification; no current accuracy claim is made.

Final: Ruling: multi-user hosting authorization is outside this personal tool release — each recipient runs an independent loopback instance, as documented — cost if wrong: converting it into a shared website requires account and authorization design.

Final: Ruling: pytest collection is restricted to tests/ through pytest.ini — independent archive extraction otherwise duplicates tests under QA — cost if wrong: any future official tests must live under tests/ or update testpaths.

Review record: docs/newsflow-code-review.md. Release content passed archive CRC, all 121 inventory hashes and private-file/credential-pattern exclusions. Its independently extracted environment passed setup-only, loaded its own modules/models, refreshed all five default sources, classified an education headline locally, rejected a 1 MiB unauthorized POST with complete JSON, and rendered the news/detail page in Edge without page errors or overflow.

Task 2: final completion — all material review findings fixed and desktop/mobile Edge flows passed.

Task 3: complete — MIT source, models/data/notices/tests, 79 Python + 30 Node checks, independent extraction/startup/UI verified. Final serialization includes this record and the latest preview; the release checksum/integrity report is generated beside the ZIP after serialization.

Final: Ruling: no merge or GitHub publication was requested for this local-tool delivery — retain the existing feature branch and uncommitted changes, and distribute the reviewed source package — cost if wrong: GitHub publication remains an explicit follow-up action.
