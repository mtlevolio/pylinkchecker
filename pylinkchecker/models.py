# -*- coding: utf-8 -*-
"""
Contains the main crawling logic.
"""
from __future__ import unicode_literals, absolute_import

from optparse import OptionParser, OptionGroup


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


def get_parser():
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
    crawler_group.add_option("-u", "--username", dest="username", action="store",
        default=None)
    crawler_group.add_option("-p", "--password", dest="password", action="store",
        default=None)
    crawler_group.add_option("-U", "--unique", dest="unique", action="store_true",
        default=False)
    crawler_group.add_option("-t", "--types", dest="types", action="store",
        default="a,img,script,link")

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


class Config(object):
    """Contains all configuration options."""

    def __init__(self, start_urls, test_outside=True, accepted_hosts=None,
        username=None, password=None, ignore_prefixes=None, types=None, ):
        pass


class Site(object):

    def __init__(self):
        pass