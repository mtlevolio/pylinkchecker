# -*- coding: utf-8 -*-
"""
Contains the crawling models.
"""
from __future__ import unicode_literals, absolute_import

from collections import namedtuple
from optparse import OptionParser, OptionGroup

from pylinkchecker.urlutil import get_clean_url_split


DEFAULT_TYPES = ['a', 'img', 'script', 'link']


TYPE_ATTRIBUTES = {
    'a': 'href',
    'img': 'src',
    'script': 'src',
    'link': 'href',
}


DEFAULT_TIMEOUT = 10


MODE_THREAD = "thread"
MODE_PROCESS = "process"
MODE_GREEN = "green"


DEFAULT_WORKERS = {
    MODE_THREAD: 1,
    MODE_PROCESS: 1,
    MODE_GREEN: 1000,
}


PARSER_STDLIB = "html.parser"
PARSER_LXML = "lxml"


FORMAT_PLAIN = "plain"
FORMAT_HTML = "html"
FORMAT_JSON = "json"


WHEN_ALWAYS = "always"
WHEN_ON_ERROR = "error"


VERBOSE_QUIET = "0"
VERBOSE_NORMAL = "1"
VERBOSE_INFO = "2"


HTML_MIME_TYPE = "text/html"


PAGE_QUEUED = '__PAGE_QUEUED__'
PAGE_CRAWLED = '__PAGE_CRAWLED__'

# Note: we use namedtuple to exchange data with workers because they are
# immutable and easy to pickle (as opposed to a class).

WorkerInit = namedtuple("WorkerInit", ["worker_config", "input_queue",
        "output_queue"])


WorkerConfig = namedtuple("WorkerConfig", ["username", "password", "types",
        "timeout", "parser"])


WorkerInput = namedtuple("WorkerInput", ["url_split", "should_crawl"])


Response = namedtuple("Response", ["content", "status", "exception",
        "original_url", "final_url", "is_redirect", "is_timeout"])


ExceptionStr = namedtuple("ExceptionStr", ["type_name", "message"])


Link = namedtuple("Link", ["type", "url_split", "original_url_split",
        "source_str"])


PageCrawl = namedtuple("PageCrawl", ["original_url_split", "final_url_split",
        "status", "is_timeout", "is_redirect", "links", "exception", "is_html"])


PageStatus = namedtuple("PageStatus", ["status", "sources"])


PageSource = namedtuple("PageSource", ["origin", "origin_str"])


class Config(object):
    """Contains all the configuration options."""

    def __init__(self):
        self.parser = self._build_parser()
        self.options = {}
        self.start_urls = []
        self.worker_config = None
        self.accepted_hosts = []
        self.ignored_prefixes = []
        self.test_outside = False
        self.worker_size = 0

    def is_local(self, url_split):
        """Returns true if url split is in the accepted hosts"""
        return url_split.netloc in self.accepted_hosts

    def should_download(self, url_split):
        """Returns True if the url does not start with an ignored prefix and if
        it is local or outside links are allowed."""
        local = self.is_local(url_split)

        if not self.test_outside and not local:
            return False

        url = url_split.geturl()

        for ignored_prefix in self.ignored_prefixes:
            if url.startswith(ignored_prefix):
                return False

        return True

    def parse_config(self):
        """Build the options and args based on the command line options."""
        (self.options, self.start_urls) = self.parser.parse_args()
        self.worker_config = self._build_worker_config(self.options)
        self.accepted_hosts = self._build_accepted_hosts(self.options,
                self.start_urls)

        if self.options.ignored_prefixes:
            self.ignored_prefixes = self.options.ignored_prefixes.split(',')

        if self.options.workers:
            self.worker_size = self.options.workers
        else:
            self.worker_size = DEFAULT_WORKERS[self.options.mode]

    def _build_worker_config(self, options):
        types = options.types.split(',')
        for element_type in types:
            if element_type not in DEFAULT_TYPES:
                raise ValueError("This type is not supported: {0}"
                        .format(element_type))

        return WorkerConfig(options.username, options.password, types,
                options.timeout, options.parser)

    def _build_accepted_hosts(self, options, start_urls):
        hosts = set()
        urls = []

        if self.options.accepted_hosts:
            urls = self.options.accepted_hosts.split(',')
        urls = urls + start_urls

        for url in urls:
            split_result = get_clean_url_split(url)
            hosts.add(split_result.netloc)

        return hosts

    def _build_parser(self):
        # avoid circular references
        import pylinkchecker
        version = pylinkchecker.__version__

        parser = OptionParser(usage="%prog [options] URL ...",
                version="%prog {0}".format(version))

        parser.add_option("-V", "--verbose", dest="verbose", action="store",
                default=VERBOSE_NORMAL, choices=[VERBOSE_QUIET, VERBOSE_NORMAL,
                VERBOSE_INFO])

        crawler_group = OptionGroup(parser, "Crawler Options",
                "These options modify the way the crawler traverses the site.")
        crawler_group.add_option("-O", "--test-outside", dest="test_outside",
                action="store_true", default=False,
                help="fetch resources from other domains without crawling them")
        crawler_group.add_option("-H", "--accepted-hosts",
                dest="accepted_hosts",  action="store", default=None,
                help="comma-separated list of additional hosts to crawl (e.g., "
                "example.com,subdomain.another.com)")
        crawler_group.add_option("-i", "--ignore", dest="ignored_prefixes",
                action="store", default=None,
                help="comma-separated list of host/path prefixes to ignore "
                "(e.g., www.example.com/ignore_this_and_after/)")
        crawler_group.add_option("-u", "--username", dest="username",
                action="store", default=None)
        crawler_group.add_option("-p", "--password", dest="password",
                action="store", default=None)
        crawler_group.add_option("-U", "--unique", dest="unique",
                action="store_true", default=False)
        crawler_group.add_option("-t", "--types", dest="types", action="store",
                default=",".join(DEFAULT_TYPES))
        crawler_group.add_option("-T", "--timeout", dest="timeout",
                type="int", action="store", default=DEFAULT_TIMEOUT)
        # TODO Add follow redirect option.

        parser.add_option_group(crawler_group)


        perf_group = OptionGroup(parser, "Performance Options",
                "These options can impact the performance of the crawler.")

        perf_group.add_option("-w", "--workers", dest="workers", action="store",
                default=None, type="int")
        perf_group.add_option("-m", "--mode", dest="mode", action="store",
                default=MODE_THREAD, choices=[MODE_THREAD, MODE_PROCESS,
                MODE_GREEN])
        perf_group.add_option("-P", "--parser", dest="parser", action="store",
                default=PARSER_STDLIB, choices=[PARSER_STDLIB, PARSER_LXML])

        parser.add_option_group(perf_group)


        output_group = OptionGroup(parser, "Output Options",
                "These options change the output of the crawler.")

        output_group.add_option("-f", "--format", dest="format", action="store",
                default=FORMAT_PLAIN, choices=[FORMAT_PLAIN, FORMAT_HTML,
                FORMAT_JSON])
        output_group.add_option("-o", "--output", dest="output", action="store",
                default=None)
        output_group.add_option("-W", "--when", dest="when", action="store",
                default=WHEN_ALWAYS, choices=[WHEN_ALWAYS, WHEN_ON_ERROR])

        parser.add_option_group(output_group)

        # TODO ADD EMAIL OPTIONS

        return parser


