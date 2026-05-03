"""Generate a wordlist directly from local files (PDF, TXT, ...).

Thin wrapper around cewler's existing parser and mangling primitives. PDF /
text parsing lives in :mod:`cewler.parsing` (same code path the spider uses
for HTTP responses); password-style permutations live in
:mod:`cewler.mangling`. This module only owns local-file I/O dispatch and the
argparse CLI.

Library entry points
--------------------
- :func:`extract_text_from_file` -- dispatch by extension to cewler's parser.
- For mangling primitives, import :mod:`cewler.mangling` directly.

CLI: ``python -m cewler.wordlist_from_files [files ...] [-o out.txt] [...]``
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable, Set

try:
    from .parsing import parse_pdf_to_text, parse_words_and_emails
    from .mangling import DEFAULT_SUFFIXES, mangle_password_candidates
except ImportError:  # When running this file directly
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from parsing import parse_pdf_to_text, parse_words_and_emails  # type: ignore
    from mangling import DEFAULT_SUFFIXES, mangle_password_candidates  # type: ignore


def extract_text_from_file(path: str) -> str:
    """Read a local file and return its raw text.

    Dispatches ``.pdf`` to :func:`cewler.spider.parse_pdf_to_text` (the same
    function the cewler spider uses for HTTP PDF responses); other extensions
    are best-effort decoded as text.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        with open(path, "rb") as f:
            return parse_pdf_to_text(f.read())
    with open(path, "rb") as f:
        data = f.read()
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cewler-wordlist",
        description="Generate a wordlist from local files (PDF, TXT, ...) "
        "using cewler's filtering rules. Optional password mangling.",
    )
    p.add_argument("files", nargs="+", help="input files (PDF or text)")
    p.add_argument("-o", "--output", help="output file (default: stdout)")
    p.add_argument(
        "-oe",
        "--output-emails",
        help="optional file to write extracted e-mail addresses",
    )
    p.add_argument(
        "-m",
        "--min-word-length",
        type=int,
        default=5,
        help="minimum word length (default: 5)",
    )
    p.add_argument("-l", "--lowercase", action="store_true", help="lowercase all words")
    p.add_argument(
        "-w",
        "--without-numbers",
        action="store_true",
        help="ignore words that contain digits",
    )

    mangle = p.add_argument_group("password mangling (off by default)")
    mangle.add_argument(
        "--mangle",
        action="store_true",
        help="enable mangling (years + simple suffixes; combine with --leet/--caps)",
    )
    mangle.add_argument(
        "--leet", action="store_true", help="also emit leet-substituted variants"
    )
    mangle.add_argument(
        "--caps",
        action="store_true",
        help="also emit lower / UPPER / Capitalized variants",
    )
    mangle.add_argument(
        "--suffix",
        action="append",
        default=[],
        metavar="STR",
        help="append literal suffix(es); repeatable",
    )
    mangle.add_argument(
        "--prefix",
        action="append",
        default=[],
        metavar="STR",
        help="prepend literal prefix(es); repeatable",
    )
    mangle.add_argument(
        "--year-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="append every year in [START, END] inclusive",
    )
    mangle.add_argument(
        "--max-per-word",
        type=int,
        default=64,
        help="cap on candidates emitted per base word (default: 64)",
    )
    mangle.add_argument(
        "--no-default-suffixes",
        action="store_true",
        help="do not add the built-in common suffixes when --mangle is set",
    )
    return p


def main(argv=None) -> int:
    args = _build_arg_parser().parse_args(argv)

    all_words: Set[str] = set()
    all_emails: Set[str] = set()
    for path in args.files:
        if not os.path.isfile(path):
            print(f"warning: not a file, skipping: {path}", file=sys.stderr)
            continue
        text = extract_text_from_file(path)
        if not text:
            print(f"warning: no text extracted from {path}", file=sys.stderr)
            continue
        words, emails = parse_words_and_emails(
            text,
            min_word_length=args.min_word_length,
            lowercase=args.lowercase,
            without_numbers=args.without_numbers,
        )
        all_words.update(words)
        all_emails.update(emails)

    if args.mangle:
        suffixes = list(args.suffix)
        prefixes = list(args.prefix)
        years: Iterable[int] = ()
        if args.year_range:
            start, end = args.year_range
            years = range(min(start, end), max(start, end) + 1)
        if not args.no_default_suffixes and not (
            args.suffix or args.prefix or args.year_range
        ):
            suffixes.extend(DEFAULT_SUFFIXES)
        all_words = set(
            mangle_password_candidates(
                sorted(all_words),
                use_leet=args.leet,
                cap_variants=args.caps,
                suffixes=suffixes,
                prefixes=prefixes,
                years=years,
                max_per_word=args.max_per_word,
            )
        )

    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        for word in sorted(all_words):
            out.write(word + "\n")
    finally:
        if args.output:
            out.close()

    if args.output_emails:
        with open(args.output_emails, "w", encoding="utf-8") as fh:
            for email in sorted(all_emails):
                fh.write(email + "\n")

    print(
        f"words: {len(all_words)}  emails: {len(all_emails)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
