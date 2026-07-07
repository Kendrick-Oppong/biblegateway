#!/usr/bin/env python3
"""
BibleGateway Scraper CLI
Full-featured: scrape, resume, retry, verify, export.

Usage:
    python cli.py -v KJV NIV -o versions --resume
    python cli.py --verify --verify-version KJV --summary-only
    python cli.py -v KJV --auto-verify
    python cli.py --scrape-all --resume
"""

import argparse
import asyncio
import json
import logging
import sys
import os
from typing import List, Optional

from scraper import BibleGatewayScraper
from verify import load_data, verify_all, verify_translation, print_verification_report
from version import (
    ENG_KING_JAMES_VERSION,
    ENG_NEW_INTERNATIONAL_VERSION,
    ENG_ENLISH_STANDARD_VERSION,
    ENG_NEW_LIVING_TRANSLATION,
    TAG_ANG_DATING_BIBLIYA_1905,
    # All 58 translation constants
    CEB_ANG_PULONG_SA_DIOS,
    ENG_KJV_21,
    ENG_AMERICAN_STANDARD_VERSION,
    ENG_AMPLIFIED_BIBLE,
    ENG_AMPLIFIED_BIBLE_CLASSIC,
    ENG_BRG_BIBLE,
    ENG_CHRISTIAN_STANDARD_BIBLE,
    ENG_COMMON_ENLISH_BIBLE,
    ENG_COMPLETE_JEWISH_BIBLE,
    ENG_CONTEMPORARY_ENGLISH_VERSION,
    ENG_DARBY_TRANSLATION,
    ENG_DISIPLES_LITERAL_NEW_TESTAMENT,
    ENG_DOUAY_RHEIMS_1899,
    ENG_EASY_TO_READ_VERSION,
    ENG_EVANGELICAL_HERITAGE_VERSION,
    ENG_ENLISH_STANDARD_VERSION_ANGLICISED,
    ENG_EXPANDED_BIBLE,
    ENG_1599_GENEVA_BIBLE,
    ENG_GODS_WORD_TRANSLATION,
    ENG_GOOD_NEWS_TRANSLATION,
    ENG_HOLMAN_CHRISTIAN_STANDARD_BIBLE,
    ENG_INTERNATIONAL_CHILDRENS_BIBLE,
    ENG_INTERNATIONAL_STANDARD_VERSION,
    ENG_JB_PHILLIPS_NEW_TESTAMENT,
    ENG_JUBILEE_BIBLE_2000,
    ENG_AUTHORIZED_KING_JAMES_VERSION,
    ENG_LEXHAM_ENGLISH_BIBLE,
    ENG_LIVING_BIBLE,
    ENG_THE_MESSAGE,
    ENG_MODERN_ENGLISH_VERSION,
    ENG_MOUNCE_REVERSE_INTERLINEAR_NEW_TESTAMENT,
    ENG_NAMES_OF_GOD_BIBLE,
    ENG_NEW_AMERICAN_BIBLE_REVISED_EDITION,
    ENG_NEW_AMERICAN_STANDARD_BIBLE,
    ENG_NEW_AMERICAN_STANDARD_BIBLE_1995,
    ENG_NEW_CATHOLIC_BIBLE,
    ENG_NEW_CENTURY_VERSION,
    ENG_NEW_ENGLISH_TRANSLATION,
    ENG_NEW_INTERNATIONAL_READERS_VERSION,
    ENG_NEW_INTERNATIONAL_VERSION_UK,
    ENG_NEW_KING_JAMES_VERSION,
    ENG_NEW_LIFE_VERSION,
    ENG_NEW_MATTHEW_BIBLE,
    ENG_NEW_REVISED_STANDARD_VERSION_ANGLICISED,
    ENG_NEW_REVISED_STANDARD_VERSION_ANGLICISED_CATHOLIC_EDITION,
    ILO_ANG_PULONG_SANG_DIOS_HLGN,
    TAG_ANG_BAGONG_TIPAN,
    TAG_ANG_BIBLIA_1978,
    TAG_ANG_BIBLIA_2001,
    TAG_ANG_SALITA_NG_DIYOS_TCB,
    TAG_ANG_SALITA_NG_DIYOS,
    TAG_MAGANDANG_BALITA,
    TAG_MAGANDANG_BALITA_DC,
)

