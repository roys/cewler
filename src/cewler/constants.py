DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
XPATH_TEXT = "//comment() | //text()[not (ancestor-or-self::script or ancestor-or-self::style)]"
XPATH_TEXT_INCLUDE_JAVASCRIPT = "//comment() | //text()[not (ancestor-or-self::style)]"
XPATH_TEXT_INCLUDE_CSS = "//comment() | //text()[not (ancestor-or-self::script)]"
XPATH_TEXT_INCLUDE_JAVASCRIPT_AND_CSS = "//comment() | //text()"
XPATH_COMMENT = "//comment()"
CHARACTERS_TO_FILTER_AWAY = '[\(\),./"\"?!“”‘’´:\{\}\[\]«»\*…•‹≈=■◦☀️„|_~✓+<>@;]'
CHARACTERS_ALLOWED_IN_WORDS_BUT_NOT_IN_START_OR_END = "'ˈ-–━—&"
