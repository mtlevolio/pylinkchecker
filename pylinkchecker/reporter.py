"""
Contains the reporting functions
"""
from __future__ import unicode_literals, absolute_import


def report_plain_text(site):
    for page in site.pages.values():
        print("{0}: {1}".format(page.url_split.geturl(), page.get_status_message()))