# Map short names (lowercase) to actual BibleGateway codes
COMMON_VERSIONS = {
    "kjv": ENG_KING_JAMES_VERSION,
    "niv": ENG_NEW_INTERNATIONAL_VERSION,
    "esv": ENG_ENLISH_STANDARD_VERSION,
    "nlt": ENG_NEW_LIVING_TRANSLATION,
    "tag1905": TAG_ANG_DATING_BIBLIYA_1905,
}

# Complete list of all available translations (used by --scrape-all)
ALL_TRANSLATIONS = [
    CEB_ANG_PULONG_SA_DIOS,
    ENG_KJV_21,
    ENG_AMERICAN_STANDARD_VERSION,
    ENG_AMPLIFIED_BIBLE,
    ENG_AMPLIFIED_BIBLE_CLASSIC,
    ENG_BRG_BIBLE,
    ENG_CHRISTIAN_STANDARD_BIBLE,
    ENG_COMMON_ENLISH_BIBLE,
    ENG_COMPLETE_JEWISH_BIBLE,
    ENG_CONTEMPORARY_ENGLISH_VERSION,
    ENG_DARBY_TRANSLATION,
    ENG_DISIPLES_LITERAL_NEW_TESTAMENT,
    ENG_DOUAY_RHEIMS_1899,
    ENG_EASY_TO_READ_VERSION,
    ENG_EVANGELICAL_HERITAGE_VERSION,
    ENG_ENLISH_STANDARD_VERSION,
    ENG_ENLISH_STANDARD_VERSION_ANGLICISED,
    ENG_EXPANDED_BIBLE,
    ENG_1599_GENEVA_BIBLE,
    ENG_GODS_WORD_TRANSLATION,
    ENG_GOOD_NEWS_TRANSLATION,
    ENG_HOLMAN_CHRISTIAN_STANDARD_BIBLE,
    ENG_INTERNATIONAL_CHILDRENS_BIBLE,
    ENG_INTERNATIONAL_STANDARD_VERSION,
    ENG_JB_PHILLIPS_NEW_TESTAMENT,
    ENG_JUBILEE_BIBLE_2000,
    ENG_KING_JAMES_VERSION,
    ENG_AUTHORIZED_KING_JAMES_VERSION,
    ENG_LEXHAM_ENGLISH_BIBLE,
    ENG_LIVING_BIBLE,
    ENG_THE_MESSAGE,
    ENG_MODERN_ENGLISH_VERSION,
    ENG_MOUNCE_REVERSE_INTERLINEAR_NEW_TESTAMENT,
    ENG_NAMES_OF_GOD_BIBLE,
    ENG_NEW_AMERICAN_BIBLE_REVISED_EDITION,
    ENG_NEW_AMERICAN_STANDARD_BIBLE,
    ENG_NEW_AMERICAN_STANDARD_BIBLE_1995,
    ENG_NEW_CATHOLIC_BIBLE,
    ENG_NEW_CENTURY_VERSION,
    ENG_NEW_ENGLISH_TRANSLATION,
    ENG_NEW_INTERNATIONAL_READERS_VERSION,
    ENG_NEW_INTERNATIONAL_VERSION,
    ENG_NEW_INTERNATIONAL_VERSION_UK,
    ENG_NEW_KING_JAMES_VERSION,
    ENG_NEW_LIFE_VERSION,
    ENG_NEW_LIVING_TRANSLATION,
    ENG_NEW_MATTHEW_BIBLE,
    ENG_NEW_REVISED_STANDARD_VERSION_ANGLICISED,
    ENG_NEW_REVISED_STANDARD_VERSION_ANGLICISED_CATHOLIC_EDITION,
    ILO_ANG_PULONG_SANG_DIOS_HLGN,
    TAG_ANG_BAGONG_TIPAN,
    TAG_ANG_BIBLIA_1978,
    TAG_ANG_BIBLIA_2001,
    TAG_ANG_DATING_BIBLIYA_1905,
    TAG_ANG_SALITA_NG_DIYOS_TCB,
    TAG_ANG_SALITA_NG_DIYOS,
    TAG_MAGANDANG_BALITA,
    TAG_MAGANDANG_BALITA_DC,
]


