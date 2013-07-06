pylinkchecker
=============

:Version: 0.1

pylinkchecker is a standalone and pure python crawler that traverses a web sites
and reports errors (e.g., 500 and 404 errors) encountered. The crawler can try
to download resources like images.


Requirements
------------

pylinkchecker does not require external libraries if executed with python 2.x.
It requires beautifulsoup4 if executed with python 3.x.
It has been tested on python 2.6, python 2.7, and python 3.3.


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
      -p PASSWORD, --password=PASSWORD
      -U, --unique
      -t TYPES, --types=TYPES
      -T TIMEOUT, --timeout=TIMEOUT
      -P, --progress

    Performance Options:
      These options can impact the performance of the crawler.

      -w WORKERS, --workers=WORKERS
      -m MODE, --mode=MODE
      -R PARSER, --parser=PARSER

    Output Options:
      These options change the output of the crawler.

      -f FORMAT, --format=FORMAT
      -o OUTPUT, --output=OUTPUT
      -W WHEN, --when=WHEN
      -E REPORT_TYPE, --report-type=REPORT_TYPE


License
-------

This software is licensed under the `New BSD License`. See the `LICENSE` file
in the for the full license text. It includes the beautifulsoup library which
is licensed under the MIT license.