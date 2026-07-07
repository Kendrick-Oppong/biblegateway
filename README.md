# BibleGateway Scrape

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A **fast, async, production-ready** web scraper that downloads the entire Bible across **50+ translations** from BibleGateway.com (https://www.biblegateway.com), and exports them into individual JSON files formatted as flat lists of verses.

---

## Features

| Feature | Description |
| :--- | :--- |
| Async / Concurrent | Scrapes all translations for a verse in parallel — 10x faster than sync. |
| Smart Resume | `--resume` picks up exactly where you left off with **accurate progress tracking** — automatically rebuilds progress from HTML cache if needed. Progress is calculated per verse-translation, not just per verse. |
| HTML Cache | Avoids re-downloading pages. Cache is used for both scraping and resume progress calculation. `--force-refresh` to bypass. |
| Retry Logic | Exponential backoff with `tenacity` for network flakiness. |
| Rate Limiting | Configurable concurrency (`--max-concurrent`) to avoid being blocked. |
| Accurate Progress | Live `tqdm` showing **true completion percentage** based on total work (31,102 verses × number of translations), not just remaining work. Includes speed (verse-translations/sec) and accurate ETA. |
| Per-Version JSON | Exports flat JSON arrays per translation (e.g., `versions/King James Version/KJV_bible.json`). |
| Export Command | `--export-versions` regenerates all translation JSON files from `bible_data.json`. |
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
├── bible_scraper.log          ← Scraper activity log (optional)
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

The scraper displays a live-updating progress bar directly in your terminal that shows **accurate total progress** across all translations, not just progress on remaining work:

```
Resuming: 115,444/684,244 verse-translations already completed (16.9%)
Scraping: 16.87%|███████░░░░░░░░░░░░░░░░░░| 115,444/684,244 [00:42<3:45:12, 42.0v-t/s]
```

**Key Improvement:** Progress is calculated as **verse-translations** (verses × number of translations), not just verses. This means:

- **22 translations × 31,102 verses = 684,244 total work units**
- If you have 5,247 verses cached for all 22 translations = 115,444 completed work units (16.9%)
- The progress bar shows your **true completion percentage** from 0-100%

When you use `--resume`, the scraper:
1. **Counts completed work** by checking which verse-translations exist in `bible_data.json`
2. **Rebuilds from cache** if progress files are missing
3. **Displays accurate percentage** based on total verse-translations (not just verses)
4. **Calculates correct ETA** based only on remaining work

Instead of showing:
```
Scraping: 0.00%|          | 0/31,102 [...]  ← Wrong! Doesn't count cached verses or translations
```

You'll see:
```
Rebuilding progress from HTML cache...
Rebuilt 115,444 verse-translations from cache
Resuming: 115,444/684,244 verse-translations already completed (16.9%)
Scraping: 16.87%|███████░  | 115,444/684,244 [...]  ← Correct! Shows true progress across all translations
```

The progress bar displays:
- **Percentage completed** (based on all verse-translations: 31,102 × number of translations)
- **Current position** in the Bible (book chapter:verse)
- **Work unit count** (completed/total verse-translations)
- **Speed** (verse-translations/second, shown as "v-t/s")
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

This checks all 66 canonical books and 31,102 verses per translation and prints a completeness report.

Example output:

```
Translation          Total Expected   Found   Missing   Complete
-------------------  --------------- ------- --------- ---------
KJV                        31,102   31,101        1    100.0%  OK
NIV                        31,102   31,086       16     99.95%  OK
ESV                        31,102   31,085       17     99.95%  OK
AMP                        31,102   31,102        0    100.0%  OK
```

Useful options:

```bash
# Check only one translation
python cli.py --verify --verify-version KJV

# Print the summary table only (no per-verse detail)
python cli.py --verify --summary-only

# Export missing verses to a file for detailed analysis
python cli.py --verify --export-missing missing_verses.json
```

#### Understanding Missing Verses

**Important**: Some translations will show "missing" verses - this is **expected and normal**. Different Bible translations have different verse counts due to textual criticism and manuscript traditions:

**Why verses are missing:**

1. **Modern critical text translations** (NIV, ESV, NRSV, CSB, NET, etc.) omit verses not found in the earliest Greek manuscripts:
   - Matthew 17:21, 18:11, 23:14
   - Mark 7:16, 9:44, 9:46, 11:26, 15:28
   - Luke 17:36, 23:17
   - John 5:4
   - Acts 8:37, 15:34, 24:7, 28:29
   - Romans 16:24
   
   These verses are typically included in footnotes as "some manuscripts include..."

2. **3 John 1:15** doesn't exist in any translation (3 John only has 14 verses)

3. **Textual variants** mean some translations combine verses or format them differently (e.g., CEV's genealogy in Matthew 1)

**Expected completion rates:**
- Most translations: 99.9%+ (missing only verses not in their textual tradition)
- Overall across all translations: 99.96%+
- 4+ translations at 100%: NIRV, AMP, NCV

**This is not a scraper error** - these verses genuinely don't exist on BibleGateway for those translations.

#### Retrying Missing Verses

If you want to double-check missing verses, use `--force-refresh` to re-download them directly from BibleGateway:

```bash
# Force re-download missing verses (ignores cache)
python cli.py -v KJV NIV ESV --retry-missing --force-refresh

# Retry only specific translation
python cli.py -v NIV --retry-missing --force-refresh
```

After running with `--force-refresh`, verses that are still missing are confirmed to not exist in those translations.

### Fetching Missing Verses

If you want to manually supplement the dataset with verses from other sources, you can:

1. Use `--export-missing` to get a list of missing verses
2. Manually look up those verses from physical Bibles or other sources
3. Edit `bible_data.json` directly to add them
4. Run `python cli.py --export-versions` to regenerate the per-translation JSON files

### Step 3 — Use the Exported Files

After scraping and verifying, you can export each translation as a flat JSON file:

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

## CLI Command Reference

### Scraping Commands

```bash
# Scrape specific translations
python cli.py -v KJV NIV ESV --resume

# Scrape all 50+ translations
python cli.py --scrape-all --resume --max-concurrent 50

# Retry only missing verses
python cli.py -v KJV --retry-missing

# Force re-download (ignore cache)
python cli.py -v KJV --force-refresh

# Start fresh (delete all progress)
python cli.py -v KJV --overwrite

# Enable auto-verify after scraping
python cli.py -v KJV --auto-verify
```

### Verification Commands

```bash
# Verify all translations
python cli.py --verify

# Verify specific translation
python cli.py --verify --verify-version KJV

# Show summary only (no missing verse details)
python cli.py --verify --summary-only

# Export missing verses to JSON
python cli.py --verify --export-missing missing_verses.json
```

### Export and Utility Commands

```bash
# Export all translations to individual JSON files
python cli.py --export-versions

# Show failed verses from last scrape
python cli.py --show-failed

# Clear failed verses log
python cli.py --clear-failed

# Enable debug logging
python cli.py -v KJV --debug
```

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

### "Why is verify showing missing verses?"

**This is normal!** Different Bible translations have different verse counts due to textual criticism:
- Modern translations (NIV, ESV, etc.) omit ~17 verses not in earliest manuscripts
- 3 John only has 14 verses (verse 15 doesn't exist)
- See the "Understanding Missing Verses" section under Step 2 for details

To confirm verses are truly unavailable:
```bash
python cli.py -v NIV --retry-missing --force-refresh
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

### "How do I export a list of missing verses?"

```bash
python cli.py --verify --export-missing missing_verses.json
```

This creates a JSON file with all missing verses organized by translation, useful for analysis or documentation.

---

## Expected Results

After successfully scraping, you should see:

**Overall Statistics:**
- Total verses per translation: 31,102
- Some translations may be missing verses due to textual variants

**What to expect:**
- Most modern critical text translations (NIV, ESV, NLT, etc.) will be missing some verses
- These verses are absent from the earliest Greek manuscripts and are therefore excluded
- Some translations format verses differently (combining or splitting them)

**If you need missing verses:**
- Export missing verses: `python cli.py --verify --export-missing missing_verses.json`
- Manually collect them from physical Bibles or other sources
- Edit `bible_data.json` directly to add them, or write a script to merge them
- Re-export: `python cli.py --export-versions`

The scraper downloads what's available on BibleGateway - missing verses reflect the actual content of each translation.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

**Important:** This license applies only to the scraper software itself. Bible translations have their own copyright terms and are not covered by this MIT License. See the LICENSE file for full details on Bible content usage.

## Acknowledgments

- BibleGateway.com — Source of all Bible content
- Python Community — For the tools and libraries that made this possible

---

**Important Note:** This is a web-scraping project. Please use it responsibly and respect BibleGateway's terms of service. Always provide copyright and credit information when using Bible translations in your applications.

**Copyright Notice:** Bible translations have different copyright terms. This data is intended for personal/educational use. For public or commercial use, verify licensing for each translation.
