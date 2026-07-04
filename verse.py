import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import re
import html

import version as ver


def clean_verse_text(text: str) -> str:
    """Same cleaning function as in scraper.py – kept here for consistency."""
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


def verse(passage: str, version: Optional[str] = None) -> Dict[str, Any]:
    if version is None:
        version = ver.ENG_KING_JAMES_VERSION

    url = "https://www.biblegateway.com/passage/"
    params = {
        "search": passage,
        "version": version,
        "interface": "print"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    text = soup.get_text()
    if "No Results Found." in text or \
       "No valid results were found" in text:
        return {"book": "No results found", "verses": []}

    table = soup.select_one(".passage-table")
    if not table:
        table = soup

    base = table.find(
        "div", class_=f"passage-col passage-col-mobile version-{version}")
    if not base:
        base = table

    book_elem = base.find("div", class_="dropdown-display-text")
    book = book_elem.get_text(strip=True) if book_elem else ""

    passage_div = base.find("div", class_="passage-text")
    if passage_div:
        verse_spans = passage_div.select(".text")
        if verse_spans:
            verses = [clean_verse_text(span.get_text(
                separator=' ', strip=True)) for span in verse_spans]
        else:
            verses = [clean_verse_text(
                passage_div.get_text(separator=' ', strip=True))]
    else:
        verses = [clean_verse_text(base.get_text(separator=' ', strip=True))]

    return {
        "book": book,
        "verses": verses
    }
