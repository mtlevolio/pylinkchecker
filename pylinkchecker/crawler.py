# -*- coding: utf-8 -*-
"""
Contains the main crawling logic.
"""
from __future__ import unicode_literals, absolute_import

from pylinkchecker.models import get_parser


def execute_from_command_line():
    parser = get_parser()
    (options, args) = parser.parse_args()
