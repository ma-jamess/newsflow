# ECS Fixed Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. One fresh-context final whole-change review; do not repeat completed source expansion work.

**Goal:** Deploy the existing news reader at a fixed ECS URL and keep updates independent of the user's computer.

**Architecture:** Reuse static public assets and the protected RSS/local-model publisher. A resource-limited systemd oneshot timer atomically updates public JSON while existing Nginx serves `/newsflow/` alongside ThinkFlow.

**Tech Stack:** Python 3.12/3.13, native JavaScript, Ubuntu 24.04, Nginx 1.24, systemd 255, Edge.

**Spec:** `docs/superpowers/specs/2026-11-02-newsflow-ecs-design.md`

## Global Constraints

- Fixed initial URL `http://47.115.130.110/newsflow/`; prefer trusted `https://47.115.130.110/newsflow/` once the officially supported shortlived IP certificate is issued and automated renewal is enabled. No domain is required for this certificate.
- Code `/opt/newsflow`; public assets `/var/lib/newsflow/site`; only public data enters deployment and GitHub.
- Reuse existing verified SSH host key and locally retained connection settings; never copy credentials into this repository.
- Preserve ThinkFlow, its root URL, accounts, data, services and tunnel. Back up Nginx and validate before graceful reload.
- Timer runs 120 seconds after the prior run finishes; CPUQuota=100%, MemoryMax=700M, dedicated non-root user.
- Retain 43 channels, 1,000 articles, 128-source bound, seven-day cache and existing fetch protection. No paid AI.
- Pages defaults remain 300 seconds and old browser snapshots remain compatible. Browser preferences remain per origin.

## Review Focus

- Publisher or disk failure must leave the prior news JSON readable and byte-for-byte intact.
- Scheduled refresh must never rewrite live HTML, scripts or styles.
- Invalid or oversized prior JSON must fall back safely; metadata must not claim the wrong interval.
- The `/newsflow/` alias and slash redirect must serve relative assets correctly without intercepting ThinkFlow.
- Systemd permissions/resource limits must allow real model and feed work without exposing secrets or restarting unrelated services.

### Task 1: ECS publication and deployment assets

**Files:** Create `newsroom/ecs_site.py`, `scripts/update_ecs_site.py`, `deploy/ecs/newsflow-update.service`, `deploy/ecs/newsflow-update.timer`, `deploy/ecs/nginx-newsflow-location.conf`; modify `newsroom/public_site.py`, `web/public/index.html`, `web/public-backend.js`, `web/live-news-ui.js`, `web/live-news.js`; test `tests/test_ecs_site.py`, `tests/public-backend.test.cjs`, `tests/public-updates.test.cjs`.

**Interfaces:** `bootstrap_site(output, classifier, *, seed_path, repository, interval_seconds=120)` initializes public assets. `refresh_site(output, classifier, *, seed_path, repository, interval_seconds=120, fetcher=fetch_feed, now=None)` builds first, then atomically replaces only news JSON. Both consume existing public snapshots and local classifier. `write_site(..., deployment='pages', interval_seconds=300)` supplies compatible publication metadata. `LiveNewsUI.updateSchedule(snapshot)` derives timing copy.

- [x] Write Python regressions for ECS metadata/HTML timing, genuine update with prior cache, classifier failure preserving files, atomic replacement failure preserving files, oversized/corrupt previous fallback and refresh preserving every static asset.
- [x] Write Node regressions for 120-second ECS metadata reaching news/sources/refresh, old metadata defaulting to Pages, invalid intervals and schedule rendering.
- [x] Run focused checks and observe missing implementation/incorrect fixed-300 behavior fail (RED).
- [x] Implement the smallest compatible publisher and client changes. Add the bounded systemd units and Nginx location include.
- [x] Run focused checks, full Python suite, full Node suite and syntax/diff checks (GREEN).
- [x] Commit the verified implementation and record results in the ledger.

### Task 2: ECS deployment and delivery

**Files:** Create `docs/ecs-site-guide.md`, `docs/ecs-site-verification.json`; update `README.md`, source inventory and this plan. Credential-using host operations remain outside the repository.

**Interfaces:** Consume Task 1's CLI and units; initialize with the clean seed, run `/opt/newsflow/.venv/bin/python scripts/update_ecs_site.py`, and serve the site with the new Nginx include. All network actions use the existing verified server connection.

- [x] One fresh final review of implementation/config changes; fix material findings with regressions in one pass.
- [ ] Upload only clean source, models and public seed; create a dedicated user/venv, initialize the site, and validate installed systemd units.
- [ ] Back up the exact live Nginx config; add only the NewsFlow include; run `nginx -t` before reload, restoring the backup if validation fails.
- [ ] Enable the NewsFlow timer, complete a real update, and verify root/news/assets/data responses plus ThinkFlow health. Verify resource use and enabled state, without rebooting ECS.
- [ ] Exercise desktop/mobile browsing, source selection, bookmark and correction persistence, export and normal refresh in Edge.
- [ ] Save true deployment evidence, update public docs/package, integrate and push authorized delivery to GitHub; confirm remote HEAD and exact archive.
