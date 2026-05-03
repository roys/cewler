"""Password-style mangling primitives for use with cewler wordlists.

These helpers are intentionally small and dependency-free so they can be
imported from any cewler entry point or from third-party code without
pulling in Scrapy or pypdf.

Public API
----------
- :data:`DEFAULT_LEET_MAP` -- conservative single-character leet map.
- :data:`DEFAULT_SUFFIXES` -- common numeric / symbolic suffixes.
- :func:`capitalization_variants` -- yield ``word``, lower, UPPER, Capitalized.
- :func:`leet_variants` -- yield single-class leet substitutions of ``word``.
- :func:`mangle_password_candidates` -- combine the above with affixes / years.

The CLI entry point is in :mod:`cewler.wordlist_from_files`.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, Iterator, List, Mapping, Sequence, Set


DEFAULT_LEET_MAP: Dict[str, List[str]] = {
    "a": ["@", "4"],
    "b": ["8"],
    "e": ["3"],
    "i": ["1", "!"],
    "l": ["1"],
    "o": ["0"],
    "s": ["$", "5"],
    "t": ["7"],
}
"""Conservative single-character leet substitutions.

One source character may map to several replacement strings; callers can
override by passing their own mapping to :func:`leet_variants` or
:func:`mangle_password_candidates`.
"""


DEFAULT_SUFFIXES: Sequence[str] = (
    "1", "12", "123", "!", "?", "@", "#", "01", "00", "2024", "2025",
)
"""Common numeric / symbolic suffixes used when mangling is enabled."""


def capitalization_variants(word: str) -> Iterator[str]:
    """Yield up to four capitalization variants of ``word``.

    Order: original, all-lower, ALL-UPPER, Capitalized. Duplicates (e.g. an
    already-lowercase input) are skipped so callers can safely deduplicate
    downstream with :func:`dict.fromkeys`.
    """
    yield word
    if word != word.lower():
        yield word.lower()
    if word != word.upper():
        yield word.upper()
    cap = word[:1].upper() + word[1:].lower()
    if cap != word:
        yield cap


def leet_variants(
    word: str,
    leet_map: Mapping[str, Sequence[str]] = DEFAULT_LEET_MAP,
) -> Iterator[str]:
    """Yield single-character-class leet substitutions of ``word``.

    The original word is yielded first. For each source character class in
    ``leet_map`` that occurs in ``word`` (case-insensitive), every replacement
    string is applied independently to both the lowercased and original forms.

    The single-class policy keeps output bounded; if you want multi-class
    substitution chains, run this iteratively over its own output.
    """
    yield word
    lower = word.lower()
    for src, repls in leet_map.items():
        if src not in lower:
            continue
        for repl in repls:
            yield re.sub(src, repl, lower)
            yield re.sub(src, repl, word)


def mangle_password_candidates(
    words: Iterable[str],
    *,
    use_leet: bool = False,
    cap_variants: bool = False,
    suffixes: Iterable[str] = (),
    prefixes: Iterable[str] = (),
    years: Iterable[int] = (),
    max_per_word: int = 64,
    leet_map: Mapping[str, Sequence[str]] = DEFAULT_LEET_MAP,
) -> Iterator[str]:
    """Generate password-style permutations from a base word iterable.

    Output is deduplicated globally and bounded per base word by
    ``max_per_word`` to keep total list size sane for offline cracking.

    Parameters
    ----------
    words:
        Source words to expand.
    use_leet:
        Apply :func:`leet_variants` to each base word before affixing.
    cap_variants:
        Apply :func:`capitalization_variants` before affixing.
    suffixes / prefixes:
        Literal strings appended / prepended to each variant.
    years:
        Iterable of years; each year is appended as a suffix
        (e.g. ``range(2020, 2027)``).
    max_per_word:
        Hard cap on emitted candidates per base word.
    leet_map:
        Override the default leet mapping if desired.
    """
    seen: Set[str] = set()
    suffix_list = list(suffixes) + [str(y) for y in years]
    prefix_list = list(prefixes)

    for base in words:
        if not base:
            continue
        bases: List[str] = [base]
        if cap_variants:
            bases = list(dict.fromkeys(capitalization_variants(base)))
        if use_leet:
            expanded: List[str] = []
            for b in bases:
                expanded.extend(leet_variants(b, leet_map))
            bases = list(dict.fromkeys(expanded))

        emitted_for_base = 0
        for b in bases:
            candidates: List[str] = [b]
            for s in suffix_list:
                candidates.append(b + s)
            for p in prefix_list:
                candidates.append(p + b)
            for s in suffix_list:
                for p in prefix_list:
                    candidates.append(p + b + s)
            for c in candidates:
                if c in seen:
                    continue
                seen.add(c)
                yield c
                emitted_for_base += 1
                if emitted_for_base >= max_per_word:
                    break
            if emitted_for_base >= max_per_word:
                break
