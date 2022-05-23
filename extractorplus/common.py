# -*- coding: utf-8 -*-
# Copyright (C) 2019-2022 Digitalhigh <donate.to.digitalhigh@gmail.com>
#
# Based on Simple Extractor and Extractor Plugins:
# Copyright (C) 2015 Chris Yereaztian <chris.yereaztian@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of the Extractor Plus plugin and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import os.path

from pkg_resources import resource_filename


def get_resource(filename):
    return resource_filename(__package__, os.path.join('data', filename))
