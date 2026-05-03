"""Pure-function text and PDF parsing used by the cewler spider.

This module is intentionally lightweight: it has no Scrapy / tld / network
dependency. Both :class:`cewler.spider.CewlerSpider` and the local-file
wordlist generator (``python -m cewler.wordlist_from_files``) call into the
functions here, so the filtering rules have a single source of truth.
"""

from __future__ import annotations

import html
import io
import re
import urllib.parse
from typing import Set, Tuple

try:
    from . import constants
except ImportError:  # When running this file directly
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import constants  # type: ignore


def parse_words_and_emails(
    text: str,
    min_word_length: int = 5,
    lowercase: bool = False,
    without_numbers: bool = False,
) -> Tuple[Set[str], Set[str]]:
    """Apply cewler's text-cleaning + filtering rules to ``text``.

    Returns ``(words, emails)`` as two ``set`` objects. Emails are also
    included in ``words`` (matches existing spider behavior).
    """
    new_words = []
    new_emails = []
    text = html.unescape(text)
    text = urllib.parse.unquote(text)
    text = re.sub(constants.CONTROL_CHARACTERS_TO_FILTER_AWAY, "", text)  # Remove control characters
    text = re.sub(constants.EMOJI_RANGES_TO_FILTER_AWAY, " ", text)  # Remove emojis

    email_list = re.findall(constants.REGEX_EMAIL, text)
    for email in email_list:
        if lowercase:
            email = email.lower()
        new_emails.append(email)
        new_words.append(email)

    text = re.sub(constants.CHARACTERS_TO_FILTER_AWAY, " ", text)  # Filter characters (incl. @, so need this after email extraction)
    text = re.sub(r"\s+", " ", text)  # Replace all spacing with one space
    if lowercase:
        text = text.lower()
    for word in text.split(" "):
        word = word.strip()
        while True:
            found = False
            for c in constants.CHARACTERS_ALLOWED_IN_WORDS_BUT_NOT_IN_START_OR_END:
                if word.startswith(c):
                    word = word[1:]
                    found = True
                if word.endswith(c):
                    word = word[:-1]
                    found = True
            if not found:
                break
        if len(word) >= max(1, min_word_length):
            if without_numbers:
                if not bool(re.search(r'\d', word)):
                    new_words.append(word)
            else:
                new_words.append(word)
    return (set(new_words), set(new_emails))


def parse_pdf_to_text(pdf_body) -> str:
    """Extract text from a PDF.

    ``pdf_body`` may be ``bytes``/``bytearray``, a file-like object, or a
    path-like. Errors are silenced (best-effort), matching the spider's
    historical behavior of not aborting on a single bad page.
    """
    from pypdf import PdfReader  # imported lazily to keep module import cheap

    if isinstance(pdf_body, (bytes, bytearray)):
        reader_input = io.BytesIO(bytes(pdf_body))
    elif hasattr(pdf_body, "read"):
        reader_input = pdf_body
    else:
        reader_input = str(pdf_body)

    pdf_text = ""
    try:
        pdf_reader = PdfReader(reader_input)
        for page in pdf_reader.pages:
            try:
                pdf_text += " " + (page.extract_text() or "")
            except Exception:
                continue
    except Exception:
        pass
    return pdf_text
