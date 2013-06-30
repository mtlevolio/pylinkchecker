# -*- coding: utf-8 -*-
"""
Contains the crawling models.
"""
from __future__ import unicode_literals, absolute_import

from collections import namedtuple
from optparse import OptionParser, OptionGroup

from pylinkchecker.urlutil import get_clean_url_split


DEFAULT_TYPES = ['a', 'img', 'script', 'link']


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


WorkerInit = namedtuple("WorkerInit", ["worker_config", "input_queue",
    "output_queue"])

WorkerConfig = namedtuple("WorkerConfig", ["username", "password", "types"])

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

        return WorkerConfig(options.username, options.password, types)

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
        crawler_group.add_option("-H", "--accepted-hosts", dest="accepted_hosts",
            action="store", default=None,
            help="comma-separated list of additional hosts to crawl (e.g., "
                "example.com,subdomain.another.com)")
        crawler_group.add_option("-i", "--ignore", dest="ignored_prefixes",
            action="store", default=None,
            help="comma-separated list of host/path prefixes to ignore (e.g., "
                "www.example.com/ignore_this_and_after/)")
        crawler_group.add_option("-u", "--username", dest="username", action="store",
            default=None)
        crawler_group.add_option("-p", "--password", dest="password", action="store",
            default=None)
        crawler_group.add_option("-U", "--unique", dest="unique", action="store_true",
            default=False)
        crawler_group.add_option("-t", "--types", dest="types", action="store",
            default=",".join(DEFAULT_TYPES))
        # TODO Add follow redirect option.

        parser.add_option_group(crawler_group)


        perf_group = OptionGroup(parser, "Performance Options",
            "These options can impact the performance of the crawler.")

        perf_group.add_option("-w", "--workers", dest="workers", action="store",
            default=None, type="int")
        perf_group.add_option("-m", "--mode", dest="mode", action="store",
            default=MODE_THREAD, choices=[MODE_THREAD, MODE_PROCESS, MODE_GREEN])
        perf_group.add_option("-P", "--parser", dest="parser", action="store",
            default=PARSER_STDLIB, choices=[PARSER_STDLIB, PARSER_LXML])

        parser.add_option_group(perf_group)


        output_group = OptionGroup(parser, "Output Options",
            "These options change the output of the crawler.")

        output_group.add_option("-f", "--format", dest="format", action="store",
            default=FORMAT_PLAIN, choices=[FORMAT_PLAIN, FORMAT_HTML, FORMAT_JSON])
        output_group.add_option("-o", "--output", dest="output", action="store",
            default=None)
        output_group.add_option("-W", "--when", dest="when", action="store",
            default=WHEN_ALWAYS, choices=[WHEN_ALWAYS, WHEN_ON_ERROR])

        parser.add_option_group(output_group)

        # TODO ADD EMAIL OPTIONS

        return parser


class Site(object):

    def __init__(self):
        pass