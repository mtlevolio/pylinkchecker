pylinkchecker
=============

:Version: 0.1

pylinkchecker is a simple crawler that traverses a web sites and reports errors
(e.g., 500 and 404 errors) encountered. The crawler can try to download
resources like images.


Requirements
------------

pylinkchecker requires beautifulsoup4. It should be installed automatically if
you use pip or easy_install. pylinkchecker has been tested on python 2.6, python
2.7, and python 3.3.


Optional Requirements
---------------------

These libraries must be installed to enable certain modes in pylinkchecker:

lxml
  beautifulsoup can use lxml to speed up the parsing of HTML pages. Because
  lxml requires C libraries, this is only an optional requirement.

gevent
  this non-blocking io library enables pylinkchecker to use green threads
  instead of processes or threads. gevent could potentially speed up the
  crawling speed on web sites with many small pages.


Installation
------------

::

  pip install pylinkchecker


Usage
-----

To be done


License
-------

This software is licensed under the `New BSD License`. See the `LICENSE` file
in the for the full license text. It includes the beautifulsoup library which
is licensed under the MIT license.