# NewsFlow Live News Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing classifier a practical local news tool with fresh RSS data, automatic classification, filtering, bookmarks and preserved graduation experiments.

**Architecture:** Add a separate SQLite cache and a single background refresh coordinator. Existing local models classify incoming titles; the existing paid model path remains user initiated. Extend the native HTTP server and front end.

**Tech Stack:** Python 3.11–3.13 standard library, scikit-learn, SQLite, HTML/CSS/JavaScript, Node tests and Edge UI validation.

**Spec:** docs/superpowers/specs/2026-10-31-newsflow-live-design.md

## Global Constraints

- Refresh interval 120 seconds, browser poll 20 seconds, manual refresh cooldown 30 seconds; at most 3 concurrent sources.
- Network timeout 10 seconds, response cap 1 MiB, 80 entries per source, seven-day unbookmarked retention and default 72-hour view.
- Five existing categories and local threshold 0.65; automatic refresh never calls DeepSeek.
- Existing data/model/test reports remain reproducible; histories and news cache are independent and excluded from packages.
- Personal local service on 127.0.0.1, guarded Host/Origin/token, public HTTPS sources only and safe text rendering.

## Review Focus

- A reachable RSS feed whose newest item is years old must not appear freshly published.
- A partial fetch failure must preserve cached bookmarks/corrections while other sources update.
- Fast filter changes and responses arriving out of order must not show the previous selection.
- A redirected/custom feed must not access a private address or render executable content.
- Repeated refresh requests and application shutdown must not create duplicate jobs or orphaned workers.

### Task 1: Feed ingestion, persistence and refresh coordinator

**Files:** Create newsroom/feeds.py, newsroom/news_store.py, newsroom/live_news.py, tests/test_live_news.py.

**Interfaces:** parse_feed(data: bytes, feed_url: str, now: datetime) -> list[dict]; fetch_feed(url: str) -> bytes; NewsStore(path) sources/list/get/ingest/finish_source/bookmark/feedback methods; LiveNewsService(store, classifier, fetcher=fetch_feed) start/stop/request_refresh/refresh/snapshot/detail.

- [x] Write failing tests for RSS/Atom title/link/date extraction, malicious XML and URL rejection, public source validation; cached deduplication, bookmark/correction preservation, time filtering; real local classification on injected RSS network fixtures; partial failures, cooldown and lifecycle.
- [x] Run focused tests and inspect expected missing-feature failures.
- [x] Implement the three modules, using per-request SQLite connections and one update lock, status and event.
- [x] Run focused tests and the full Python suite; inspect all output.
- [x] Record completion and retain scoped changes on the existing feature branch, following the no-mixed-commits ledger ruling.

### Task 2: HTTP integration and redesigned news interface

**Files:** Modify newsroom/server.py, run.py, newsroom/__init__.py, web/index.html, web/app.js. Create web/live-news-ui.js, web/live-news.js, web/newsflow.css, tests/test_news_api.py and tests/live-news.test.cjs.

**Interfaces:** GET news returns rows/stats/update metadata; GET news/sources returns source health; GET news/detail?id returns an article and local explanation; guarded POST refresh/save/feedback/sources/export validate inputs and return changed metadata. window.NewsroomReady resolves after bootstrap; navigation accepts news.

- [x] Write and run failing tests for cache API filters, mutation authentication, server-generated export, source creation validation, and browser-side date/URL/filter display helpers.
- [x] Integrate lifecycle from run.py without network calls in existing create_server tests, register routes/static assets, and implement pagination and safe CSV export.
- [x] Build the news-first desktop/mobile page and source management. Keep existing page element IDs and one-title, batch, history and experiment behavior. Ignore stale search/detail responses; preserve focus where useful.
- [x] Run all Python/Node tests and syntax checks; then verify real feeds and Edge user flows at desktop and mobile widths.
- [x] Record completion and retain verified integration/UI changes uncommitted, following the ledger ruling.

### Task 3: Open-source delivery and final verification

**Files:** Modify README.md and scripts/package.py; add LICENSE, README_EN.md, docs/newsflow-guide.md and docs/newsflow-live-verification.json.

**Interfaces:** python run.py still starts the app; complete source archive NewsFlow_1.4_完整源码.zip excludes runtime data and credentials while including models, source, third-party notices and tests.

- [x] Update packaging tests before changing package naming/exclusions; verify failing expectation then implementation.
- [x] Document source freshness, update interval, local use, configurable sources, manually initiated paid model use, rights and reproducible graduation experiments.
- [x] Run required full checks, collect real feed/Edge evidence, and request one fresh whole-change reviewer using the spec and this Review Focus.
- [x] Fix material findings with regression tests, package and verify the archive in an independent extracted directory; record final results.
