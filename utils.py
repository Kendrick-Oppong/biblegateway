# Book detection for audio

def detect_book(book_and_chapter: str) -> str:
    """Convert full book name to BibleGateway's abbreviation (for audio URLs)."""
    b = book_and_chapter.replace(" ", "").lower()
    book = "gen"
    list_books = [
        "gen", "exod", "lev", "num", "deut", "josh", "judg", "ruth",
        "1sam", "2sam", "1kgs", "2kgs", "1chr", "2chr", "ezra", "neh",
        "esth", "job", "ps", "prov", "eccl", "song", "isa", "jer",
        "lam", "ezek", "dan", "hos", "joel", "amos", "obad", "jonah",
        "mic", "nah", "hab", "zeph", "hag", "zech", "mal",
        "matt", "mark", "luke", "john", "acts", "rom",
        "1cor", "2cor", "gal", "eph", "phil", "col",
        "1thess", "2thess", "1tim", "2tim", "titus", "phlm",
        "heb", "jas", "1pet", "2pet", "1john", "2john", "3john",
        "jude", "rev"
    ]
    for abbr in list_books:
        if b.startswith(abbr):
            book = abbr
            break
    # Special overrides
    if b.startswith("1king"):
        book = "1kgs"
    elif b.startswith("2king"):
        book = "2kgs"
    elif b.startswith("philemon"):
        book = "phlm"
    elif b.startswith("james"):
        book = "jas"
    return book
