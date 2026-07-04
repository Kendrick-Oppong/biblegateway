import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

from audio_version import KJV_PAUL_MIMS
from utils import detect_book


def audio(book_and_chapter: str, audio_version: Optional[str] = None) -> Dict[str, Any]:
    if audio_version is None:
        audio_version = KJV_PAUL_MIMS

    if not audio_version.startswith("audio"):
        return {
            "result_code": 404,
            "mp3": "Undefined audio, please read the documentation."
        }

    parts = audio_version.split(" ", 1)
    if len(parts) < 2:
        return {
            "result_code": 404,
            "mp3": "Invalid audio version format."
        }
    vers = parts[1]

    book = detect_book(book_and_chapter)
    tokens = book_and_chapter.split()
    chapter = tokens[1] if len(tokens) >= 2 else "1"

    audio_url = f"https://www.biblegateway.com/audio/{vers}/{book}.{chapter}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(audio_url, headers=headers)
    if resp.status_code != 200:
        return {
            "result_code": resp.status_code,
            "mp3": "Audio not found."
        }

    soup = BeautifulSoup(resp.text, "lxml")

    audio_elem = soup.select_one("#audio-player-element source")
    mp3_url = audio_elem["src"] if audio_elem and audio_elem.has_attr("src") else ""

    copyright_elem = soup.find("div", class_="copyright-text")
    copyright_text = copyright_elem.get_text(strip=True) if copyright_elem else ""

    return {
        "result_code": 200,
        "mp3": mp3_url,
        "copyright": copyright_text
    }
