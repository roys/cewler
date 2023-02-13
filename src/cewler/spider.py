import html
import re
import scrapy
import scrapy.exceptions
import tld
from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spidermiddlewares import offsite
from scrapy.spiders import CrawlSpider, Rule
import scrapy.core.downloader.handlers.http

try:
    from . import constants
except ImportError:  # When running this file directly
    import os
    import sys
    sys.path.insert(0, os.path.abspath('.'))
    import constants


class OnlyExactSameDomainSpiderMiddleware(offsite.OffsiteMiddleware):

    def get_host_regex(self, spider):
        regex = super().get_host_regex(spider)
        # Remove optional .* (any subdomains) from regex
        regex = regex.pattern.replace("(.*\.)?", "", 1)
        return re.compile(regex)


class OnlyChildrenSubdomainAndSameDomainSpiderMiddleware(offsite.OffsiteMiddleware):

    def get_host_regex(self, spider):
        return super().get_host_regex(spider)


class AnyParentAndSisterAndSubdomainMiddleware(offsite.OffsiteMiddleware):

    has_altered_allowed_domains = False

    def get_host_regex(self, spider):
        if not self.has_altered_allowed_domains:
            self.has_altered_allowed_domains = True
            tld_obj = tld.get_tld(spider.start_urls[0], as_object=True, fail_silently=True)
            if tld_obj is None:
                # Typically localhost or similar - just keep spider.allowed_domains unaltered
                # TODO: Log something in this case? Or throw and force change of settings?
                pass
            else:
                spider.allowed_domains = [tld_obj.domain + "." + tld_obj.tld]
        regex = super().get_host_regex(spider)
        return re.compile(regex)


