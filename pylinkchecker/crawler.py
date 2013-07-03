# -*- coding: utf-8 -*-
"""
Contains the crawling logic.
"""
from __future__ import unicode_literals, absolute_import

import sys

from pylinkchecker.bs4 import BeautifulSoup

import pylinkchecker.compat as compat
from pylinkchecker.compat import (range, HTTPError, get_url_open, unicode,
        get_content_type)
from pylinkchecker.models import (Config, WorkerInit, Response, PageCrawl,
        ExceptionStr, Link, Site, TYPE_ATTRIBUTES, HTML_MIME_TYPE)
from pylinkchecker.urlutil import (get_clean_url_split, get_absolute_url_split,
        is_link)


WORK_DONE = '__WORK_DONE__'


class SiteCrawler(object):
    """Main crawler/orchestrator"""

    def __init__(self, config):
        self.config = config
        self.start_url_splits = []
        for start_url in config.start_urls:
            self.start_url_splits.append(get_clean_url_split(start_url))
        self.workers = []
        self.input_queue = self.build_queue(config)
        self.output_queue = self.build_queue(config)
        self.worker_init = WorkerInit(self.config.worker_config,
            self.input_queue, self.output_queue)
        self.site = Site(self.start_url_splits)

    def crawl(self):
        self.workers = self.get_workers(self.config, self.worker_init)
        queue_size = len(self.start_url_splits)
        for start_url_split in self.start_url_splits:
            self.input_queue.put(start_url_split, False)

        self.start_workers(self.workers, self.input_queue, self.output_queue)

        while True:
            page_crawl = self.output_queue.get()
            queue_size -= 1
            new_url_splits = self.process_page_crawl(page_crawl)

            if not new_url_splits and queue_size <= 0:
                self.stop_workers(self.workers, self.input_queue,
                        self.output_queue)
                return self.site

            for url_split in new_url_splits:
                queue_size += 1
                self.input_queue.put(url_split, False)


    def build_queue(self, config):
        """Returns an object implementing the Queue interface."""
        raise NotImplementedError()

    def get_workers(self, config, worker_init):
        """Returns a sequence of workers of the desired type."""
        raise NotImplementedError()

    def start_workers(self, workers, input_queue, output_queue):
        """Start the workers."""
        raise NotImplementedError()

    def stop_workers(self, workers, input_queue, output_queue):
        """Stops the workers."""
        for worker in workers:
            input_queue.put(WORK_DONE)

    def process_page_crawl(self, page_crawl):
        """Returns a sequence of SplitResult to crawl."""
        return self.site.add_crawled_page(page_crawl)


class ThreadSiteCrawler(SiteCrawler):
    """Site Crawler with thread workers."""

    def build_queue(self, config):
        return compat.Queue.Queue()

    def get_workers(self, config, worker_init):
        from threading import Thread
        workers = []
        for _ in range(config.worker_size):
            workers.append(Thread(target=crawl_page, kwargs={'worker_init':
                worker_init}))

        return workers

    def start_workers(self, workers, input_queue, output_queue):
        for worker in workers:
            worker.start()


class ProcessSiteCrawler(SiteCrawler):
    """Site Crawler with process workers."""
    pass


class GreenSiteCrawler(SiteCrawler):
    """Site Crawler with green thread workers."""
    pass


