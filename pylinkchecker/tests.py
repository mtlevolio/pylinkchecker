# -*- coding: utf-8 -*-
"""
Unit and integration tests for pylinkchecker
"""
from __future__ import unicode_literals, absolute_import

import unittest

from pylinkchecker.urlutil import get_clean_url_split


class ConfigTest(unittest.TestCase):

    def test_simple(self):
        self.assertTrue(True)


class URLUtilTest(unittest.TestCase):

    def test_clean_url_split(self):
        self.assertEqual("http://www.perdu.com",
            get_clean_url_split("www.perdu.com").geturl())
