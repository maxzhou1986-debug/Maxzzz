# Fund Radar V2.10 validation

Run `node tests/review-unit.cjs` and `node tests/sw.spec.cjs` from the repository root. Check JavaScript syntax using `node --check` on each file under `fund-radar`.

`review.spec.cjs` is a Playwright browser suite using synthetic, explicitly isolated JSONP fixtures. Install Playwright and its WebKit browser, then run `node tests/review.spec.cjs`. Set `TEST_BROWSER=chromium` to use Chromium. Optional `PLAYWRIGHT_MODULE` points to a bundled Playwright module. No production demo data enters review calculations.

Validated for this change: seven JavaScript files pass syntax checks; review logic tests and service worker tests pass. The local in-app browser displayed all seven tabs. Full Playwright/WebKit and Chromium runs were blocked by the host browser-process sandbox; iPhone device testing has not been completed. Live Eastmoney requests returned intermittently empty responses, so complete live-market coverage was not confirmed.

## Data behavior

- Review uses paginated Eastmoney stock lists, industry lists and representative indices independently of the radar's truncated rankings.
- The index timestamp supplies the market date. Only matching-date quotes with valid percentage change and positive turnover enter breadth and turnover totals. Excluded quotes and pagination coverage are displayed.
- HK industry indices use market 124; if unavailable, group only explicit industry labels supplied in HK quotes. If neither is provided, display missing industry data. Never substitute HK stocks for industries.
- Null and unavailable money fields remain missing. Positive and negative sector flows are ranked separately. No inferred funds, index values, or predictions.
- End-of-day snapshots retain ten dates per market. A-share close check is 15:00; HK check is 16:10 with the representative index updated at or after 16:00. Special half-day sessions remain previews when close cannot be established.
- While the app is open, check every five minutes after close and upon foregrounding. A closed iPhone PWA cannot collect in the background. Historical snapshots keep their original date and capture time.
- The six original features retain their implementations. Four add-ons only gain an initialization guard to handle old service-worker script concatenation during upgrades. New HTML loads all scripts explicitly. The new service worker supports legacy unversioned clients and scoped offline caches.
