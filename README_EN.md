# NewsFlow

A small, local news reader that automatically classifies Chinese headlines
into sports, technology, education, finance, and entertainment. Browse recent
news, search titles and summaries, filter sources, bookmark articles, and
correct categories. A reproducible machine learning graduation project is
included in the same application.

[中文说明](README.md) · [License](LICENSE) · [User guide](docs/newsflow-guide.md)

**Use online: [NewsFlow](https://ma-jamess.github.io/newsflow/).** GitHub Pages serves the public news reader independently of any local process. GitHub Actions attempts a feed refresh every five minutes; schedules may be delayed. Bookmarks, corrections and source display preferences belong to each browser. The downloadable Python application retains training, arbitrary-title/CSV classification and complete experiments. See [public deployment guide](docs/public-site-guide.md).

## Run

Install Python 3.11–3.13 (3.13 recommended), extract the complete source archive,
and run from its `NewsFlow` folder:

```powershell
python run.py
```

Windows users can also double-click `run.bat`. The launcher prepares a project
virtual environment and opens Microsoft Edge at `http://127.0.0.1:8510`.
The initial dependency installation needs internet access. The archive
includes source code, models, training data, tests, and experiment reports.
Models are retrained if their code/environment no longer matches.

```powershell
python run.py --no-browser
python run.py --port 8511
python run.py --setup-only
python run.py --retrain
```

The server listens on loopback. Each person runs their own instance; there is
no account system or shared hosted backend.

## Continuously updated feeds

The validated catalogue contains 43 free Chinese RSS/Atom channels, including
IT Home, SSPAI, China News, technology and gaming publishers, BBC Chinese,
DW, RFI, Yonhap Chinese, and ten Google Chinese News aggregation channels.
A GitHub-network audit on 2026-11-02 checked 91 candidates, found 46 readable
feeds, merged two duplicate alternatives, and excluded a confirmed 2008 Sina
finance archive. Feeds without publication dates
remain explicitly undated. See the [source catalogue and audit](docs/free-news-sources.md).

Edit `newsroom/sources.json` to update built-ins while keeping source IDs stable.
Public source preferences apply per browser; the downloadable application
also accepts custom public HTTPS RSS/Atom URLs in its source settings.

The server checks feeds every 120 seconds. The browser reads the local cache
every 20 seconds and a manual check has a 30-second cooldown. This is periodic
polling: publication speed depends on the original feeds, rather than a
push-based real-time news guarantee.

The default view covers the last 72 hours. Publication times and local fetch
times are distinct. Source errors preserve the cache. Bookmarks persist across
refreshes and restarts; unsaved cache entries are retained for seven days.
Only feed headlines and plain-text summaries are stored, with links to the
original articles.

Automatic news classification uses local scikit-learn models. It never calls
a paid API. Optional DeepSeek support is available only when the user manually
submits a headline in the quick classification page; that request is sent to
the official API and billed by the provider. Configure your own key according
to [the integration guide](docs/deepseek-integration.md). Personal keys,
history, and news caches are excluded from the source archive.

## Graduation project

The application retains single-title classification, a three-model comparison,
CSV batches, human review, calibrated probabilities, feature explanations,
confusion matrices, and reproducible NB/LR/SVM experiments. Human corrections
do not automatically change models or test data.

Held-out dataset metrics describe the bundled historical dataset. They do not
measure current-feed accuracy. The five-class model may misclassify new terms,
cross-topic stories, or categories it has never learned; probabilities are
model preferences, not guarantees or fact-checks.

## Development

Python standard-library HTTP server, SQLite, scikit-learn, and native
HTML/CSS/JavaScript; no frontend build step and no Node.js requirement to run
the application.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest -q
node --test tests/*.test.cjs
.venv\Scripts\python scripts/package.py
```

PowerShell users can run all Node checks with
`Get-ChildItem tests -Filter '*.test.cjs' | ForEach-Object { node --test $_.FullName }`.
The generated `dist/NewsFlow_1.4_完整源码.zip` contains a SHA-256 source inventory.

## License and attribution

NewsFlow code is MIT-licensed. Dataset and icon licenses remain under
`data/raw/` and `third_party/lucide/`. News content belongs to its publishers.
The layout and feed workflow were informed by ThinkFlow, NewsNow, and Horizon;
no code from those projects was copied into this implementation.
