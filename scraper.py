import os
import json
import asyncio
import time
import logging
import re
import html
from typing import List, Dict, Any, Optional, Tuple, Set

import aiohttp
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm as async_tqdm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from bible_structure import BIBLE_STRUCTURE, TOTAL_VERSES, get_all_book_names
from translations import VERSION_NAMES, sanitize_folder_name

logger = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS = (
    aiohttp.ClientError,
    aiohttp.ClientConnectionError,
    asyncio.TimeoutError,
    ConnectionError,
)


def clean_verse_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'^\d+', '', text)
    text = re.sub(r'\(\s*[A-Z]\s*\)', '', text)
    text = re.sub(r'\[\s*[a-zA-Z0-9]+\s*\]', '', text)
    text = re.sub(r'\([A-Z]\)', '', text)
    text = re.sub(r'\[[a-zA-Z0-9]+\]', '', text)
    text = re.sub(r'\s*\(\s*[A-Z]\s*\)\s*', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'([a-zA-Z])&([a-zA-Z])', r'\1 & \2', text)

    fixes = {
        r'theLord': 'the Lord',
        r'theLORD': 'the LORD',
        r'andLord': 'and Lord',
        r'andLORD': 'and LORD',
        r'LordGod': 'Lord God',
        r'LORDGod': 'LORD God',
        r'Lordsaid': 'Lord said',
        r'LORDsaid': 'LORD said',
        r'Lordcommanded': 'Lord commanded',
        r'LORDcommanded': 'LORD commanded',
        r'Lordhad': 'Lord had',
        r'LORDhad': 'LORD had',
        r'Lordput': 'Lord put',
        r'LORDput': 'LORD put',
        r'Lordset': 'Lord set',
        r'LORDset': 'LORD set',
        r'Lordgave': 'Lord gave',
        r'LORDgave': 'LORD gave',
        r'Lordtold': 'Lord told',
        r'LORDtold': 'LORD told',
        r'Lordasked': 'Lord asked',
        r'LORDasked': 'LORD asked',
        r'Lordspake': 'Lord spake',
        r'LORDspake': 'LORD spake',
        r'Lordanswered': 'Lord answered',
        r'LORDanswered': 'LORD answered',
        r'Godsaid': 'God said',
        r'Godsaw': 'God saw',
        r'Godmade': 'God made',
        r'Godcreated': 'God created',
        r'Godblessed': 'God blessed',
        r'Godcalled': 'God called',
        r'Godcommanded': 'God commanded',
        r'Godput': 'God put',
        r'Godset': 'God set',
        r'Godgave': 'God gave',
        r'Godtold': 'God told',
        r'Godasked': 'God asked',
        r'Godspake': 'God spake',
        r'Godanswered': 'God answered',
        r'JesusChrist': 'Jesus Christ',
        r'ChristJesus': 'Christ Jesus',
        r'Jesussaid': 'Jesus said',
        r'Christsaid': 'Christ said',
        r'Jesusanswered': 'Jesus answered',
        r'Christanswered': 'Christ answered',
        r'HolySpirit': 'Holy Spirit',
        r'HolyGhost': 'Holy Ghost',
        r'theHolySpirit': 'the Holy Spirit',
        r'theHolyGhost': 'the Holy Ghost',
        r'SonofGod': 'Son of God',
        r'SonofMan': 'Son of Man',
        r'SonofDavid': 'Son of David',
        r'KingdomofGod': 'Kingdom of God',
        r'KingdomofHeaven': 'Kingdom of Heaven',
        r'KingdomofIsrael': 'Kingdom of Israel',
        r'theFather': 'the Father',
        r'theSon': 'the Son',
        r'theHolyOne': 'the Holy One',
        r'theMostHigh': 'the Most High',
        r'MostHigh': 'Most High',
    }
    for pattern, replacement in fixes.items():
        text = re.sub(pattern, replacement, text)

    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    common_combined = [
        (r'darknesswasupon', 'darkness was upon'),
        (r'thatit', 'that it'),
        (r'andherb', 'and herb'),
        (r'whichwereabove', 'which were above'),
        (r'drylandappear', 'dry land appear'),
        (r'thatis', 'that is'),
        (r'andit', 'and it'),
        (r'andthere', 'and there'),
        (r'thatthe', 'that the'),
        (r'andthe', 'and the'),
        (r'ofhis', 'of his'),
        (r'inhis', 'in his'),
        (r'forit', 'for it'),
        (r'butit', 'but it'),
        (r'andthey', 'and they'),
        (r'thatthey', 'that they'),
        (r'andwhen', 'and when'),
        (r'itwas', 'it was'),
        (r'hewas', 'he was'),
        (r'shewas', 'she was'),
        (r'theywere', 'they were'),
        (r'youshall', 'you shall'),
        (r'heshall', 'he shall'),
        (r'sheshall', 'she shall'),
        (r'itshall', 'it shall'),
        (r'theyshall', 'they shall'),
        (r'weshall', 'we shall'),
        (r'andshall', 'and shall'),
        (r'shallbe', 'shall be'),
        (r'willbe', 'will be'),
        (r'havebeen', 'have been'),
        (r'hadsaid', 'had said'),
        (r'havemade', 'have made'),
        (r'isnot', 'is not'),
        (r'arenot', 'are not'),
        (r'wasnot', 'was not'),
        (r'werenot', 'were not'),
        (r'havenot', 'have not'),
        (r'hasnot', 'has not'),
        (r'didnot', 'did not'),
        (r'cannot', 'can not'),
        (r'wouldnot', 'would not'),
        (r'shouldnot', 'should not'),
        (r'willnot', 'will not'),
        (r'maynot', 'may not'),
    ]
    for pattern, replacement in common_combined:
        text = re.sub(pattern, replacement, text)

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.,;!?:])', r'\1', text)
    text = re.sub(r'"\s+', '"', text)
    text = re.sub(r"'\s+", "'", text)
    text = re.sub(r'[\u200b\u200c\u200d\u2060\uFEFF]', '', text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class BibleGatewayScraper:
    def __init__(
        self,
        versions: List[str],
        output_dir: str = "versions",
        max_concurrent: int = 20,
        resume: bool = False,
        overwrite: bool = False,
        force_refresh: bool = False,
        retry_missing: bool = False,
        auto_verify: bool = False,
    ):
        self.versions = versions
        self.output_dir = output_dir
        self.max_concurrent = max_concurrent
        self.resume = resume
        self.overwrite = overwrite
        self.force_refresh = force_refresh
        self.retry_missing = retry_missing
        self.auto_verify = auto_verify

        self.cache_dir = "html_cache"
        self.progress_file = "scraper_progress.json"
        self.data_file = "bible_data.json"
        self.failed_file = "failed_verses.json"

        self.progress: Dict[str, bool] = {}
        self.data: Dict[str, Dict[str, Dict[int, Dict[int, str]]]] = {}
        self.failed: Dict[str, str] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        self._load_state()

    def _load_state(self):
        if self.overwrite:
            self.progress = {}
            self.data = {}
            self.failed = {}
            return
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf-8") as f:
                self.progress = json.load(f)
        else:
            self.progress = {}
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                # JSON loads with string keys, keep them as strings for consistency
        else:
            self.data = {}
        if os.path.exists(self.failed_file):
            with open(self.failed_file, "r", encoding="utf-8") as f:
                self.failed = json.load(f)
        else:
            self.failed = {}
        
        # If resuming and we have cache, rebuild missing data from cache
        if self.resume and os.path.exists(self.cache_dir):
            # Check if any requested versions are missing from data or incomplete
            needs_rebuild = False
            if not self.data:
                needs_rebuild = True
            else:
                for version_code in self.versions:
                    if version_code not in self.data:
                        needs_rebuild = True
                        break
            
            if needs_rebuild:
                logger.info("Rebuilding progress from HTML cache...")
                self._rebuild_from_cache()

    def _save_state(self):
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        with open(self.failed_file, "w", encoding="utf-8") as f:
            json.dump(self.failed, f, indent=2, ensure_ascii=False)

    def _rebuild_from_cache(self):
        """Rebuild progress and data from HTML cache files."""
        rebuilt_count = 0
        logger.info(f"Scanning cache for {len(self.versions)} version(s)...")
        
        for book, chapters in BIBLE_STRUCTURE.items():
            for chapter, vcount in chapters:
                for verse in range(1, vcount + 1):
                    # Check if ALL requested versions have this verse cached
                    all_cached = True
                    verse_texts = {}
                    
                    for version_code in self.versions:
                        # Skip if already in data (use string keys for JSON compatibility)
                        if (version_code in self.data and 
                            book in self.data[version_code] and
                            str(chapter) in self.data[version_code][book] and
                            str(verse) in self.data[version_code][book][str(chapter)]):
                            verse_texts[version_code] = self.data[version_code][book][str(chapter)][str(verse)]
                            continue
                        
                        cache_path = self._get_cache_path(version_code, book, chapter, verse)
                        if os.path.exists(cache_path):
                            with open(cache_path, "r", encoding="utf-8") as f:
                                cached_text = f.read()
                            if cached_text and cached_text != "__EMPTY__":
                                verse_texts[version_code] = cached_text
                            else:
                                all_cached = False
                                break
                        else:
                            all_cached = False
                            break
                    
                    # If all versions have valid cache, mark as done (use string keys)
                    if all_cached and len(verse_texts) == len(self.versions):
                        for version_code, text in verse_texts.items():
                            self.data.setdefault(version_code, {})
                            self.data[version_code].setdefault(book, {})
                            self.data[version_code][book].setdefault(str(chapter), {})
                            self.data[version_code][book][str(chapter)][str(verse)] = text
                        
                        self._mark_verse_done(book, chapter, verse)
                        rebuilt_count += 1
        
        if rebuilt_count > 0:
            logger.info(f"Rebuilt {rebuilt_count} verses from cache")
            self._save_state()
        else:
            logger.info("No additional verses found in cache")
        
        return rebuilt_count

    def _is_verse_done(self, book: str, chapter: int, verse: int) -> bool:
        key = f"{book}_{chapter}_{verse}"
        if not self.progress.get(key, False):
            return False
        for version_code in self.versions:
            if not (version_code in self.data and
                    book in self.data[version_code] and
                    str(chapter) in self.data[version_code][book] and
                    str(verse) in self.data[version_code][book][str(chapter)]):
                return False
        return True

    def _mark_verse_done(self, book: str, chapter: int, verse: int):
        key = f"{book}_{chapter}_{verse}"
        self.progress[key] = True

    def _log_failed(self, book: str, chapter: int, verse: int, error: str):
        key = f"{book}_{chapter}_{verse}"
        self.failed[key] = error

    def _get_cache_path(self, version: str, book: str, chapter: int, verse: int) -> str:
        safe_book = book.replace(" ", "_").replace("'", "")
        version_safe = version.replace("/", "_")
        return os.path.join(
            self.cache_dir,
            version_safe,
            safe_book,
            str(chapter),
            f"{verse}.html"
        )

    def _get_verses_to_scrape(self) -> List[Tuple[str, int, int]]:
        if self.retry_missing:
            return self._find_missing_verses()
        results = []
        for book, chapters in BIBLE_STRUCTURE.items():
            for chapter, vcount in chapters:
                for verse in range(1, vcount + 1):
                    if self.resume and self._is_verse_done(book, chapter, verse):
                        continue
                    results.append((book, chapter, verse))
        return results

    def _find_missing_verses(self) -> List[Tuple[str, int, int]]:
        """Find verses that are missing from at least one of the requested translations."""
        missing = []
        for book, chapters in BIBLE_STRUCTURE.items():
            for chapter, vcount in chapters:
                for verse in range(1, vcount + 1):
                    # Check if ANY of the requested versions is missing this verse
                    is_missing_from_any = False
                    for version_code in self.versions:
                        if not (version_code in self.data and
                                book in self.data[version_code] and
                                str(chapter) in self.data[version_code][book] and
                                str(verse) in self.data[version_code][book][str(chapter)] and
                                self.data[version_code][book][str(chapter)][str(verse)]):
                            is_missing_from_any = True
                            break
                    if is_missing_from_any:
                        missing.append((book, chapter, verse))
        return missing

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS)
    )
    async def _fetch_verse_text(
        self,
        session: aiohttp.ClientSession,
        version: str,
        book: str,
        chapter: int,
        verse: int
    ) -> Optional[str]:
        passage = f"{book} {chapter}:{verse}"
        url = "https://www.biblegateway.com/passage/"
        params = {
            "search": passage,
            "version": version,
            "interface": "print"
        }

        cache_path = self._get_cache_path(version, book, chapter, verse)
        if not self.force_refresh and os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_text = f.read()
            if cached_text and cached_text != "__EMPTY__":
                return cached_text

        async with self._semaphore:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            try:
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 429:
                        raise aiohttp.ClientResponseError(
                            status=429,
                            message="Rate limited",
                            headers=resp.headers,
                            request_info=resp.request_info,
                            history=resp.history
                        )
                    if resp.status != 200:
                        return None

                    html_content = await resp.text()
                    soup = BeautifulSoup(html_content, "lxml")

                    if "No Results Found." in soup.get_text() or \
                       "No valid results were found" in soup.get_text():
                        return None

                    base = soup.find(
                        "div", class_=f"passage-col passage-col-mobile version-{version}")
                    if not base:
                        base = soup

                    passage_div = base.find("div", class_="passage-text")
                    if passage_div:
                        verse_spans = passage_div.select(".text")
                        if verse_spans:
                            text = ' '.join(span.get_text(
                                separator=' ', strip=True) for span in verse_spans)
                        else:
                            text = passage_div.get_text(
                                separator=' ', strip=True)
                    else:
                        text = base.get_text(separator=' ', strip=True)

                    text = clean_verse_text(text)

                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(text if text else "__EMPTY__")

                    return text if text else None

            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {passage} ({version})")
                raise
            except Exception as e:
                logger.error(
                    f"Error fetching {passage} ({version}): {type(e).__name__}: {e}")
                raise

    async def _process_verse(
        self,
        session: aiohttp.ClientSession,
        book: str,
        chapter: int,
        verse: int
    ) -> Dict[str, Optional[str]]:
        # Determine which translations still need fetching for this verse.
        # Translations already present in self.data are carried over as-is,
        # so a partial verse only re-fetches the truly missing translations.
        already_have: Dict[str, str] = {}
        versions_to_fetch: List[str] = []
        for v in self.versions:
            existing = (
                self.data.get(v, {})
                    .get(book, {})
                    .get(chapter, {})
                    .get(verse)
            )
            if existing is not None:
                already_have[v] = existing
            else:
                versions_to_fetch.append(v)

        tasks = [
            self._fetch_verse_text(session, v, book, chapter, verse)
            for v in versions_to_fetch
        ]
        fetched_results = await asyncio.gather(*tasks, return_exceptions=True)

        verse_data: Dict[str, Optional[str]] = dict(already_have)
        all_failed = not already_have  # start optimistic if we already have some
        for idx, result in enumerate(fetched_results):
            version_code = versions_to_fetch[idx]
            if isinstance(result, Exception):
                verse_data[version_code] = None
            elif result is None:
                verse_data[version_code] = None
            else:
                verse_data[version_code] = result
                all_failed = False

        if all_failed:
            self._log_failed(book, chapter, verse,
                             "All translations returned no data")

        return verse_data

    async def scrape_all(self):
        verses_to_scrape = self._get_verses_to_scrape()
        remaining = len(verses_to_scrape)
        
        # Calculate total work units: verses × translations
        total_work_units = TOTAL_VERSES * len(self.versions)
        
        # Calculate already completed work units
        already_done_count = 0
        for book, chapters in BIBLE_STRUCTURE.items():
            for chapter, vcount in chapters:
                for verse in range(1, vcount + 1):
                    # Count how many translations have this verse
                    for version_code in self.versions:
                        if (version_code in self.data and
                            book in self.data[version_code] and
                            str(chapter) in self.data[version_code][book] and
                            str(verse) in self.data[version_code][book][str(chapter)]):
                            already_done_count += 1
        
        remaining_work_units = total_work_units - already_done_count
        total = total_work_units
        already_done = already_done_count

        if remaining == 0:
            logger.info("No verses to scrape (all done).")
            self._export_versions()
            if self.auto_verify:
                self._auto_verify()
            return

        if already_done > 0:
            logger.info(
                f"Resuming: {already_done:,}/{total:,} verse-translations already completed "
                f"({already_done/total*100:.1f}%)"
            )
        logger.info(
            f"Scraping {remaining:,} verse(s) across {len(self.versions)} translation(s) "
            f"with {self.max_concurrent} concurrent requests..."
        )

        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            start_time = time.time()
            processed = 0
            verses_processed = 0  # Track number of verses (not verse-translations)

            pbar = async_tqdm(
                total=total,
                initial=already_done,
                unit="v-t",  # verse-translations
                desc="Scraping",
                dynamic_ncols=True,
                bar_format="{desc}: {percentage:3.2f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                miniters=1,
                mininterval=0.1
            )

            for i in range(0, remaining, 5):  # Save state every 5 verses
                batch = verses_to_scrape[i:i + 5]

                tasks = [
                    self._process_verse(session, book, ch, v)
                    for book, ch, v in batch
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for idx, result in enumerate(batch_results):
                    book, ch, v = batch[idx]
                    if isinstance(result, Exception):
                        logger.error(
                            f"Batch error for {book} {ch}:{v}: {result}")
                        self._log_failed(book, ch, v, f"Batch error: {result}")
                        continue

                    verse_update_count = 0
                    for version_code, text in result.items():
                        if text:
                            self.data.setdefault(version_code, {})
                            self.data[version_code].setdefault(book, {})
                            self.data[version_code][book].setdefault(str(ch), {})
                            self.data[version_code][book][str(ch)][str(v)] = text
                            verse_update_count += 1

                    self._mark_verse_done(book, ch, v)
                    processed += verse_update_count  # Count each translation as a work unit
                    verses_processed += 1

                    elapsed = time.time() - start_time
                    rate = verses_processed / elapsed if elapsed > 0 else 0
                    remaining_verses = remaining - verses_processed
                    eta = remaining_verses / rate if rate > 0 else 0
                    pbar.set_postfix({
                        "Ref": f"{book} {ch}:{v}",
                        "Rate": f"{rate:.1f} v/s",
                        "ETA": f"{eta/60:.1f}m" if eta < 3600 else f"{eta/3600:.1f}h"
                    })
                    pbar.update(verse_update_count)  # Update by the number of translations fetched

                self._save_state()

            pbar.close()

        logger.info(f"Scraping complete! Processed {verses_processed:,} verses ({processed:,} verse-translations).")
        if self.failed:
            logger.warning(
                f"⚠️ {len(self.failed)} verses failed. Run `--retry-missing` to re‑scrape them.")
            logger.warning(f"   See failed_verses.json for details.")
        else:
            logger.info("✅ No failures recorded.")
        self._export_versions()
        if self.auto_verify:
            self._auto_verify()

    def _auto_verify(self):
        from verify import verify_all, print_verification_report
        results = verify_all(self.data)
        print("\n" + "=" * 60)
        print("AUTO-VERIFICATION REPORT")
        print("=" * 60)
        print_verification_report(results, summary_only=True)

    def _export_versions(self):
        logger.info("Exporting per-version JSON files...")
        book_order = {name: idx for idx,
                      name in enumerate(get_all_book_names())}

        for version_code, books in self.data.items():
            verses_list = []
            for book, chapters in books.items():
                for chapter, verses in chapters.items():
                    for verse_num, text in verses.items():
                        verses_list.append({
                            "book": book,
                            "chapter": chapter,
                            "verse": verse_num,
                            "text": text
                        })

            verses_list.sort(
                key=lambda x: (book_order.get(
                    x["book"], 999), x["chapter"], x["verse"])
            )

            display_name = VERSION_NAMES.get(version_code, version_code)
            safe_folder = sanitize_folder_name(display_name)
            out_dir = os.path.join(self.output_dir, safe_folder)
            os.makedirs(out_dir, exist_ok=True)

            out_file = os.path.join(out_dir, f"{version_code}_bible.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(verses_list, f, indent=2, ensure_ascii=False)

            logger.info(
                f"  ✓ Exported {len(verses_list)} verses to {out_file}")
