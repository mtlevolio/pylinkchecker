# -*- coding: utf-8 -*-
"""
Contains the compatibility layer for python 2 & 3
"""
from __future__ import unicode_literals, absolute_import

import sys

if sys.version_info[0] < 3:
    range = xrange
    import urlparse
else:
    range = range
    import urllib.parse as urlparse