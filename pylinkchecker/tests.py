# -*- coding: utf-8 -*-
"""
Unit and integration tests for pylinkchecker
"""
from __future__ import unicode_literals, absolute_import

import os
import sys
import time
import threading
import unittest

from pylinkchecker.crawler import open_url
from pylinkchecker.compat import SocketServer, SimpleHTTPServer, get_url_open
from pylinkchecker.models import Config
from pylinkchecker.urlutil import get_clean_url_split, get_absolute_url


TEST_FILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
        'testfiles')


class ConfigTest(unittest.TestCase):

    def setUp(self):
        self.argv = sys.argv

    def tearDown(self):
        sys.argv = self.argv

    def test_accepted_hosts(self):
        sys.argv = ['pylinkchecker', 'http://www.example.com/']
        config = Config()
        config.parse_config()
        self.assertTrue('www.example.com' in config.accepted_hosts)

        sys.argv = ['pylinkchecker', '-H', 'www.example.com',
                'http://example.com', 'foo.com', 'http://www.example.com/',
                'baz.com']
        config = Config()
        config.parse_config()

        self.assertTrue('www.example.com' in config.accepted_hosts)
        self.assertTrue('example.com' in config.accepted_hosts)
        self.assertTrue('foo.com' in config.accepted_hosts)
        self.assertTrue('baz.com' in config.accepted_hosts)


class URLUtilTest(unittest.TestCase):

    def test_clean_url_split(self):
        self.assertEqual("http://www.example.com",
            get_clean_url_split("www.example.com").geturl())
        self.assertEqual("http://www.example.com",
            get_clean_url_split("//www.example.com").geturl())
        self.assertEqual("http://www.example.com",
            get_clean_url_split("http://www.example.com").geturl())

        self.assertEqual("http://www.example.com/",
            get_clean_url_split("www.example.com/").geturl())
        self.assertEqual("http://www.example.com/",
            get_clean_url_split("//www.example.com/").geturl())
        self.assertEqual("http://www.example.com/",
            get_clean_url_split("http://www.example.com/").geturl())

    def test_get_absolute_url(self):
        base_url_split = get_clean_url_split(
                "https://www.example.com/hello/index.html")
        self.assertEqual("https://www.example2.com/test.js",
            get_absolute_url("//www.example2.com/test.js", base_url_split).
            geturl())
        self.assertEqual("https://www.example.com/hello2/test.html",
            get_absolute_url("/hello2/test.html", base_url_split).geturl())
        self.assertEqual("https://www.example.com/hello/test.html",
            get_absolute_url("test.html", base_url_split).geturl())
        self.assertEqual("https://www.example.com/test.html",
            get_absolute_url("../test.html", base_url_split).geturl())

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def start_http_server():
    """Starts a simple http server for the test files"""
    # For the http handler
    os.chdir(TEST_FILES_DIR)
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = ThreadedTCPServer(("localhost", 0), handler)
    ip, port = httpd.server_address

    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.setDaemon(True)
    httpd_thread.start()

    return (ip, port, httpd, httpd_thread)


class CrawlerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        (cls.ip, cls.port, cls.httpd, cls.httpd_thread) = start_http_server()
        # FIXME replace by thread synchronization on start
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        # We must do this because Python 2.6 does not have setUpClass
        # This will only be executed if setUpClass is ignored.
        # It will not be shutdown properly though, but this does not prevent
        # the unit test to run properly
        if not hasattr(self, 'port'):
            (self.ip, self.port, self.httpd, self.httpd_thread) =\
                    start_http_server()
            # FIXME replace by thread synchronization on start
            time.sleep(0.2)

    def get_url(self, test_url):
        return "http://{0}:{1}{2}".format(self.ip, self.port, test_url)

    def test_404(self):
        urlopen = get_url_open()
        import socket
        url = self.get_url("/does_not_exist.html")
        response = open_url(urlopen, url, 5, socket.timeout)

        self.assertEqual(404, response.status)
        self.assertTrue(response.exception is not None)

    def test_200(self):
        urlopen = get_url_open()
        import socket
        url = self.get_url("/index.html")
        response = open_url(urlopen, url, 5, socket.timeout)

        self.assertEqual(200, response.status)
        self.assertTrue(response.exception is None)

    def test_301(self):
        urlopen = get_url_open()
        import socket
        url = self.get_url("/sub")
        response = open_url(urlopen, url, 5, socket.timeout)

        self.assertEqual(200, response.status)
        self.assertTrue(response.is_redirect)
