# Free news source expansion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Continue the existing native execution and one fresh final whole-change review.

**Goal:** Expand the deployed Chinese news reader with every usable free feed found in this research pass, including international Chinese news, while keeping Pages stable.
**Architecture:** Retain the existing protected RSS/Atom fetcher, temporary publication database, local model and per-browser preferences. Store verified built-in feeds in an editable catalogue; audit candidates on the actual GitHub execution network before enabling them.
**Tech Stack:** Python, native JS, existing scikit-learn models, GitHub Actions/Pages, Edge.
**Spec:** Existing public delivery design at docs/superpowers/specs/2026-11-01-newsflow-public-design.md and the user's explicit request to add free sources, followed by confirmed Chinese-first/international-Chinese preference.

## Global constraints

- No paid keys, login scraping, personal runtime, credentials or personal databases. No paid AI calls.
- Admit only public HTTPS RSS/Atom that returns actual Chinese items; record inaccessible and old candidates rather than claiming they were connected.
- Keep source failures isolated, the latest usable deployment intact, prior source timestamps and individual browser preferences/bookmarks/corrections preserved.
- Retain the five-category classifier, 1 MiB feed bound, 1,000 published rows, 8 MiB previous-public-JSON budget, three simultaneous feed tasks and five-minute best-effort schedule.
- Expand the bounded public-source validation/restoration capacity from 20 to 128.
- Preserve the original mixed local graduation repository. Use a feature branch in the separate clean newsflow repository; publish only after checks/review.

## Review focus

- A newly added source beyond position 20 must not reject the whole website or lose its old successful state on failure.
- Invalid/old feeds and unknown publication dates must not be reported as fresh news.
- Existing source visibility preferences and saved snapshots must survive an enlarged catalogue.
- Audit data and source files must never contain credentials or private endpoints.
- The cloud audit must have no Pages deployment side effect; restore the normal publication workflow before main integration.

### Task 1: Audit free feeds on the actual cloud network

- [x] Add/test a small protected RSS auditor using real parser and injected test fetches; emit bounded metadata and exclude old/non-Chinese/invalid feeds.
- [x] Research direct official/public feed URLs and audit candidates locally and on GitHub, with no publishing step.
- [x] Save a dated audit report and select the successfully read recent Chinese feeds; retain existing IDs.

### Task 2: Catalogue and public reader capacity

- [x] Add failing tests for expanded built-ins, sources beyond 20, cache retention and enlarged catalogue preserving personal preferences.
- [x] Move built-ins to an editable validated catalogue and extend source count guards/restoration to 128.
- [x] Run full Python/Node/syntax checks and build with actual public data; verify desktop/mobile source filtering in Edge.

### Task 3: Review and publication

- [ ] One fresh independent final review, material fixes with regressions and green suite.
- [ ] Restore publication workflow, publish the verified catalogue, wait for successful Pages deployment and verify public source count, current data and persistent personal state.
- [ ] Record connected feeds, publishers, failed candidates and dates; refresh source package and local documentation.