class SitePage(object):
    """Contains the crawling result for a page.

    This is a class because we need to keep track of the various sources
    linking to this page and it must be modified as the crawl progresses.
    """

    def __init__(self, url_split, status=200, is_timeout=False, exception=None,
            is_html=True, is_local=True):
        self.url_split = url_split

        self.original_source = None
        self.sources = []

        self.type = type
        self.status = status
        self.is_timeout = is_timeout
        self.exception = exception
        self.is_html = is_html
        self.is_ok = status and status < 400
        self.is_local = is_local

    def add_sources(self, page_sources):
        self.sources.extend(page_sources)


class Site(object):
    """Contains all the visited and visiting pages of a site.

    This class is NOT thread-safe and should only be accessed by one thread at
    a time!
    """

    def __init__(self, start_url_splits, config):
        self.start_url_splits = start_url_splits

        self.pages = {}
        """Map of url:SitePage"""

        self.page_statuses = {}
        """Map of url:PageStatus (PAGE_QUEUED, PAGE_CRAWLED)"""

        self.config = config

        for start_url_split in self.start_url_splits:
            self.page_statuses[start_url_split] = PageStatus(PAGE_QUEUED, [])

    def add_crawled_page(self, page_crawl):
        """Adds a crawled page. Returns a list of url split to crawl"""
        if not page_crawl.original_url_split in self.page_statuses:
            # There is a problem! Should not happen.
            # TODO LOG!
            return []

        status = self.page_statuses[page_crawl.original_url_split]

        # Mark it as crawled
        self.page_statuses[page_crawl.original_url_split] = PageStatus(
                PAGE_CRAWLED, None)

        if page_crawl.original_url_split in self.pages:
            # There is a problem! Should not happen
            # TODO LOG!
            return []

        final_url_split = page_crawl.final_url_split
        if final_url_split in self.pages:
            # This means that we already processed this final page (redirect).
            # It's ok. Just add a source
            site_page = self.pages[final_url_split]
            site_page.add_sources(status.sources)
        else:
            is_local = self.config.is_local(final_url_split)
            site_page = SitePage(final_url_split, page_crawl.status,
                    page_crawl.is_timeout, page_crawl.exception,
                    page_crawl.is_html, is_local)
            site_page.add_sources(status.sources)

        return self.process_links(page_crawl)

    def process_links(self, page_crawl):
        links_to_process = []
        for link in page_crawl.links:
            url_split = link.url_split
            if not self.config.should_download(url_split):
                continue

            page_status = self.page_statuses.get(url_split, None)

            page_source = PageSource(url_split, link.source_str)

            if not page_status:
                # We never encountered this url before
                self.page_statuses[url_split] = PageStatus(PAGE_QUEUED,
                        [page_source])
                links_to_process.append(
                        WorkerInput(url_split, self.config.is_local(url_split)))
            elif page_status.status == PAGE_CRAWLED:
                # Already crawled. Add source
                self.pages[url_split].add_sources([page_source])
            elif page_status.status == PAGE_QUEUED:
                # Already queued for crawling. Add source.
                page_status.sources.append(page_source)

        return links_to_process
