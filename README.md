# BibleGateway Scrape

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A **fast, async, production-ready** web scraper that downloads the entire Bible across **50+ translations** from BibleGateway.com (https://www.biblegateway.com), and exports them into individual JSON files formatted as flat lists of verses.

---

## Features

| Feature | Description |
| :--- | :--- |
| Async / Concurrent | Scrapes all translations for a verse in parallel — 10x faster than sync. |
| Smart Resume | `--resume` picks up exactly where you left off with **accurate progress tracking** — automatically rebuilds progress from HTML cache if needed. |
| HTML Cache | Avoids re-downloading pages. Cache is used for both scraping and resume progress calculation. `--force-refresh` to bypass. |
| Retry Logic | Exponential backoff with `tenacity` for network flakiness. |
| Rate Limiting | Configurable concurrency (`--max-concurrent`) to avoid being blocked. |
| Accurate Progress | Live `tqdm` showing **true completion percentage** based on total verses (31,102), not just remaining work. Includes speed (verses/sec) and accurate ETA. |
| Per-Version JSON | Exports flat JSON arrays per translation (e.g., `versions/King James Version/KJV_bible.json`). |
| Retry Missing | `--retry-missing` finds and re-scrapes only verses that failed. |
| Verify Completeness | `--verify` checks every book, chapter, and verse against the canonical structure. |
| Overwrite Protection | Prompts or `--overwrite` to force a fresh start. |
| Scrape All | `--scrape-all` downloads all 50+ translations in one command. |
| Multi-Language Support | English, Tagalog, Cebuano, Ilonggo translations. |

---

## Project Structure (Your Actual Setup)

```
biblegateway/                  ← Project root (also the package)
├── .venv/                     ← Virtual environment (optional)
├── __init__.py                ← Makes it a package
├── version.py                 ← All translation codes (50+ versions)
├── audio_version.py           ← Audio version codes
├── utils.py                   ← Book detection helper
├── verse.py                   ← Single verse lookup
├── daily_verse.py             ← Daily verse
├── audio.py                   ← Audio lookup
├── bible_structure.py         ← Canonical Bible structure (66 books)
├── scraper.py                 ← Full async scraper with resume, cache, progress
├── verify.py                  ← Verify completeness
├── translations.py            ← Human-readable names for folders
├── cli.py                     ← Command-line entrypoint
├── requirements.txt           ← Python dependencies
├── README.md                  ← You are here
├── .gitignore
│
├── bible_data.json            ← Raw scraped data (created by scraper)
├── scraper_progress.json      ← Resume checkpoint — automatically saved after each batch
├── failed_verses.json         ← Tracks verses that failed to download
├── bible_scraper.log          ← Scraper activity log
│
├── versions/                  ← Per-translation output (created by scraper)
│   ├── Amplified Bible/
│   │   └── AMP_bible.json
│   ├── King James Version/
│   │   └── KJV_bible.json
│   └── ...
│
└── html_cache/                ← Cached HTML pages (auto-created, enables fast resume)
    ├── KJV/
    │   ├── Genesis/
    │   │   ├── 1/
    │   │   │   ├── 1.html
    │   │   │   ├── 2.html
    │   │   │   └── ...
    ├── NIV/
    ├── ESV/
    └── ...
```

**Important Files:**
- **`bible_data.json`** — Contains all scraped verses organized by translation → book → chapter → verse
- **`scraper_progress.json`** — Tracks which verses are complete across all requested translations
- **`html_cache/`** — Stores downloaded HTML to avoid re-fetching (used for both scraping and resume progress calculation)

---

## Quick Start

### Prerequisites

Make sure you have **Python 3.11+** installed, then install dependencies:

```bash
pip install -r requirements.txt
```

### Step 1 — Scrape the Bible

This downloads all translations from BibleGateway, verse by verse. It scrapes ~31,000 verses and captures 50+ translations simultaneously from each verse page.

Since you're running from inside the `biblegateway` folder, use `python cli.py` instead of `python -m biblegateway.cli`:

```bash
# Scrape a single translation
python cli.py -v KJV -o versions

# Scrape multiple translations
python cli.py -v KJV NIV ESV -o versions --resume

# Scrape ALL 50+ translations
python cli.py --scrape-all --resume
```

This will take 1.5–3 hours depending on network speed and `--max-concurrent` setting. The scraper is intentionally rate-limited to be respectful to BibleGateway.

#### Smart Resume Feature

The `--resume` flag intelligently continues from where you left off, even across different scraping sessions:

**Scenario 1: Resume after interruption**
```bash
# Start scraping
python cli.py -v KJV NIV ESV --resume

# Press Ctrl+C to interrupt after 5,000 verses
# Later, resume from exactly verse 5,001
python cli.py -v KJV NIV ESV --resume
```

**Scenario 2: Add more translations later**
```bash
# First, scrape 3 translations
python cli.py -v KJV NIV ESV --resume

# Later, add 2 more translations
# The scraper detects you already have KJV, NIV, ESV cached
# It only downloads NASB and NLT for all verses
python cli.py -v KJV NIV ESV NASB NLT --resume
```

**Scenario 3: Resume from cache after data loss**
```bash
# You have html_cache/ but lost bible_data.json
python cli.py -v KJV --resume

# Output:
# Rebuilding progress from HTML cache...
# Rebuilt 31,102 verses from cache
# Resuming: 31,102/31,102 verses already completed (100.0%)
# No verses to scrape (all done).
```

The resume system uses three tracking mechanisms:
1. **`scraper_progress.json`** — Tracks which verses are complete
2. **`bible_data.json`** — Stores the actual verse text data
3. **`html_cache/`** — Cached HTML files (used as fallback if progress files are lost)

#### Accidental Overwrite Protection

If you run `python cli.py` without `--resume` but have existing data or progress files, the scraper will detect it and print a warning:

- **Interactive terminal:** You will be prompted to either `[r]` Resume (highly recommended), `[o]` Overwrite (start fresh), or `[a]` Abort.
- **Non-interactive terminal (scripts):** The scraper will fail safely and abort, prompting you to explicitly pass `--resume` or `--overwrite`.

#### Terminal Progress Bar

The scraper displays a live-updating progress bar directly in your terminal that shows **accurate total progress**, not just progress on remaining work:

```
Resuming: 5,247/31,102 verses already completed (16.9%)
Scraping: 16.87%|███████░░░░░░░░░░░░░░░░░░░| 5,247/31,102 [00:42<3:45:12, 1.91verse/s]
```

When you use `--resume`, the scraper:
1. **Automatically detects** cached HTML files from previous runs
2. **Rebuilds progress** from cache if needed (shows which verses are already downloaded)
3. **Displays accurate percentage** from 0-100% based on total Bible verses (31,102)
4. **Calculates correct ETA** based only on remaining work

Instead of showing:
```
Scraping: 0.00%|          | 0/25,855 [...]  ← Wrong! Doesn't count cached verses
```

You'll see:
```
Rebuilding progress from HTML cache...
Rebuilt 5,247 verses from cache
Resuming: 5,247/31,102 verses already completed (16.9%)
Scraping: 16.87%|███████░  | 5,247/31,102 [...]  ← Correct! Shows true progress
```

The progress bar displays:
- **Percentage completed** (based on all 31,102 verses)
- **Current position** in the Bible (book chapter:verse)
- **Verse count** (completed/total)
- **Speed** (verses/second)
- **Accurate ETA** (estimated time for remaining work)

#### Monitor Log File

To keep your terminal clean, all detailed logs are written to `bible_scraper.log`. Watch it live:

```bash
# Linux / macOS
tail -f bible_scraper.log

# Windows (PowerShell)
Get-Content bible_scraper.log -Wait
```

### Step 2 — Verify the Data

Once scraping is complete (or even while it's running), verify that all books, chapters, and verses were captured correctly:

```bash
python cli.py --verify
```

This checks all 66 canonical books and 31,103 verses per translation and prints a completeness report.

Example output:

```
Translation          Total Expected   Found   Missing   Complete
-------------------  --------------- ------- --------- ---------
KJV                        31,102   31,102        0    100.0%  OK
NIV                        31,102   31,100        2     99.99%  INCOMPLETE
ESV                        31,085   31,085        0    100.0%  OK
NLT                        31,102   31,102        0    100.0%  OK
```

Useful options:

```bash
# Check only one translation
python cli.py --verify --verify-version KJV

# Print the summary table only (no per-verse detail)
python cli.py --verify --summary-only

# Export missing verses to a file for later retry
python cli.py --verify --export-missing missing.json
```

If any translation shows INCOMPLETE, run a targeted retry instead of re-running the entire scrape:

```bash
# Retry only verse pages that verify.py reports as truly missing
python cli.py -v KJV --retry-missing

# Re-download those pages instead of using cached HTML first
python cli.py -v KJV --retry-missing --force-refresh
```

### Step 3 — Use the Exported Files

After scraping and verifying, the scraper automatically exports each translation as a flat JSON file inside a human-readable folder in `versions/`

File structure:

```
versions/
├── Amplified Bible/
│   └── AMP_bible.json
├── English Standard Version/
│   └── ESV_bible.json
├── King James Version/
│   └── KJV_bible.json
└── ...
```

Each JSON file is an array of verse objects:

```json
[
  { "book": "Genesis", "chapter": 1, "verse": 1, "text": "In the beginning God created..." },
  { "book": "Genesis", "chapter": 1, "verse": 2, "text": "And the earth was without form..." }
]
```

Copy the translations you need:

```bash
# Linux / macOS
cp -r "versions/King James Version" ../your-bible-app/resources/bibles/

# Windows (PowerShell)
Copy-Item -Recurse "versions\King James Version" "..\your-bible-app\resources\bibles\"
```

---

## API (On-Demand Lookup)

In addition to full-Bible scraping, the package provides lightweight on-demand lookup functions:

### Fetch a Verse

```python
from biblegateway import verse, version

result = verse("John 3:16", version.ENG_KING_JAMES_VERSION)
print(result)
# { "book": "John 3:16", "verses": ["For God so loved the world..."] }
```

### Daily Verse

```python
from biblegateway import daily_verse, version

daily = daily_verse(version.ENG_NEW_INTERNATIONAL_VERSION, (2026, 7, 3))
print(daily)
```

### Audio Bible

```python
from biblegateway import audio, audio_version

audio_data = audio("John 1", audio_version.KJV_PAUL_MIMS)
print(audio_data["mp3"])
```

---

## Available Translations

The scraper captures 50+ translations from BibleGateway, including:

### English Versions

| Code | Name |
| :--- | :--- |
| KJV | King James Version |
| NIV | New International Version |
| ESV | English Standard Version |
| NLT | New Living Translation |
| CSB | Christian Standard Bible |
| NASB | New American Standard Bible |
| NKJV | New King James Version |
| AMP | Amplified Bible |
| MSG | The Message |
| GNT | Good News Translation |
| NRSVA | New Revised Standard Version Anglicised |
| ... | and 30+ more |

### Tagalog Versions

| Code | Name |
| :--- | :--- |
| ADB1905 | Ang Dating Biblia (1905) |
| ABTAG1978 | Ang Biblia (1978) |
| ABTAG2001 | Ang Biblia (2001) |
| MBBTAG | Magandang Balita Biblia |
| ASND | Ang Salita ng Diyos |

### Other Languages

| Code | Name |
| :--- | :--- |
| APSD-CEB | Ang Pulong Sa Dios (Cebuano) |
| HLGN | Ang Pulong Sang Dios (Ilonggo) |

---

## Performance Tuning

| Setting | Default | Recommendation |
| :--- | :--- | :--- |
| `--max-concurrent` | 20 | Increase to 30–50 on fast networks, but beware of rate limiting. |
| `--batch-size` | 5 | Larger batches reduce overhead but use more memory. |
| `--force-refresh` | False | Use only when BibleGateway changes layout or cache is corrupted. |
| `--resume` | False | Always use unless starting fresh. |

---

## Edge Cases Handled

| Issue | Solution |
| :--- | :--- |
| Network timeouts | Retry 4× with exponential backoff (1s, 2s, 4s, 15s) |
| HTTP 429 (Rate Limit) | Retry with longer delays via tenacity |
| Missing verses | Returns None and continues (logs to `failed_verses.json`) |
| Malformed HTML | Falls back to alternative CSS selectors |
| Cache corruption | `--force-refresh` bypasses cache |
| Keyboard Interrupt | Saves all progress immediately |
| Empty verse text | Caches as `__EMPTY__` to avoid re-fetching |
| Overwrite protection | Prompts user or requires `--overwrite` flag |
| Resume with cache but no progress | Automatically rebuilds progress from cached HTML files |
| Adding new translations to existing scrape | Detects missing translations and only scrapes those |

---

## Troubleshooting

### "Why does --resume show 0% when I have cached data?"

**Fixed in latest version!** The scraper now automatically detects cached HTML files and rebuilds the progress tracker. You'll see:
```
Rebuilding progress from HTML cache...
Rebuilt 5,247 verses from cache
```

### "How do I check which verses failed?"

```bash
python cli.py --show-failed
```

To retry failed verses:
```bash
python cli.py -v KJV --retry-missing
```

To clear the failed verses log:
```bash
python cli.py --clear-failed
```

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.

## Acknowledgments

- BibleGateway.com — Source of all Bible content
- Python Community — For the tools and libraries that made this possible

---

**Important Note:** This is a web-scraping project. Please use it responsibly and respect BibleGateway's terms of service. Always provide copyright and credit information when using Bible translations in your applications.

**Copyright Notice:** Bible translations have different copyright terms. This data is intended for personal/educational use. For public or commercial use, verify licensing for each translation.
