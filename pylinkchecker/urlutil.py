# -*- coding: utf-8 -*-
"""
Contains the crawling logic.
"""
from __future__ import unicode_literals, absolute_import

from pylinkchecker.compat import urlparse


SCHEME_HTTP = "http"
SCHEME_HTTPS = "https"
SUPPORTED_SCHEMES = (SCHEME_HTTP, SCHEME_HTTPS)


def get_clean_url_split(url):
    """Returns a clean SplitResult with a scheme and a valid path

    :param url: The url to clean
    :rtype: A urlparse.SplitResult
    """
    if not url:
        raise ValueError('The URL must not be empty')
    split_result = urlparse.urlsplit(url)

    if not split_result.scheme:
        if split_result.netloc:
            url = SCHEME_HTTP + ":" + url
        else:
            url = SCHEME_HTTP + "://" + url
        split_result = urlparse.urlsplit(url)

    return split_result