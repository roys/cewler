DEFAULT_USER_AGENT                    = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
XPATH_TEXT                            = "//comment() | //a[starts-with(@href, 'mailto')] | //meta[@name]/@content | //text()[not (ancestor-or-self::script or ancestor-or-self::style)]"
XPATH_TEXT_INCLUDE_JAVASCRIPT         = "//comment() | //a[starts-with(@href, 'mailto')] | //meta[@name]/@content | //text()[not (ancestor-or-self::style)]"
XPATH_TEXT_INCLUDE_CSS                = "//comment() | //a[starts-with(@href, 'mailto')] | //meta[@name]/@content | //text()[not (ancestor-or-self::script)]"
XPATH_TEXT_INCLUDE_JAVASCRIPT_AND_CSS = "//comment() | //a[starts-with(@href, 'mailto')] | //meta[@name]/@content | //text()"
XPATH_COMMENT                         = "//comment()"
CHARACTERS_TO_FILTER_AWAY = '[\(\),./"\"?!“”‘’´`:\{\}\[\]«»\*…•‹≈=■◦☀️„|_~✓+<>@;￼\\\\]|&&|--'
CHARACTERS_ALLOWED_IN_WORDS_BUT_NOT_IN_START_OR_END = "'ˈ-–━—&"
# It's pretty impossible to use regex for emails (https://stackoverflow.com/a/201378/467650 ), so we'll just keep it simple with this one:
REGEX_EMAIL = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
