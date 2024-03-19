#!/usr/bin/python3
import argparse
import logging
import math
import sys
import textwrap
import time

from rich import print
from rich.console import *
from rich.console import Console
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from scrapy.crawler import CrawlerProcess

try:
    from . import constants
    from . import spider
    spider_package = "cewler."
except ImportError:  # When running this file directly
    sys.path.insert(0, os.path.abspath('.'))
    import constants
    import spider
    spider_package = ""


__author__ = "Roy Solberg"
__version__ = "1.2.0"
__program__ = "CeWLeR"
__description__ = "Custom Word List generator Redefined"


class Cewler:

    def __init__(self):
        self.live = None
        self.static_ui_lines = None
        self.console = Console()
        self.longest_status_text = 0
        self.is_verbose_output = False
        self.last_event_received = None

    def get_parsed_args_and_init_parser(self):
        parser = argparse.ArgumentParser(prog=__program__.lower(), allow_abbrev=False, description=f"{__program__} v.{__version__} - {__description__}", epilog="Visit https://github.com/roys/cewler for more information")

        parser.add_argument("url", help="URL to start crawling from")
        parser.add_argument("-d", "--depth", type=int, default=2, help="directory path depth to crawl, 0 for unlimited (default: 2)")
        parser.add_argument("-css", "--include-css", action="store_true", help="include CSS from external files and <style> tags")
        parser.add_argument("-js", "--include-js", action="store_true", help="include JavaScript from external files and <script> tags")
        parser.add_argument("-pdf", "--include-pdf", action="store_true", help="include text from PDF files")
        parser.add_argument("-l", "--lowercase", action="store_true", help="lowercase all parsed words")
        parser.add_argument("-m", "--min-word-length", type=int, default=5, help="minimum word length to include (default: 5)")
        parser.add_argument("-o", "--output", help="file were to stream and store wordlist instead of screen (default: screen)")
        parser.add_argument("-oe", "--output-emails", help="file were to stream and store e-mail addresses found (they will always be outputted in the wordlist)")
        parser.add_argument("-ou", "--output-urls", help="file were to stream and store URLs visited (default: not outputted)")
        parser.add_argument("-r", "--rate", type=int, default=20, help="requests per second (default: 20)")
        parser.add_argument("-s", "--subdomain_strategy", choices=["all", "children", "exact"], default="exact", help="allow crawling [all] domains, including children and siblings, only [exact] the same (sub)domain (default), or same domain and any belonging [children]")
        parser.add_argument("--stream", action="store_true", default=False, help="writes to file after each request (may produce duplicates because of threading) (default: false)")
        parser.add_argument("-u", "--user-agent", default=constants.DEFAULT_USER_AGENT, help=f"User-Agent header to send (default: {constants.DEFAULT_USER_AGENT})")
        parser.add_argument("-v", "--verbose", action="store_true", help="A bit more detailed output")
        parser.add_argument("-w", "--without-numbers", action="store_true", help="ignore words are numbers or contain numbers")

        args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
        if "://" not in args.url:  # Missing scheme in request url - let try to help out the user by prefixing it with http
            args.url = f"http://{args.url}"
        if args.stream and args.output is None:
            exit("cewler: error: Argument --stream cannot be used without a file specified with --output")
        return args

    def get_scrapy_settings_and_init_logging(self, user_agent, depth_limit, reqs_per_sec, subdomain_strategy):
        """ Sets up scrapy logging and returns necessary settings object """
        logging.getLogger("scrapy").setLevel(logging.ERROR)
        logging.getLogger("scrapy").propagate = False

        if subdomain_strategy == "all":
            offsite_class = f"{spider_package}spider.AnyParentAndSisterAndSubdomainMiddleware"
        elif subdomain_strategy == "children":
            offsite_class = f"{spider_package}spider.OnlyChildrenSubdomainAndSameDomainSpiderMiddleware"
        else:  # "exact"
            offsite_class = f"{spider_package}spider.OnlyExactSameDomainSpiderMiddleware"

        middleware_settings = {
            "scrapy.spidermiddlewares.offsite.OffsiteMiddleware": None,
            offsite_class: 1337
        }

        return {
            # https://docs.scrapy.org/en/latest/topics/settings.html
            "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
            "USER_AGENT": user_agent,
            "DEPTH_LIMIT": depth_limit,
            "DOWNLOAD_DELAY": 1/reqs_per_sec,
            "SPIDER_MIDDLEWARES": middleware_settings,
            "HTTPERROR_ALLOW_ALL": True
            # "CONCURRENT_REQUESTS": 16
            # "CONCURRENT_REQUESTS_PER_DOMAIN": 8
            # "CONCURRENT_REQUESTS_PER_IP": 0
            # "CONCURRENT_REQUESTS": 16
        }

    def on_spider_event(self, event):
        """ Callback from spider with stats and other events """
        self.last_event_received = event
        if self.live is not None:
            self.live.update(self.generate_ui())

    def get_nice_bytes(self, bytes=None):
        if bytes == None:
            return "-"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(bytes, 1024)))
        p = math.pow(1024, i)
        s = round(bytes / p, 2)
        return "%s %s" % (s, size_name[i])

    def get_live_ui(self, args):
        if args.subdomain_strategy == "all":
            nice_strategy = "Any and all subdomains of top domain"
        elif args.subdomain_strategy == "children":
            nice_strategy = "Same domain + any child subdomains"
        else:  # "exact"
            nice_strategy = "Exact same domain"
        nice_strategy += f", max depth {args.depth}"
        nice_strategy += f", {args.rate} reqs/s"
        nice_words = "Lowercase" if args.lowercase else "Mixed case"
        nice_words += ", " + ("excl." if args.without_numbers else "incl.") + " numbers"
        nice_words += ", incl. JS" if args.include_js else ""
        nice_words += ", incl. CSS" if args.include_css else ""
        nice_words += f", min. {args.min_word_length} chars."
        nice_ua = "Default" if constants.DEFAULT_USER_AGENT == args.user_agent else "Custom"
        nice_ua += " (" + textwrap.shorten(args.user_agent, width=40, placeholder="...") + ")"
        nice_output = "Screen only" if args.output is None else args.output

        self.is_verbose_output = args.verbose
        static_ui_lines = []
        static_ui_lines.append(["URL: ", f"[bold underline blue]{args.url}"])
        static_ui_lines.append(["Strategy: ", f"[magenta]{nice_strategy}"])
        static_ui_lines.append(["Words: ", f"[magenta]{nice_words}"])
        static_ui_lines.append(["User-Agent: ", f"[magenta]{nice_ua}"])
        static_ui_lines.append(["Output: ", f"[magenta]{nice_output}"])
        self.static_ui_lines = static_ui_lines

        print("\n")
        return Live(self.generate_ui(), console=self.console, refresh_per_second=4, auto_refresh=True)

    def generate_ui(self):
        try:
            grid = Table.grid(expand=True)
            for row in self.static_ui_lines:
                grid.add_row(row[0], row[1])

            event = self.last_event_received
            if self.is_verbose_output and event is not None and "status" in event:
                status = event["status"]
                color = "[green]"
                if isinstance(status, str):
                    if status == "init":
                        status = "Initializing..."
                    elif status == "writing_to_file":
                        status = "Writing words to file..."
                    elif status == "spider_closed":
                        status = "Spider stopped"
                    elif status == "engine_stopped":
                        status = "Spider engine stopped"
                    status_length = len(status)
                elif isinstance(status, tuple):
                    if status[0] == "request_reached_downloader":
                        status = f"Requesting [underline blue]{status[1]}[/underline blue]"
                        status_length = len(status)
                if status_length > self.longest_status_text:
                    self.longest_status_text = status_length
                status = status.ljust(self.longest_status_text, " ")
                grid.add_row("Status: ", color + status)

            time_spent = time.time() - self.start_time
            panel_footer = None if time_spent < 60 else "Press <ctrl> + c [bold]once[/bold] to abort and write to file"
            hours, remainder = divmod(time_spent, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours == 0:
                time_spent = "[magenta]{:02}:{:02}".format(int(minutes), int(seconds))
            else:
                time_spent = "[magenta]{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
            grid.add_row("Time elapsed: ", time_spent)

            if event is not None and "stats" in event and "downloader/request_count" in event["stats"] and "downloader/response_count" in event["stats"]:
                requests = "[magenta]" + str(event["stats"]["downloader/response_count"]) + "/" + str(
                    event["stats"]["downloader/request_count"])
                if "domains" in event and len(event["domains"]) > 1:
                    requests += f" @ {len(event['domains'])} domains"
            else:
                requests = "[magenta]-"
            grid.add_row("Requests: ", requests)

            if event is not None and "stats" in event and "downloader/response_bytes" in event["stats"]:
                received = event["stats"]["downloader/response_bytes"]
            else:
                received = None
            grid.add_row("Data received: ", "[magenta]" + self.get_nice_bytes(received))

            if self.is_verbose_output and event is not None and "unsupported_content_types" in event:
                unsupported_content_types = event["unsupported_content_types"]
                if (len(unsupported_content_types) > 0):
                    grid.add_row("Unsupported: ", ", ".join(sorted(unsupported_content_types)))

            if event is not None and "words" in event:
                words = str(len(event["words"]))
            else:
                words = "-"
            grid.add_row("Words found: ", "[green bold]" + words)

            renderable = Panel.fit(Padding(grid, (1, 2)), title=f"{__program__} v.{__version__} - {__description__}", subtitle=panel_footer)

            if event is not None and "exceptions" in event:
                exceptions = event["exceptions"]
                if (len(exceptions) > 0):
                    for exception in exceptions:
                        try:
                            raise exception
                        except Exception:
                            self.console.print_exception(show_locals=False)
                    event["exceptions"].clear()

            return renderable
        except Exception:
            self.console.print_exception(show_locals=False)

    def run(self):
        self.start_time = time.time()
        try:
            args = self.get_parsed_args_and_init_parser()
            self.live = self.get_live_ui(args)

            with self.live:
                process = CrawlerProcess(self.get_scrapy_settings_and_init_logging(args.user_agent, args.depth, args.rate, args.subdomain_strategy))
                process.crawl(spider.CewlerSpider, console=self.console, url=args.url, file_words=args.output, file_emails=args.output_emails, file_urls=args.output_urls, include_js=args.include_js, include_css=args.include_css, include_pdf=args.include_pdf,
                              should_lowercase=args.lowercase, without_numbers=args.without_numbers, min_word_length=args.min_word_length, verbose=args.verbose, stream_to_file=args.stream, spider_event_callback=self.on_spider_event)
                process.start()
            print("")

            if args.output is None:  # Should output to screen
                if self.last_event_received is not None and "words" in self.last_event_received:
                    for word in self.last_event_received["words"]:
                        print(word)
                    print("")
        except Exception:
            self.console.print_exception(show_locals=False)


def main():
    cewler = Cewler()
    cewler.run()


if __name__ == "__main__":
    main()
