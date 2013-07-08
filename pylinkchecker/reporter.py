"""
Contains the reporting functions
"""
from __future__ import unicode_literals, absolute_import, print_function

import codecs
import smtplib
import sys

from pylinkchecker.compat import StringIO
from pylinkchecker.models import (REPORT_TYPE_ERRORS, REPORT_TYPE_ALL,
        FORMAT_PLAIN)


PLAIN_TEXT = "text/plain"
HTML = "text/html"


EMAIL_HEADER = "from: {0}\r\nsubject: {1}\r\nto: {2}\r\nmime-version: 1.0\r\n"\
        "content-type: {3}\r\n\r\n{4}"


def close_quietly(a_file):
    """Closes a file and does not report an error."""
    try:
        if a_file:
            a_file.close()
    except Exception:
        pass


def report(site, config, total_time):
    """Prints reports to console, file, and email."""
    output_files = []
    output_file = None
    email_file = None

    if config.options.output:
        output_file = codecs.open(config.options.output, "w", "utf-8")
        output_files.append(output_file)

    if config.options.smtp:
        email_file = StringIO()
        output_files.append(email_file)

    if config.options.console or not output_files:
        output_files.append(sys.stdout)

    try:
        if config.options.format == FORMAT_PLAIN:
            _write_plain_text_report(site, config, output_files, total_time)
    except Exception:
        # TODO Log exception
        pass

    if output_file:
        close_quietly(output_file)

    if email_file:
        send_email(email_file, site, config)


def _write_plain_text_report(site, config, output_files, total_time):
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

    oprint("{0} Crawled {1} urls {2}in {3:.2f} seconds".format(
            global_status, total_urls, error_summary, total_time),
            files=output_files)

    pages = {}

    if config.options.report_type == REPORT_TYPE_ERRORS:
        pages = site.error_pages
    elif config.options.report_type == REPORT_TYPE_ALL:
        pages = site.pages

    if pages:
        oprint("\n  Start URL(s): {0}".format(start_urls), files=output_files)

        for page in pages.values():
            oprint("\n  {0}: {1}".format(page.get_status_message(),
                    page.url_split.geturl()), files=output_files)
            for source in page.sources:
                oprint("    from {0}".format(source.origin.geturl()),
                        files=output_files)


def oprint(message, files):
    """Prints to a sequence of files."""
    for file in files:
        print(message, file=file)


def send_email(email_file, site, config):
    if config.subject:
        subject = config.subject
    else:
        if site.is_ok:
            subject = "SUCCESS - {0}".format(site.start_url_splits[0].geturl())
        else:
            subject = "ERROR - {0}".format(site.start_url_splits[0].geturl())

    if config.from_address:
        from_address = config.from_address
    else:
        from_address = "pylinkchecker@localhost"

    if not config.options.address:
        print("Email address must be specified when using smtp.")
        sys.exit(1)

    addresses = config.options.address.split(",")

    msg = EMAIL_HEADER.format(from_address, subject, ", ".join(addresses),
            PLAIN_TEXT, email_file.getvalue())

    smtpserver = smtplib.SMTP(options.smtp, options.port)

    if options.tls:
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo

    if options.smtp_username and options.smtp_password:
        smtpserver.login(options.smtp_username, options.smtp_password)

    smtpserver.sendmail(from_address, addresses, msg)

    smtpserver.close()
