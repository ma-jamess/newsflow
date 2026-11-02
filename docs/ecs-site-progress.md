# ECS ledger — plan: docs/superpowers/plans/2026-11-02-ecs-fixed-site.md

2026-11-02: user requested a fixed ECS site and authorized inspection/reuse of the existing ThinkFlow connection. SSH login succeeded using the existing separately stored settings and recorded ED25519 host key; credentials were not printed or copied. Ubuntu 24.04, Nginx 1.24 and systemd 255 confirmed. ThinkFlow health=200; `/newsflow/` previously reached its login redirect.

Ruling: reuse the clean NewsFlow export repository on a feature branch and retain its current static public reader/local model — existing user authorization covers ECS deployment, and preserving the current reader avoids introducing shared anonymous write APIs. Cost if wrong: a future change to the product/deployment architecture needs separate implementation.

Ruling: use the existing IP plus `/newsflow/` for the first fixed endpoint — no domain or certificate has been supplied and ThinkFlow already owns port 80/root. Cost if wrong: later domain/HTTPS binding requires DNS and a certificate; browser-local preferences are separated by origin.

Pre-flight: publication metadata -> PublicBackend -> UI schedule copy; modify all three together, preserving Pages defaults. Publisher -> Nginx static root -> systemd state-directory permissions; update only JSON after bootstrap, validate actual Linux units and Nginx alias. The existing ThinkFlow Nginx server has one default port-80 block and no NewsFlow location.

Task 1 RED: seven Python regressions failed on missing ECS publisher/unsupported publication metadata; five new Node cases failed on fixed-300 metadata, absent Pages defaults/interval validation and missing schedule rendering. Existing ten public-backend cases passed. Oversized-input fixtures use explicit short IDs so diagnostics do not echo multi-megabyte input.

Task 1 Linux contract RED: the actual ECS publisher, exercised with a deterministic classifier boundary and real SQLite/filesystem, replaced public JSON with a 0600 temporary file. The separate Nginx user requires a readable file. Add a POSIX regression and set 0644 before fsync/atomic replacement; verify on the real host as well as the Windows suite.

Task 1: complete — focused publication checks 23/23, full Windows Python 114 passed with one POSIX-only skip and the existing upstream pytz warning; full Node 46/46; Python/JS syntax and diff checks passed. Actual Ubuntu ECS tests 8/8 passed, including the POSIX readability case. Its explicit filesystem contract observed 0600 RED then 0644 GREEN. Linux model checks peaked at 294,792 KiB RSS with no swaps; ThinkFlow health stayed 200. Nginx and systemd templates passed real installed-tool validation. Code is ready for the one fresh whole-change review before exposing the new route.

Final review: one fresh independent review of 68248f0..be9b3d0 completed. Important/P2 malformed cached source IDs could stop all fetch attempts; Critical/Minor: none. The reviewer set aside live-host/browser checks, which remain mandatory deployment acceptance work.

Final: fixed malformed cached IDs and nested reader fields — four ID-list/dict cases and three result/probability/source-name cases observed RED then GREEN. Final Windows Python suite: 121 passed, 1 POSIX-only skipped, the existing upstream pytz warning; Node suite: 46 passed. Actual ECS Linux publisher suite: 15 passed, peak RSS 292,852 KiB, zero swaps, ThinkFlow health 200. No second review is needed.

Task 2: clean source and current fixes uploaded; dedicated newsflow user, state directory and /opt/newsflow/.venv installed. Site bootstrap, live Nginx inclusion and timer enablement remain pending.

Ruling: attempt trusted HTTPS for the fixed public IP using Let's Encrypt's now generally available shortlived IP certificates — official January 15, 2026 availability and production ACME profile were verified; no domain is needed. Require automated renewal and retain the existing HTTP/ThinkFlow route. Cost if wrong: certificate issuance or external port access may prevent HTTPS, in which case the working fixed HTTP endpoint remains available and the unmet HTTPS check must be reported.

Task 2 deployment: initialized /var/lib/newsflow/site as newsflow. Backed up exact live ThinkFlow Nginx bytes (SHA256 9fec20563eb0920f1f4e9beedb9c99569f1a548e9e84e0079edf250706c03035), added only the NewsFlow location include and validated before graceful reload. A later byte comparison confirmed no other edit to the original HTTP server. Its actual anonymous root redirect is /gate?next=/; GET /health remains 200.

Task 2 HTTPS: installed isolated Certbot 5.9.0 after verifying --ip-address/--required-profile and the supported automation flags from the installed official CLI. Staging issuance and production issuance succeeded for the IP SAN. Installed a separate 443 server, validated Nginx/systemd, enabled the twice-daily persistent renewal timer and tested renewal with the real deploy hook. Normal local/public TLS validation and Edge navigation succeeded. Initial certificate expiry: 2026-11-09 01:51:03 UTC; private account/key files remain outside the project, key mode 0600.

Task 2 live checks: the enabled timer completed two real rounds without a reboot, publishing 1,000 news / 43 sources with partial status; first run added 389 retained-cache rows, second 310. Fifteen channels failed to connect, while other channels updated. First round ran approximately 236 seconds and peaked at 276,475,904 bytes with zero swap. One CPU / 700 MiB limits are active; subsequent scheduling follows 120 seconds after completion. Twelve public assets, news/report JSON, slash/root redirects, denied public writes and 404 handling passed; ThinkFlow health remained 200 and its process start time remains 2026-10-24.

Task 2 Edge: desktop 1440x1000 and mobile 390x844 passed with no horizontal page/dialog overflow or page errors. Category, an expanded source, search, five probability bars, bookmarks, corrections, CSV export and three-model report passed. A newer automatic publication preserved the bookmark, human correction and hidden-source preference. Test overlays were cleared from the dedicated Edge profile after verification.

Final: Ruling: live-host/browser behaviors the reviewer declined to judge — completed installed-tool validation, two timer publications, normal public TLS, ACME renewal with deploy hook and Edge persistence checks; the original ThinkFlow HTTP config has only the intended include. Cost if wrong: a production regression requires restoring the saved Nginx config or previous public JSON.

Ruling: integrate the verified feature into main and update the existing public NewsFlow repository — the user's continuing authorization to deploy and save the project covers this delivery; the repository and base branch were verified directly. Cost if wrong: a normal revert restores the prior project revision without touching ThinkFlow.

Task 2 delivery: acceptance JSON and HTTPS guide prepared; Linux deployment templates are explicitly LF on Windows so the renewal hook remains executable after archive/checkout. Final source inventory, archive validation, main integration and remote verification are the remaining steps.
