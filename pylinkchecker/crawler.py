# -*- coding: utf-8 -*-
"""
Contains the crawling logic.
"""
from __future__ import unicode_literals, absolute_import

import sys

from bs4 import BeautifulSoup

import pylinkchecker.compat as compat
from pylinkchecker.compat import range, HTTPError, get_url_open, unicode
from pylinkchecker.models import (Config, WorkerInit, Response, PageCrawl,
        ExceptionStr, Link, DATA_SRC)
from pylinkchecker.urlutil import get_clean_url_split, get_absolute_url_split


WORK_DONE = '__WORK_DONE__'


class SiteCrawler(object):
    """Main crawler/orchestrator"""

    def __init__(self, config):
        self.config = config
        self.start_urls = config.start_urls
        self.workers = []
        self.input_queue = self.build_queue(config)
        self.output_queue = self.build_queue(config)
        self.worker_init = WorkerInit(self.config.worker_config,
            self.input_queue, self.output_queue)

    def crawl(self):
        self.workers = self.get_workers(self.config, self.worker_init)
        queue_size = len(self.start_urls)
        for start_url in self.start_urls:
            self.input_queue.put(start_url, False)

        self.start_workers(self.workers, self.input_queue, self.output_queue)

        urls_to_process = self.output_queue.get()
        queue_size -= 1
        new_urls = self.process_urls(urls_to_process)

        if not new_urls and queue_size <= 0:
            self.stop_workers(self.workers, self.input_queue, self.output_queue)

    def build_queue(self, config):
        raise NotImplementedError()

    def get_workers(self, config, worker_init):
        raise NotImplementedError()

    def start_workers(self, workers, input_queue, output_queue):
        raise NotImplementedError()

    def stop_workers(self, workers, input_queue, output_queue):
        raise NotImplementedError

    def process_urls(self, urls_to_process):
        return []


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

    def stop_workers(self, workers, input_queue, output_queue):
        for worker in workers:
            input_queue.put(WORK_DONE)

    def process_urls(self, urls_to_process):
        return []


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
                            exception=None)
                elif response.is_timeout:
                    # This is a timeout. No need to wrap the exception
                    page_crawl = PageCrawl(
                            original_url_split=url_split_to_crawl,
                            final_url_split=None, status=None,
                            is_timeout=True, is_redirect=False, links=None,
                            exception=None)
                else:
                    exception = ExceptionStr(unicode(type(response.exception)),
                        unicode(response.exception))
                    page_crawl = PageCrawl(
                            original_url_split=url_split_to_crawl,
                            final_url_split=None, status=None,
                            is_timeout=False, is_redirect=False, links=None,
                            exception=exception)
            else:
                final_url_split = get_clean_url_split(response.final_url)

                html_soup = BeautifulSoup(response.content,
                        self.worker_config.parser)
                links = self.get_links(html_soup, final_url_split)

                page_crawl = PageCrawl(original_url_split=url_split_to_crawl,
                    final_url_split=final_url_split, status=response.status,
                    is_timeout=False, is_redirect=response.is_redirect,
                    links=links, exception=None)
        except Exception as exc:
            exception = ExceptionStr(unicode(type(exc)), unicode(exc))
            page_crawl = PageCrawl(original_url_split=url_split_to_crawl,
                    final_url_split=None, status=None,
                    is_timeout=False, is_redirect=False, links=None,
                    exception=exception)
            from traceback import print_exc
            print_exc()

        return page_crawl

    def get_links(self, html_soup, original_url_split):

        # This is a weird html tag that defines the base URL of a page.
        base_url_split = original_url_split

        bases = html_soup.find_all('base')
        if bases:
            base = bases[0]
            if 'href' in base.attrs:
                base_url_split = get_clean_url_split(base['href'])

        links = []
        if 'a' in self.worker_config.types:
            a_links = html_soup.find_all('a')
            links.extend(self._get_links(a_links, 'href', base_url_split,
                    original_url_split))
        if 'img' in self.worker_config.types:
            img_links = html_soup.find_all('img')
            links.extend(self._get_links(img_links, 'src', base_url_split,
                    original_url_split))
        if 'link' in self.worker_config.types:
            link_links = html_soup.find_all('link')
            links.extend(self._get_links(link_links, 'href', base_url_split,
                    original_url_split))
        if 'script' in self.worker_config.types:
            script_links = html_soup.find_all('script')
            links.extend(self._get_links(script_links, 'src', base_url_split,
                    original_url_split))
        return links

    def _get_links(self, elements, attribute, base_url_split,
        original_url_split):
        links = []
        for element in elements:
            if attribute in element.attrs:
                url = element[attribute]
                if url.startswith(DATA_SRC) or url.startswith('#'):
                    # Local or Base 64
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
