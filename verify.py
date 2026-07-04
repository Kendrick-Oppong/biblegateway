import json
import os
import sys
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict

from bible_structure import BIBLE_STRUCTURE, TOTAL_VERSES, get_all_book_names


def load_data(data_file: str = "bible_data.json") -> Dict[str, Dict]:
    if not os.path.exists(data_file):
        return {}
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_translation(
    data: Dict[str, Dict[str, Dict[int, Dict[int, str]]]],
    version_code: str
) -> Dict[str, any]:
    missing = []
    extra = []
    total_found = 0
    total_expected = 0

    version_data = data.get(version_code, {})

    for book, chapters in BIBLE_STRUCTURE.items():
        for chapter, vcount in chapters:
            total_expected += vcount
            book_data = version_data.get(book, {})
            chapter_data = book_data.get(chapter, {})
            for verse in range(1, vcount + 1):
                if verse not in chapter_data or not chapter_data[verse]:
                    missing.append((book, chapter, verse))
                else:
                    total_found += 1

    for book, chapters_data in version_data.items():
        if book not in BIBLE_STRUCTURE:
            for chapter, verses_data in chapters_data.items():
                for verse in verses_data:
                    extra.append((book, chapter, verse))
            continue
        for chapter, verses_data in chapters_data.items():
            chapter_info = next((c for c in BIBLE_STRUCTURE[book] if c[0] == chapter), None)
            if not chapter_info:
                for verse in verses_data:
                    extra.append((book, chapter, verse))
                continue
            max_verse = chapter_info[1]
            for verse in verses_data:
                if verse > max_verse:
                    extra.append((book, chapter, verse))

    completeness = (total_found / total_expected * 100) if total_expected > 0 else 0.0

    return {
        "total_missing": len(missing),
        "missing_verses": missing,
        "extra_verses": extra,
        "total_expected": total_expected,
        "total_found": total_found,
        "completeness": completeness,
    }


def verify_all(data: Dict[str, Dict]) -> Dict[str, any]:
    results = {}
    for version_code in data.keys():
        results[version_code] = verify_translation(data, version_code)
    return results


def print_verification_report(results: Dict[str, any], summary_only: bool = False):
    total_missing_all = 0
    total_extra_all = 0

    if not results:
        print("No data found. Run scraper first.")
        return

    for version_code, res in results.items():
        if summary_only:
            print(f"{version_code}: {res['total_found']:,}/{res['total_expected']:,} "
                  f"({res['completeness']:.2f}%) missing={res['total_missing']}")
        else:
            print(f"\n{'='*60}")
            print(f"Translation: {version_code}")
            print(f"{'='*60}")
            print(f"Total expected: {res['total_expected']:,}")
            print(f"Total found:    {res['total_found']:,}")
            print(f"Completeness:   {res['completeness']:.2f}%")
            if res['total_missing'] > 0:
                print(f"\nMissing verses: {res['total_missing']:,}")
                for book, ch, v in res['missing_verses'][:10]:
                    print(f"  - {book} {ch}:{v}")
                if len(res['missing_verses']) > 10:
                    print(f"  ... and {len(res['missing_verses']) - 10} more")
            if res['extra_verses']:
                print(f"\nExtra verses (not in canonical structure): {len(res['extra_verses'])}")
                for book, ch, v in res['extra_verses'][:5]:
                    print(f"  - {book} {ch}:{v}")
                if len(res['extra_verses']) > 5:
                    print(f"  ... and {len(res['extra_verses']) - 5} more")
        total_missing_all += res['total_missing']
        total_extra_all += len(res['extra_verses'])

    if summary_only and len(results) > 1:
        print(f"\nTOTAL: {total_missing_all} missing verses across all translations")
        if total_extra_all:
            print(f"WARNING: {total_extra_all} extra verses found (not in canonical structure)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify scraped Bible data")
    parser.add_argument("--data", default="bible_data.json", help="Data file to verify")
    parser.add_argument("--version", help="Specific translation to verify (e.g., KJV)")
    parser.add_argument("--summary", action="store_true", help="Show only summary (no full details)")
    parser.add_argument("--export-missing", help="Export missing verses to a file (JSON)")
    args = parser.parse_args()

    data = load_data(args.data)
    if not data:
        print(f"Error: No data found in {args.data}. Run scraper first.")
        sys.exit(1)

    if args.version:
        if args.version not in data:
            print(f"Error: Version '{args.version}' not found in data. Available: {', '.join(data.keys())}")
            sys.exit(1)
        results = {args.version: verify_translation(data, args.version)}
    else:
        results = verify_all(data)

    print_verification_report(results, summary_only=args.summary)

    if args.export_missing and results:
        missing_data = {}
        for version_code, res in results.items():
            if res['total_missing'] > 0:
                missing_data[version_code] = [
                    {"book": b, "chapter": c, "verse": v}
                    for b, c, v in res['missing_verses']
                ]
        with open(args.export_missing, "w", encoding="utf-8") as f:
            json.dump(missing_data, f, indent=2)
        print(f"\nExported missing verses to {args.export_missing}")


if __name__ == "__main__":
    main()
