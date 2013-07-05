"""
Contains the reporting functions
"""
from __future__ import unicode_literals, absolute_import, print_function

import codecs
import sys

from pylinkchecker.models import REPORT_TYPE_ERRORS, REPORT_TYPE_ALL


def close_quietly(a_file):
    """Closes a file and does not report an error."""
    try:
        if a_file:
            a_file.close()
    except Exception:
        pass


def report_plain_text(site, config, total_time):
    if config.options.output:
        output_file = codecs.open(config.options.output, "w", "utf-8")
    else:
        output_file = sys.stdout

    try:
        _write_plain_text_report(site, config, output_file, total_time)
    except Exception:
        # TODO Log exception
        pass

    if config.options.output:
        close_quietly(output_file)


def _write_plain_text_report(site, config, output_file, total_time):
    start_urls = ",".join((start_url_split.geturl() for start_url_split in
        site.start_url_splits))

    total_urls = len(site.pages)
    total_errors = len(site.error_pages)

    if not site.is_ok:
        global_status = "ERROR"
        error_summary = "with {0} error(s) ".format(total_errors)
    else:
        global_status = "SUCCESS"
        error_summary = ""


    print("{0} Crawled {1} urls {2}in {3:.2f} seconds".format(
            global_status, total_urls, error_summary, total_time),
            file=output_file)

    pages = {}

    if config.options.report_type == REPORT_TYPE_ERRORS:
        pages = site.error_pages
    elif config.options.report_type == REPORT_TYPE_ALL:
        pages = site.pages

    if pages:
        print("\n  Start URL(s): {0}".format(start_urls), file=output_file)

        for page in pages.values():
            print("\n  {0}: {1}".format(page.get_status_message(),
                    page.url_split.geturl()), file=output_file)
            for source in page.sources:
                print("    from {0}".format(source.origin.geturl()),
                        file=output_file)

    # for page in site.pages.values():
    #     print("{0}: {1}".format(page.url_split.geturl(), page.get_status_message()))

