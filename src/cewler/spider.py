import html
import re
import scrapy
import scrapy.exceptions
import tld
import urllib.parse
import io
from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spidermiddlewares import offsite
from scrapy.spiders import CrawlSpider, Rule
import scrapy.core.downloader.handlers.http
from pypdf import PdfReader

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

    def __init__(self, console, url, file_words=None, file_emails=None, file_urls=None, include_js=False, include_css=False, include_pdf=False, should_lowercase=False, without_numbers=False, min_word_length=5, verbose=False, spider_event_callback=None, stream_to_file=False, *args, **kwargs):
        self.console = console
        self.should_lowercase = should_lowercase
        self.without_numbers = without_numbers
        self.min_word_length = min_word_length
        self.verbose = verbose
        self.spider_event_callback = spider_event_callback
        self.stream_to_file = stream_to_file
        self.words_found = set()
        self.emails_found = set()
        self.urls_parsed = set()
        self.visited_domains = set()
        self.exceptions = []
        self.unsupported_content_types = set()
        self.log_lines = []
        self.last_status = "init"
        self.include_js = include_js
        self.include_css = include_css
        self.include_pdf = include_pdf
        deny_extensions = scrapy.linkextractors.IGNORED_EXTENSIONS
        if self.include_pdf:
            deny_extensions.remove("pdf")
        if self.include_css:
            deny_extensions.remove("css")
        if self.include_js and self.include_css:
            self.link_extractor = LinkExtractor(tags=("a", "area", "script", "link"), attrs=("href", "src"), deny_extensions=deny_extensions)
            self.xpath = constants.XPATH_TEXT_INCLUDE_JAVASCRIPT_AND_CSS
        elif self.include_js:
            self.link_extractor = LinkExtractor(tags=("a", "area", "script"), attrs=("href", "src"), deny_extensions=deny_extensions)
            self.xpath = constants.XPATH_TEXT_INCLUDE_JAVASCRIPT
        elif self.include_css:
            self.link_extractor = LinkExtractor(tags=("a", "area", "link"), attrs=("href", "src"), deny_extensions=deny_extensions)
            self.xpath = constants.XPATH_TEXT_INCLUDE_CSS
        else:
            self.link_extractor = LinkExtractor(deny_extensions=deny_extensions)
            self.xpath = constants.XPATH_TEXT
        try:
            self.rules = (Rule(self.link_extractor, follow=True, callback="parse_item"),)
            super(CewlerSpider, self).__init__(*args, **kwargs)
            self.start_urls = [url]

            self.allowed_domains = [self.get_allowed(url)]
            self.file_words = open(file_words, mode="w") if file_words is not None else None
            self.file_emails = open(file_emails, mode="w") if file_emails is not None else None
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
        # print("get_allowed", url)
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
                self.send_spider_callback()
                for word in self.words_found:
                    self.file_words.write(word)
                    self.file_words.write("\n")
                self.file_words.close()
            if self.file_emails is not None:
                self.last_status = "writing_to_file"
                self.send_spider_callback()
                for email in sorted(self.emails_found):
                    self.file_emails.write(email)
                    self.file_emails.write("\n")
                self.file_emails.close()
            if self.file_urls is not None:
                self.last_status = "writing_to_file"
                self.send_spider_callback()
                for url in sorted(self.urls_parsed):
                    self.file_urls.write(url)
                    self.file_urls.write("\n")
                self.file_urls.close()
        self.last_status = "spider_closed"
        self.send_spider_callback()

    def _get_words_and_emails_from_text(self, text):
        new_words = []
        new_emails = []
        text = html.unescape(text)
        text = urllib.parse.unquote(text)

        email_list = re.findall(constants.REGEX_EMAIL, text)
        for email in email_list:
            if self.should_lowercase:
                email = email.lower()
            new_emails.append(email)
            new_words.append(email)

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
        return (set(new_words), set(new_emails))

    def _get_words_from_text_response(self, text):
        new_words = set()
        new_emails = set()
        try:
            new_words, new_emails = self._get_words_and_emails_from_text(text)
            if len(new_words) > 0:
                if self.file_words is not None and self.stream_to_file:
                    for word in new_words:
                        if word not in self.words_found:
                            self.words_found.add(word)
                            self.file_words.write(word + "\n")
                    self.file_words.flush()
                else:
                    self.words_found.update(new_words)
            if len(new_emails) > 0:
                if self.file_emails is not None and self.stream_to_file:
                    for email in new_emails:
                        if email not in self.emails_found:
                            self.emails_found.add(email)
                            self.file_emails.write(email + "\n")
                    self.file_emails.flush()
                else:
                    self.emails_found.update(new_emails)
        except Exception as e:
            exit(e)
        return new_words

    def _get_words_from_html_response(self, response):
        new_words = set()
        new_emails = set()
        try:
            for item in response.xpath(self.xpath):
                words_and_emails_tuple = self._get_words_and_emails_from_text(item.get())
                new_words.update(words_and_emails_tuple[0])
                new_emails.update(words_and_emails_tuple[1])
            if len(new_words) > 0:
                if self.file_words is not None and self.stream_to_file:
                    for word in new_words:
                        if word not in self.words_found:
                            self.words_found.add(word)
                            self.file_words.write(word + "\n")
                    self.file_words.flush()
                else:
                    self.words_found.update(new_words)
            if len(new_emails) > 0:
                if self.file_emails is not None and self.stream_to_file:
                    for email in new_emails:
                        if email not in self.emails_found:
                            self.emails_found.add(email)
                            self.file_emails.write(email + "\n")
                    self.file_emails.flush()
                else:
                    self.emails_found.update(new_emails)
        except Exception as e:
            exit(e)
        return new_words

    def _get_words_from_pdf(self, pdf_body):
        pdf_text = ""
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_body))
            for page in pdf_reader.pages:
                pdf_text += " " + page.extract_text()
        except Exception:
            pass
        return pdf_text

    def is_supported_text_content_type(self, content_type):
        if "text/plain" in content_type:
            return True
        return False

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
                content_type = headers[b"content-type"][0].decode().lower()
                if "text/html" in content_type:
                    yield {
                        "url": response.url,
                        "title": response.css("title::text").get(),
                        "words:": self._get_words_from_html_response(response),
                    }
                    for item in response.xpath(constants.XPATH_COMMENT):
                        inside_comment = item.get().replace("<!--", "").replace("-->", "")
                        for link in self.link_extractor.extract_links(scrapy.http.TextResponse(url=response.url, body=bytes(inside_comment, encoding="utf-8"))):
                            yield response.follow(link, callback=self.parse_item)
                elif self.is_supported_text_content_type(content_type):
                    yield {
                        "url": response.url,
                        "title": "",
                        "words:": self._get_words_from_text_response(response.text),
                    }
                elif self.include_js and ("script" in content_type or "application/json" in content_type or "application/ld+json" in content_type):
                    yield {
                        "url": response.url,
                        "title": "",
                        "words:": self._get_words_from_text_response(response.text),
                    }
                elif self.include_css and ("text/css" in content_type):
                    yield {
                        "url": response.url,
                        "title": "",
                        "words:": self._get_words_from_text_response(response.text),
                    }
                elif self.include_pdf and ("application/pdf" in content_type):
                    pdf_text = self._get_words_from_pdf(response.body)
                    yield {
                        "url": response.url,
                        "title": "",
                        "words:": self._get_words_from_text_response(pdf_text),
                    }
                else:
                    self.unsupported_content_types.add(content_type)
                    yield {
                        "url": response.url,
                        "title": "",
                        "error": f"Unsupported Content-Type [{b'content-type' in headers.keys()}]"
                    }
            else:
                self.unsupported_content_types.add("Missing Content-Type header")
                yield {
                    "url": response.url,
                    "title": "",
                    "error": f"Skipping because of missing Content-Type"
                }
        except Exception as e:
            self.exceptions.append(e)
            yield {"url": response.url, "title": "", "error": str(e)}
