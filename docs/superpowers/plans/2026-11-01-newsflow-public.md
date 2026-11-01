# NewsFlow Public Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Continue native execution already used by this project; user approved the free public news-site scope and requested continuation.

**Goal:** Deliver a working free HTTPS NewsFlow news site and a new public GitHub source repository.
**Architecture:** Python builds sanitized classified snapshots, a browser adapter reuses the news controller with individual local storage, and pinned GitHub Actions publish to Pages.
**Tech Stack:** Existing Python/scikit-learn, native JS/CSS/HTML, GitHub Actions/Pages, Node tests, Microsoft Edge.
**Spec:** docs/superpowers/specs/2026-11-01-newsflow-public-design.md

## Global Constraints

- No read/copy/publish of runtime/deepseek.env, credentials, personal databases or old Git history.
- Schedule every 5 minutes with honest best-effort wording; browser checks every 20 seconds.
- Reuse existing local models and source safety/limits; public reader storage is per browser.
- Preserve existing full local graduation project; only inspected source files enter the new repository.

## Review Focus

- Failed fetches cannot erase existing news or pretend data is fresh.
- Old bookmarks/corrections must survive new deployments and disabled source views.
- Storage/network failure must remain usable and cannot falsely confirm writes.
- Public mode must not call localhost, paid APIs or shared mutation endpoints.
- Project-path deployment, CSP, mobile overlays and Actions permissions must work.

### Task 1: Static snapshot builder and delivery artifact

Files: newsroom/public_site.py, scripts/build_public_site.py, tests/test_public_site.py, web/public/index.html.
Interfaces: build_snapshot(classifier, fetcher, previous, now) -> dict; write_site(output, snapshot, report, repository) -> Path. Input prior snapshots are sanitized and restored into temporary SQLite; output is schema version 1 with rows, sources, update and build timestamps.

- [ ] Write/run failing tests for real model snapshot, prior news retention, total failure fallback, invalid prior source/link rejection, no personal fields and artifact whitelist.
- [ ] Implement builder with temporary databases, precomputed model explanations and atomic data writes; add CLI and clean public seed.
- [ ] Run focused/full Python checks; verify actual current RSS data.

### Task 2: Public reader backend and UI

Files: web/public-backend.js, web/public-app.js, web/public.css, web/live-news.js, tests/public-backend.test.cjs.
Interfaces: PublicBackend({fetch,storage,clock}).request(path,payload?) -> Promise<object>; exportCSV(filters) -> string; initialize from same-origin JSON. Public shell defines state/bootstrap/api/download/navigate/toast before mounting the existing news controller.

- [ ] Write/run failing tests for filter intersection, isolated persisted bookmarks/corrections, newer snapshot merge, safe export, offline fallback, unavailable storage and stale response exclusion.
- [ ] Implement adapter and public shell; public source toggles only affect individual display, detail quick-action becomes full source download, status reports 5-minute scheduling/cache truthfully.
- [ ] Run all Python/Node/syntax checks; verify static site in Edge desktop/mobile with bookmarking reload, correction, CSV and report page.

### Task 3: Safe publication and real deployment

Files: .github/workflows/pages.yml, README.md, README_EN.md, docs/public-site-guide.md, packaging exclusions, verification report.

- [ ] Write pinned workflow with build/read and deploy/pages permissions, schedule/push/manual triggers and deployment concurrency; preserve latest usable data on source failures.
- [ ] One independent final review, fix material findings with regressions and green suites.
- [ ] Export only allowed release files to a new local repository, scan exclusions/content before initial commit; create ma-jamess/newsflow publicly and push main after local verification.
- [ ] Configure Pages, wait for real deploy success, verify public site in Edge and HTTPS API reads; record exact URLs, commit and evidence.