class PageCrawler(object):
    """Worker that parses a page and extracts links"""

    def __init__(self, worker_init):
        self.worker_config = worker_init.worker_config
        self.input_queue = worker_init.input_queue
        self.output_queue = worker_init.output_queue
        self.urlopen = get_url_open()

        # We do this here to allow patching by gevent
        import socket
        self.timeout_exception = socket.timeout

    def crawl_page_forever(self):
        """Starts page crawling loop for this worker."""

        while True:
            url_split_to_crawl = self.input_queue.get()

            if url_split_to_crawl == WORK_DONE:
                # No more work! Pfew!
                return
            else:
                page_crawl = self._crawl_page(url_split_to_crawl)
                self.output_queue.put(page_crawl)

    def _crawl_page(self, url_split_to_crawl):
        page_crawl = None

        try:
            response = open_url(self.urlopen, url_split_to_crawl.geturl(),
                    self.worker_config.timeout, self.timeout_exception)

            if response.exception:
                if response.status:
                    # This is a http error. Good.
                    page_crawl = PageCrawl(
                            original_url_split=url_split_to_crawl,
                            final_url_split=None, status=response.status,
                            is_timeout=False, is_redirect=False, links=None,
                            exception=None, is_html=False)
                elif response.is_timeout:
                    # This is a timeout. No need to wrap the exception
                    page_crawl = PageCrawl(
                            original_url_split=url_split_to_crawl,
                            final_url_split=None, status=None,
                            is_timeout=True, is_redirect=False, links=None,
                            exception=None, is_html=False)
                else:
                    # Something bad happened when opening the url
                    exception = ExceptionStr(unicode(type(response.exception)),
                        unicode(response.exception))
                    page_crawl = PageCrawl(
                            original_url_split=url_split_to_crawl,
                            final_url_split=None, status=None,
                            is_timeout=False, is_redirect=False, links=None,
                            exception=exception, is_html=False)
            else:
                final_url_split = get_clean_url_split(response.final_url)

                mime_type = get_content_type(response.content.info())

                if mime_type == HTML_MIME_TYPE:
                    html_soup = BeautifulSoup(response.content,
                            self.worker_config.parser)
                    links = self.get_links(html_soup, final_url_split)
                    is_html = True
                else:
                    links = []
                    is_html = False

                page_crawl = PageCrawl(original_url_split=url_split_to_crawl,
                    final_url_split=final_url_split, status=response.status,
                    is_timeout=False, is_redirect=response.is_redirect,
                    links=links, exception=None, is_html=is_html)
        except Exception as exc:
            exception = ExceptionStr(unicode(type(exc)), unicode(exc))
            page_crawl = PageCrawl(original_url_split=url_split_to_crawl,
                    final_url_split=None, status=None,
                    is_timeout=False, is_redirect=False, links=None,
                    exception=exception, is_html=False)

        return page_crawl

    def get_links(self, html_soup, original_url_split):
        """Get Link for desired types (e.g., a, link, img, script)

        :param html_soup: The page parsed by BeautifulSoup
        :param original_url_split: The URL of the page used to resolve relative
                links.
        :rtype: A sequence of Link objects
        """

        # This is a weird html tag that defines the base URL of a page.
        base_url_split = original_url_split

        bases = html_soup.find_all('base')
        if bases:
            base = bases[0]
            if 'href' in base.attrs:
                base_url_split = get_clean_url_split(base['href'])

        links = []
        for element_type in self.worker_config.types:
            if element_type not in TYPE_ATTRIBUTES:
                raise Exception("Unknown element type: {0}".
                        format(element_type))
            attribute = TYPE_ATTRIBUTES[element_type]
            element_links = html_soup.find_all(element_type)
            links.extend(self._get_links(element_links, attribute,
                    base_url_split, original_url_split))
        return links

    def _get_links(self, elements, attribute, base_url_split,
        original_url_split):
        links = []
        for element in elements:
            if attribute in element.attrs:
                url = element[attribute]
                if not is_link(url):
                    continue
                abs_url_split = get_absolute_url_split(url, base_url_split)

                link = Link(type=unicode(element.name), url_split=abs_url_split,
                    original_url_split=original_url_split,
                    source_str=unicode(element))
                links.append(link)

        return links


def crawl_page(worker_init):
    """Safe redirection to the page crawler"""
    page_crawler = PageCrawler(worker_init)
    page_crawler.crawl_page_forever()


def open_url(open_func, url, timeout, timeout_exception):
    """Opens a URL and returns a Response object.

    All parameters are required to be able to use a patched version of the
    Python standard library (i.e., patched by gevent)

    :param open_func: url open function, typicaly urllib2.urlopen
    :param url: the url to open
    :param timeout: number of seconds to wait before timing out
    :param timeout_exception: the exception thrown by open_func if a timeout
            occurs
    :rtype: A Response object
    """
    try:
        output_value = open_func(url)
        final_url = output_value.geturl()
        code = output_value.getcode()
        response = Response(content=output_value, status=code, exception=None,
            original_url=url, final_url=final_url, is_redirect=final_url != url,
            is_timeout=False)
    except HTTPError as http_error:
        code = http_error.code
        response = Response(content=None, status=code, exception=http_error,
            original_url=url, final_url=None, is_redirect=False,
            is_timeout=False)
    except timeout_exception as t_exception:
        response = Response(content=None, status=None, exception=t_exception,
            original_url=url, final_url=None, is_redirect=False,
            is_timeout=True)
    except Exception as exc:
        response = Response(content=None, status=None, exception=exc,
            original_url=url, final_url=None, is_redirect=False)

    return response


def execute_from_command_line():
    config = Config()
    config.parse_config()

    if not config.start_urls:
        print("At least one starting URL must be supplied.")
        sys.exit(1)

    crawler = ThreadSiteCrawler(config)
    crawler.crawl()
