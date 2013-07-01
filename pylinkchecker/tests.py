# -*- coding: utf-8 -*-
"""
Unit and integration tests for pylinkchecker
"""
from __future__ import unicode_literals, absolute_import

import os
import sys
import threading
import unittest

from pylinkchecker.compat import SocketServer, SimpleHTTPServer
from pylinkchecker.models import Config
from pylinkchecker.urlutil import get_clean_url_split


TEST_FILES_DIR = os.path.dirname(os.path.realpath(__file__))


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


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def start_http_server():
    """Starts a simple http server for the test files"""
    # For the http handler
    os.chdir(TEST_FILES_DIR)
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("localhost", 0), handler)
    ip, port = httpd.server_address

    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.setDaemon(True)
    httpd_thread.start()

    return (ip, port, httpd, httpd_thread)


class CrawlerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        (cls.ip, cls.port, cls.httpd, cls.httpd_thread) = start_http_server()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        # We must do this because Python 2.6 does not have setUpClass
        # It will not be shutdown properly though, but this does not prevent
        # the unit test to run properly
        if not hasattr(self, 'test_port'):
            (self.ip, self.port, self.httpd, self.httpd_thread) =\
                    start_http_server()

    def test_404(self):
        pass