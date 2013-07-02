# -*- coding: utf-8 -*-
"""
Contains the compatibility layer for python 2 & 3
"""
from __future__ import unicode_literals, absolute_import

import sys

if sys.version_info[0] < 3:
    range = xrange
    import urlparse
    import SimpleHTTPServer
    import SocketServer
    from urllib2 import HTTPError
    import Queue
    unicode = unicode
    get_content_type = lambda m: m.gettype()
else:
    range = range
    import urllib.parse as urlparse
    import http.server as SimpleHTTPServer
    import socketserver as SocketServer
    from urllib.error import HTTPError
    import queue as Queue
    unicode = str
    get_content_type = lambda m: m.get_content_type()


def get_url_open():
    # Not automatically imported to allow monkey patching.
    if sys.version_info[0] < 3:
        from urllib2 import urlopen
    else:
        from urllib.request import urlopen
    return urlopen