class CewlerSpider(CrawlSpider):
    name = "CeWLeR"

    def __init__(self, console, url, file_words=None, file_urls=None, include_js=False, include_css=False, should_lowercase=False, without_numbers=False, min_word_length=5, verbose=False, spider_event_callback=None, stream_to_file=False, *args, **kwargs):
        self.console = console
        self.should_lowercase = should_lowercase
        self.without_numbers = without_numbers
        self.min_word_length = min_word_length
        self.verbose = verbose
        self.spider_event_callback = spider_event_callback
        self.stream_to_file = stream_to_file
        self.words_found = set()
        self.urls_parsed = set()
        self.visited_domains = set()
        self.exceptions = []
        self.unsupported_content_types = set()
        self.log_lines = []
        self.last_status = "init"
        self.include_js = include_js
        self.include_css = include_css
        if self.include_js and self.include_css:
            deny_extensions = scrapy.linkextractors.IGNORED_EXTENSIONS
            deny_extensions.remove("css")
            self.link_extractor = LinkExtractor(tags=("a", "area", "script", "link"), attrs=("href", "src"), deny_extensions=deny_extensions)
            self.xpath = constants.XPATH_TEXT_INCLUDE_JAVASCRIPT_AND_CSS
        elif self.include_js:
            self.link_extractor = LinkExtractor(tags=("a", "area", "script"), attrs=("href", "src"))
            self.xpath = constants.XPATH_TEXT_INCLUDE_JAVASCRIPT
        elif self.include_css:
            deny_extensions = scrapy.linkextractors.IGNORED_EXTENSIONS
            deny_extensions.remove("css")
            self.link_extractor = LinkExtractor(tags=("a", "area", "link"), attrs=("href", "src"), deny_extensions=deny_extensions)
            self.xpath = constants.XPATH_TEXT_INCLUDE_CSS
        else:
            self.link_extractor = LinkExtractor()
            self.xpath = constants.XPATH_TEXT
        try:
            self.rules = (Rule(self.link_extractor, follow=True, callback="parse_item"),)
            super(CewlerSpider, self).__init__(*args, **kwargs)
            self.start_urls = [url]

            self.allowed_domains = [self.get_allowed(url)]
            self.file_words = open(file_words, mode="w") if file_words is not None else None
            self.file_urls = open(file_urls, mode="w") if file_urls is not None else None
        except Exception:
            self.console.print_exception(show_locals=False)
            raise scrapy.exceptions.CloseSpider()

    def parse_start_url(self, response):
        return self.parse_item(response)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CewlerSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(spider.request_reached_downloader, signal=signals.request_reached_downloader)
        # crawler.signals.connect(spider.signal,signal=signals.engine_started)
        # crawler.signals.connect(spider.signal,signal=signals.item_scraped)
        crawler.signals.connect(spider.engine_stopped, signal=signals.engine_stopped)
        return spider

    def get_allowed(self, url):
        #print("get_allowed", url)
        return re.findall("^(?:https?:\/\/)?(?:[^@\/\n]+@)?([^:\/\n]+)", url)[0]

    def send_spider_callback(self):
        if self.spider_event_callback is not None:
            self.spider_event_callback(
                {
                    "stats": self.crawler.stats.get_stats(),
                    "words": self.words_found,
                    "domains": self.visited_domains,
                    "status": self.last_status,
                    "unsupported_content_types": self.unsupported_content_types,
                    "exceptions": self.exceptions
                }
            )

    def request_reached_downloader(self, request, spider):
        self.last_status = ("request_reached_downloader", request.url)
        self.send_spider_callback()

    def engine_stopped(self):
        self.last_status = "engine_stopped"
        self.send_spider_callback()

    def spider_closed(self, spider):
        self.words_found = sorted(self.words_found)
        if not self.stream_to_file:
            if self.file_words is not None:
                self.last_status = "writing_to_file"
                for word in self.words_found:
                    self.file_words.write(word)
                    self.file_words.write("\n")
                self.file_words.close()
            if self.file_urls is not None:
                self.last_status = "writing_to_file"
                for url in sorted(self.urls_parsed):
                    self.file_urls.write(url)
                    self.file_urls.write("\n")
                self.file_urls.close()
        self.last_status = "spider_closed"
        self.send_spider_callback()

    def _get_words_from_text(self, text):
        new_words = []
        text = html.unescape(text)
        text = re.sub(constants.CHARACTERS_TO_FILTER_AWAY, " ", text)  # Filter characters
        text = re.sub("\s+", " ", text)  # Replace all spacing with one space
        if self.should_lowercase:
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
            if len(word) >= max(1, self.min_word_length):
                if self.without_numbers:
                    if not bool(re.search(r'\d', word)):
                        new_words.append(word)
                else:
                    new_words.append(word)
        return set(new_words)

    def _get_words_from_text_response(self, response):
        new_words = set()
        try:
            new_words = self._get_words_from_text(response.text)
            if len(new_words) > 0:
                if self.file_words is not None and self.stream_to_file:
                    for word in new_words:
                        if word not in self.words_found:
                            self.words_found.add(word)
                            self.file_words.write(word + "\n")
                    self.file_words.flush()
                else:
                    self.words_found.update(new_words)
        except Exception as e:
            exit(e)
        return new_words

    def _get_words_from_html_response(self, response):
        new_words = set()
        try:
            for item in response.xpath(self.xpath):
                new_words.update(self._get_words_from_text(item.get()))
            if len(new_words) > 0:
                if self.file_words is not None and self.stream_to_file:
                    for word in new_words:
                        if word not in self.words_found:
                            self.words_found.add(word)
                            self.file_words.write(word + "\n")
                    self.file_words.flush()
                else:
                    self.words_found.update(new_words)
        except Exception as e:
            exit(e)
        return new_words

    def parse_item(self, response):
        try:
            if self.stream_to_file and self.file_urls is not None:
                if response.url not in self.urls_parsed:
                    self.urls_parsed.add(response.url)
                    self.file_urls.write(response.url + "\n")
                self.file_urls.flush()
            else:
                self.urls_parsed.add(response.url)
            headers = {key.lower(): value for key, value in response.headers.items()}
            if (b"content-type" in headers.keys()):
                tld_obj = tld.get_tld(response.url, as_object=True, fail_silently=True)
                if tld_obj is not None:
                    self.visited_domains.add(tld_obj.subdomain + "." + tld_obj.domain + "." + tld_obj.tld)
                content_type = headers[b"content-type"][0]
                if (b"text/html" in content_type):
                    yield {
                        "url": response.url,
                        "title": response.css("title::text").get(),
                        "words:": self._get_words_from_html_response(response),
                    }
                    for item in response.xpath(constants.XPATH_COMMENT):
                        inside_comment = item.get().replace("<!--", "").replace("-->", "")
                        for link in self.link_extractor.extract_links(scrapy.http.TextResponse(url=response.url, body=bytes(inside_comment, encoding="utf-8"))):
                            yield response.follow(link, callback=self.parse_item)
                elif b"text/plain" in content_type:
                    yield {
                        "url": response.url,
                        "title": "",
                        "words:": self._get_words_from_text_response(response),
                    }
                elif self.include_js and (b"script" in content_type or b"application/json" in content_type or b"application/ld+json" in content_type):
                    yield {
                        "url": response.url,
                        "title": "",
                        "words:": self._get_words_from_text_response(response),
                    }
                elif self.include_css and (b"text/css" in content_type):
                    yield {
                        "url": response.url,
                        "title": "",
                        "words:": self._get_words_from_text_response(response),
                    }
                else:
                    try:
                        self.unsupported_content_types.add(content_type.decode("utf-8"))
                    except UnicodeDecodeError:
                        self.unsupported_content_types.add(str(content_type))
                    yield {
                        "url": response.url,
                        "title": "",
                        "error": f"Unsupported Content-Type [{b'content-type' in headers.keys()}]"
                    }
            else:
                yield {
                    "url": response.url,
                    "title": "",
                    "error": f"Skipping because of Content-Type [{b'content-type' in headers.keys()}]"
                }
        except Exception as e:
            self.exceptions.append(e)
            yield {"url": response.url, "title": "", "error": str(e)}
