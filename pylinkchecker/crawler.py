# -*- coding: utf-8 -*-
"""
Contains the crawling logic.
"""
from __future__ import unicode_literals, absolute_import

import sys

from pylinkchecker.compat import range
from pylinkchecker.models import Config, WorkerInit


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
        from Queue import Queue
        return Queue()

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

    def crawl_pages(self):
        url_to_crawl = self.input_queue.get()

        if url_to_crawl == WORK_DONE:
            # No more work! Pfew!
            return

        self.output_queue.put("")


def crawl_page(worker_init):
    """Safe redirection to the page crawler"""
    page_crawler = PageCrawler(worker_init)
    page_crawler.crawl_pages()


def execute_from_command_line():
    config = Config()
    config.parse_config()

    if not config.start_urls:
        print("At least one starting URL must be supplied.")
        sys.exit(1)

    crawler = ThreadSiteCrawler(config)
    crawler.crawl()
