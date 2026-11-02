# Public delivery ledger — plan: docs/superpowers/plans/2026-11-01-newsflow-public.md

2026-11-01: user chose public access and free GitHub Pages news-site scope, then requested continuation. Existing temporary local server no longer listened on 8510; OS did not reboot and no application exception was recorded. Do not attribute termination to a proven application crash.

Pre-flight: snapshot JSON is consumed by PublicBackend; PublicBackend feeds the existing NewsController. Public bootstrap toggles only delivery-specific UI. Site output is separate from complete source and never includes personal runtime.

Ruling: user approved the small public news-reader delivery mode in chat; preserve native execution and existing local functionality. Extra design/plan records support review, without reopening already answered choices.

Ruling: user explicitly requested a new source repository; initialize fresh history from inspected deliverable files after verification, rather than pushing mixed existing Git history. Keep the source checkout unchanged by Git operations.

Task 1: complete — builder uses real local models, prior public data, temporary SQLite, safe public assets and relative paths. Python builder regressions verified.
Task 2: complete — isolated browser bookmarks/corrections, combined filters, safe CSV, cache and response-order handling. Edge desktop and mobile interactions passed.
Design checker failed twice due to provider token rate limits; no design review is claimed. One fresh independent final reviewer completed the whole-change review.
Final: fixed prior JSON size limit — a separate bounded 8 MiB snapshot budget supports 1,000 explained articles; RSS remains at 1 MiB. Regression failed before fix.
Final: fixed long RSS title contract — retain up to 500 characters for reading, classify the first 200 consistently, and retain these articles on source failure. Python and Node regressions failed before fix.
Final: fixed first-time offline retry — reset disabled refresh button even without a snapshot. Node regression failed before fix.
Additional fixes: public navigation no longer binds body click events (failing then passing mobile Edge flow); corrupt prior rows/sources/count no longer abort fresh refresh (three reproducing Python failures then green).
Final local verification: Python 91 passed (existing pytz warning); Node 39 passed; syntax and diff checks passed. Five real public sources produced 154 articles in the latest local build.
Task 3: in progress — 136 inspected files exported with copy hashes verified, no credential pattern hits, and no original Git history. GitHub workflow scope requires interactive authorization before source push/deploy.
Source publication: GitHub rejected the initial push because the OAuth App lacks workflow scope. The unpushed initial commit was amended to exclude the workflow, which remains intact locally. Verified application source was then pushed successfully to ma-jamess/newsflow, main commit 0fc4161350d146c8a6cfb60a42381801cff8e4e0. Pages is configured for workflow publication with enforced HTTPS, but no public deployment exists yet.
Pending: gh auth refresh interactive session awaits the owner; after authorization, restore workflow to Git tracking, remove temporary pending-deployment notices, push, wait for successful Actions deployment and verify real public desktop/mobile news data. Local static preview remains available until deployment succeeds.

2026-11-02: owner completed the device authorization. GitHub API confirms repo and workflow scopes. The original verified workflow is restored for publication; preparing the first GitHub Actions deployment and public HTTPS verification.

First cloud deployment: implementation commit 3cc4df2a665e5eb490cad4c87f91d4a921cd452c, successful run https://github.com/ma-jamess/newsflow/actions/runs/41400301372. GitHub Ubuntu/Python 3.13 installed the pinned dependencies, built classified news and deployed Pages successfully.
Public proof: https://ma-jamess.github.io/newsflow/ and data/news.json returned HTTPS 200; 284 retained articles, 273 within the default 72-hour view, five sources updated successfully and no personal flags. Edge desktop search/bookmark/correction reload/export/report/refresh passed without page errors or local API requests. Mobile 390x844 details/source settings and overflow checks passed. Separate clean-browser and cached-browser network failures retained cached news and allowed manual retry.
Fresh exported-source suites: Python 91 passed (one existing pytz warning); Node 39 passed. Public documentation now reports the verified live site, and a clean current public snapshot is retained for source-download startup.
Task 3: complete — the inspected source and workflow are published in the new repository, Pages deployed successfully, and real public HTTPS/browser/failure checks passed. Final documentation and source archive are refreshed together; the original mixed source checkout and its Git history are preserved.