def resolve_versions(version_list: List[str]) -> List[str]:
    resolved = []
    for v in version_list:
        lower = v.lower()
        resolved.append(COMMON_VERSIONS.get(lower, v.upper()))
    return resolved


def main():
    parser = argparse.ArgumentParser(
        description="Async BibleGateway Full‑Bible Scraper with Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape specific translations
  python cli.py -v KJV NIV -o versions --resume

  # Scrape ALL translations
  python cli.py --scrape-all --resume --max-concurrent 50

  # Verify completeness
  python cli.py --verify --verify-version KJV --summary-only

  # Scrape with auto-verify
  python cli.py -v KJV --auto-verify --max-concurrent 30

  # Retry missing verses only
  python cli.py -v KJV --retry-missing
        """
    )

    # Scraping options
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument(
        "-v", "--versions",
        nargs="+",
        help="List of version codes or short names (e.g., KJV NIV ESV tag1905). "
             "Short names: kjv, niv, esv, nlt, tag1905"
    )
    version_group.add_argument(
        "--scrape-all",
        action="store_true",
        help="Scrape ALL available translations (50+ versions)"
    )

    parser.add_argument(
        "-o", "--output",
        default="versions",
        help="Output directory for per‑version JSON files (default: versions/)"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="Resume from last checkpoint (progress saved automatically)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete all progress and start fresh (ignores existing data)"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore HTML cache and re‑download all pages"
    )
    parser.add_argument(
        "--retry-missing",
        action="store_true",
        help="Only retry verses that are missing from all translations"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=20,
        help="Maximum concurrent HTTP requests (default: 20, recommended: 50)"
    )
    parser.add_argument(
        "--auto-verify",
        action="store_true",
        help="Automatically verify completeness after scraping"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # Failure log commands
    parser.add_argument(
        "--show-failed",
        action="store_true",
        help="Show the list of failed verses from the last scrape (from failed_verses.json)"
    )
    parser.add_argument(
        "--clear-failed",
        action="store_true",
        help="Clear the failed_verses.json file (use after retrying or if you don't care)"
    )

    # Verification options
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification on existing data (does not scrape)"
    )
    parser.add_argument(
        "--verify-version",
        help="When verifying, check only this translation (e.g., KJV)"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="When verifying, show only a summary (no full missing lists)"
    )
    parser.add_argument(
        "--data-file",
        default="bible_data.json",
        help="Data file for verification (default: bible_data.json)"
    )
    parser.add_argument(
        "--export-missing",
        help="Export missing verses to a JSON file (only works with --verify)"
    )
    parser.add_argument(
        "--export-versions",
        action="store_true",
        help="Export individual translation JSON files from bible_data.json"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # --- Handle --show-failed and --clear-failed ---
    if args.show_failed:
        failed_file = "failed_verses.json"
        if not os.path.exists(failed_file):
            print("No failed verses file found.")
            return
        with open(failed_file, "r", encoding="utf-8") as f:
            failed = json.load(f)
        if not failed:
            print("No failed verses recorded.")
            return
        print(f"\n📋 Failed verses ({len(failed)} total):")
        for key, error in sorted(failed.items()):
            book, ch, v = key.split("_")
            print(f"  - {book} {ch}:{v}  → {error}")
        return

    if args.clear_failed:
        failed_file = "failed_verses.json"
        if os.path.exists(failed_file):
            os.remove(failed_file)
            print("✅ Cleared failed_verses.json")
        else:
            print("No failed_verses.json file to clear.")
        return

    # --- EXPORT VERSIONS MODE ---
    if args.export_versions:
        from bible_structure import get_all_book_names
        from translations import VERSION_NAMES, sanitize_folder_name
        
        # Load bible_data.json
        try:
            with open("bible_data.json", "r", encoding="utf-8") as f:
                bible_data = json.load(f)
        except FileNotFoundError:
            logger.error("bible_data.json not found!")
            sys.exit(1)
        
        logger.info("Exporting per-version JSON files...")
        book_order = {name: idx for idx, name in enumerate(get_all_book_names())}
        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)
        
        for version_code, books in bible_data.items():
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
            
            # Sort by book order, then chapter, then verse
            verses_list.sort(
                key=lambda x: (book_order.get(x["book"], 999), int(x["chapter"]), int(x["verse"]))
            )
            
            display_name = VERSION_NAMES.get(version_code, version_code)
            safe_folder = sanitize_folder_name(display_name)
            out_dir = os.path.join(output_dir, safe_folder)
            os.makedirs(out_dir, exist_ok=True)
            
            out_file = os.path.join(out_dir, f"{version_code}_bible.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(verses_list, f, indent=2, ensure_ascii=False)
            
            logger.info(f"  ✓ Exported {len(verses_list):,} verses to {out_file}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Export complete! Exported {len(bible_data)} translations.")
        logger.info(f"{'='*60}")
        return

    # --- VERIFICATION MODE ---
    if args.verify:
        data = load_data(args.data_file)
        if not data:
            logger.error(
                f"No data found in {args.data_file}. Run scraper first.")
            sys.exit(1)

        if args.verify_version:
            if args.verify_version not in data:
                logger.error(
                    f"Version '{args.verify_version}' not found in data. "
                    f"Available: {', '.join(data.keys())}"
                )
                sys.exit(1)
            results = {args.verify_version: verify_translation(
                data, args.verify_version)}
        else:
            results = verify_all(data)

        print_verification_report(results, summary_only=args.summary_only)

        if args.export_missing and results:
            missing_data = {}
            for version_code, res in results.items():
                if res["total_missing"] > 0:
                    missing_data[version_code] = [
                        {"book": b, "chapter": c, "verse": v}
                        for b, c, v in res["missing_verses"]
                    ]
            with open(args.export_missing, "w", encoding="utf-8") as f:
                json.dump(missing_data, f, indent=2)
            logger.info(f"Exported missing verses to {args.export_missing}")

        return

    # --- SCRAPING MODE ---
    # Determine which versions to scrape
    if args.scrape_all:
        versions = ALL_TRANSLATIONS
        logger.info(f"Scraping ALL {len(versions)} translations")
    elif args.versions:
        try:
            versions = resolve_versions(args.versions)
            logger.info(f"Target versions: {', '.join(versions)}")
        except KeyError as e:
            logger.error(f"Unknown version alias: {e}")
            sys.exit(1)
    else:
        versions = [ENG_KING_JAMES_VERSION]
        logger.info(
            "No versions specified. Defaulting to KJV. Use -v or --scrape-all for more.")

    logger.info(f"Output directory: {args.output}")
    logger.info(f"Concurrency: {args.max_concurrent}")

    # Overwrite protection
    if not args.overwrite and not args.resume and not args.retry_missing:
        progress_file = "scraper_progress.json"
        data_file = "bible_data.json"
        found_files = []

        if os.path.exists(progress_file):
            found_files.append(f"progress: {os.path.abspath(progress_file)}")
        if os.path.exists(data_file):
            found_files.append(f"data: {os.path.abspath(data_file)}")

        if found_files:
            logger.warning("=" * 60)
            logger.warning("Existing progress or data found!")
            for f in found_files:
                logger.warning(f"  → {f}")
            logger.warning("To resume:    python cli.py --resume")
            logger.warning("To overwrite: python cli.py --overwrite")
            logger.warning("=" * 60)
            if sys.stdin.isatty():
                response = input(
                    "Resume [r], Overwrite [o], or Abort [a]? ").strip().lower()
                if response == 'r':
                    args.resume = True
                elif response == 'o':
                    args.overwrite = True
                else:
                    logger.info("Aborted.")
                    sys.exit(0)
            else:
                logger.error(
                    "Non-interactive session. Use --resume or --overwrite explicitly.")
                sys.exit(1)

    # Instantiate the scraper
    scraper = BibleGatewayScraper(
        versions=versions,
        output_dir=args.output,
        max_concurrent=args.max_concurrent,
        resume=args.resume,
        overwrite=args.overwrite,
        force_refresh=args.force_refresh,
        retry_missing=args.retry_missing,
        auto_verify=args.auto_verify,
    )
    try:
        asyncio.run(scraper.scrape_all())
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Progress saved.")
        scraper._save_state()
        sys.exit(1)


if __name__ == "__main__":
    main()
