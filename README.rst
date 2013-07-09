pylinkchecker
=============

:Version: 0.1

pylinkchecker is a standalone and pure python link checker and crawler that
traverses a web site and reports errors (e.g., 500 and 404 errors) encountered.
The crawler can also download resources such as images, scripts and
stylesheets.

pylinkchecker's performance can be improved by installing additional libraries
that require a C compiler, but these libraries are optional.

We created pylinkchecker so that it could be executed in environments without
access to a compiler (e.g., Microsoft Windows, some *nix production
environments) or with an old version of python (e.g., Centos).

pylinkchecker is highly modular and has many configuration options, but the
only required parameter is the starting url.

.. image:: https://api.travis-ci.org/auto123/pylinkchecker.png


Requirements
------------

pylinkchecker does not require external libraries if executed with python 2.x.
It requires beautifulsoup4 if executed with python 3.x. It has been tested on
python 2.6, python 2.7, and python 3.3.


Optional Requirements
---------------------

These libraries can be installed to enable certain modes in pylinkchecker:

lxml
  beautifulsoup can use lxml to speed up the parsing of HTML pages. Because
  lxml requires C libraries, this is only an optional requirement.

gevent
  this non-blocking io library enables pylinkchecker to use green threads
  instead of processes or threads. gevent could potentially speed up the
  crawling speed on web sites with many small pages.

cchardet
  this library speeds up the detection of document encoding.


Installation
------------

::

  pip install pylinkchecker


Usage
-----

::

  Usage: pylinkcheck.py [options] URL ...

  Options:
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    -V VERBOSE, --verbose=VERBOSE

    Crawler Options:
      These options modify the way the crawler traverses the site.

      -O, --test-outside  fetch resources from other domains without crawling
                          them
      -H ACCEPTED_HOSTS, --accepted-hosts=ACCEPTED_HOSTS
                          comma-separated list of additional hosts to crawl
                          (e.g., example.com,subdomain.another.com)
      -i IGNORED_PREFIXES, --ignore=IGNORED_PREFIXES
                          comma-separated list of host/path prefixes to ignore
                          (e.g., www.example.com/ignore_this_and_after/)
      -u USERNAME, --username=USERNAME
                          username to use with basic HTTP authentication
      -p PASSWORD, --password=PASSWORD
                          password to use with basic HTTP authentication
      -t TYPES, --types=TYPES
                          Comma-separated values of tags to look for when
                          crawlinga site. Default (and supported types):
                          a,img,link,script
      -T TIMEOUT, --timeout=TIMEOUT
                          Seconds to wait before considering that a page timed
                          out
      -P, --progress      Prints crawler progress in the console

    Performance Options:
      These options can impact the performance of the crawler.

      -w WORKERS, --workers=WORKERS
                          Number of workers to spawn
      -m MODE, --mode=MODE
                          Types of workers: thread (default), process, or green
      -R PARSER, --parser=PARSER
                          Types of HTML parse: html.parser (default) or lxml

    Output Options:
      These options change the output of the crawler.

      -f FORMAT, --format=FORMAT
                          Format of the report: plain
      -o OUTPUT, --output=OUTPUT
                          Path of the file where the report will be printed.
      -W WHEN, --when=WHEN
                          When to print the report. error (default, only if a
                          crawling error occurs) or always
      -E REPORT_TYPE, --report-type=REPORT_TYPE
                          Type of report to print: errors (default, summary and
                          erroneous links), summary, all (summary and all
                          links)
      -c, --console       Prints report to the console in addition to other
                          output options such as file or email.

    Email Options:
      These options allows the crawler to send a report by email.

      -a ADDRESS, --address=ADDRESS
                          Comma-separated list of email addresses used to send a
                          report
      --from=FROM_ADDRESS
                          Email address to use in the from field of the email
                          (optional)
      -s SMTP, --smtp=SMTP
                          Host of the smtp server
      --port=PORT         Port of the smtp server (optional)
      --tls               Use TLS with the email server.
      --subject=SUBJECT   Subject of the email (optional)
      --smtp-username=SMTP_USERNAME
                          Username to use with the smtp server (optional)
      --smtp-password=SMTP_PASSWORD
                          Password to use with the smtp server (optional)


License
-------

This software is licensed under the `New BSD License`. See the `LICENSE` file
in the for the full license text. It includes the beautifulsoup library which
is licensed under the MIT license.
