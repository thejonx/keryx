#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: mac9416
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os
import sys

def compare(status1, status2, older=True):
    """Takes two status file strings and returns only packages in both (choosing
       the older version of the two by default)
    """
    # Make each string a dict of package names : package entries
    status = []
    status2 = dict([[get_property(x, 'Package'), x] for x in status2.split('\n\n')])

    for entry in status1.split('\n\n'):
        if entry.strip() == '': continue  # Empty strings. Who needs them.
        pkg_name = get_property(entry, 'Package')
        if pkg_name in status2.keys():
            ver1 = get_property(entry, 'Version')
            ver2 = get_property(status2[pkg_name], 'Version')
            if DpkgVersion(ver1) < DpkgVersion(ver2) or DpkgVersion(ver1) == DpkgVersion(ver2):
                status.append(entry)
            elif DpkgVersion(ver1) > DpkgVersion(ver2):
                status.append(status2[pkg_name])

    return '\n\n'.join(status)

def get_property(pkg_str, prop):
    """Takes a status file package entry and package property; returns value for
       that property
    """
    for line in pkg_str.split('\n'):
        if line.startswith(prop):
            return line.split(':')[-1].strip()


############ Minideblib's Version Compare Code ############


# -*- coding: UTF-8 -*-
# Small changes by Steve Kowalik, GPL (C) 2005
# Scott James Remnant told me the license is MIT
"""Parse and compare Debian version strings.

This module contains a class designed to sit in your Python code pretty
naturally and represent a Debian version string.  It implements various
special methods to make dealing with them sweet.
"""

__author__    = "Scott James Remnant <scott@netsplit.com>"


import re


# Regular expressions make validating things easy
valid_epoch = re.compile(r'^[0-9]+$')
valid_upstream = re.compile(r'^[0-9][A-Za-z0-9+:.~-]*$')
valid_revision = re.compile(r'^[A-Za-z0-9+.~]+$')

# Character comparison table for upstream and revision components
cmp_table = "~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-.:"


class VersionError(Exception): pass
class BadInputError(VersionError): pass
class BadEpochError(BadInputError): pass
class BadUpstreamError(BadInputError): pass
class BadRevisionError(BadInputError): pass

class DpkgVersion(object):
    """
    Debian version number.

    This class is designed to be reasonably transparent and allow you to write code like:

    >>> s.version >= '1.100-1'

    The comparison will be done according to Debian rules, so '1.2' will compare lower.

    Properties:
     - epoch: Epoch
     - upstream: Upstream version
     - revision: Debian/local revision
    """

    def __init__(self, ver):
        """Parse a string or number into the three components."""
        self.epoch = None
        self.upstream = None
        self.revision = None

        ver = str(ver)
        if not len(ver):
            raise BadInputError, "Input cannot be empty"

        # Epoch is component before first colon
        idx = ver.find(":")
        if idx != -1:
            self.epoch = ver[:idx]
            if not len(self.epoch):
                raise BadEpochError, "Epoch cannot be empty"
            if not valid_epoch.search(self.epoch):
                raise BadEpochError, "Bad epoch format"
            ver = ver[idx+1:]

        # Revision is component after last hyphen
        idx = ver.rfind("-")
        if idx != -1:
            self.revision = ver[idx+1:]
            if not len(self.revision):
                raise BadRevisionError, "Revision cannot be empty"
            if not valid_revision.search(self.revision):
                raise BadRevisionError, "Bad revision format"
            ver = ver[:idx]

        # Remaining component is upstream
        self.upstream = ver
        if not len(self.upstream):
            raise BadUpstreamError, "Upstream version cannot be empty"
        if not valid_upstream.search(self.upstream):
            raise BadUpstreamError, "Bad upstream version format"

        if self.epoch is not None:
            self.epoch = int(self.epoch)

    def getWithoutEpoch(self):
        """Return the version without the epoch."""
        str = self.upstream
        if self.revision is not None:
            str += "-%s" % (self.revision,)
        return str

    without_epoch = property(getWithoutEpoch)

    def __str__(self):
        """Return the class as a string for printing."""
        str = ""
        if self.epoch is not None:
            str += "%d:" % (self.epoch,)
        str += self.upstream
        if self.revision is not None:
            str += "-%s" % (self.revision,)
        return str

    def __repr__(self):
        """Return a debugging representation of the object."""
        return "<%s epoch: %r, upstream: %r, revision: %r>" \
               % (self.__class__.__name__, self.epoch,
                  self.upstream, self.revision)

    def __cmp__(self, other):
        """Compare two Version classes."""
        other = DpkgVersion(other)

        # Compare epochs only if they are not equal.
        if self.epoch != other.epoch:
            # Special cases for braindead packages
            sepoch = self.epoch
            oepoch = other.epoch
            if sepoch is None:
                sepoch = 0
            if oepoch is None:
                oepoch = 0
            result = cmp(sepoch, oepoch)
            if result != 0: return result

        result = deb_cmp(self.upstream, other.upstream)
        if result != 0: return result

        result = deb_cmp(self.revision or "", other.revision or "")
        if result != 0: return result

        return 0

    def is_native(self):
        native = False
        if not self.revision:
            native = True
        return native

def strcut(str, idx, accept):
    """Cut characters from str that are entirely in accept."""
    ret = ""
    while idx < len(str) and str[idx] in accept:
        ret += str[idx]
        idx += 1

    return (ret, idx)

def deb_order(str, idx):
    """Return the comparison order of two characters."""
    if idx >= len(str):
        return 0
    elif str[idx] == "~":
        return -1
    else:
        return cmp_table.index(str[idx])

def deb_cmp_str(x, y):
    """Compare two strings in a deb version."""
    idx = 0
    while (idx < len(x)) or (idx < len(y)):
        result = deb_order(x, idx) - deb_order(y, idx)
        if result < 0:
            return -1
        elif result > 0:
            return 1

        idx += 1

    return 0

def deb_cmp(x, y):
    """Implement the string comparison outlined by Debian policy."""
    x_idx = y_idx = 0
    while x_idx < len(x) or y_idx < len(y):
        # Compare strings
        (x_str, x_idx) = strcut(x, x_idx, cmp_table)
        (y_str, y_idx) = strcut(y, y_idx, cmp_table)
        result = deb_cmp_str(x_str, y_str)
        if result != 0: return result

        # Compare numbers
        (x_str, x_idx) = strcut(x, x_idx, "0123456789")
        (y_str, y_idx) = strcut(y, y_idx, "0123456789")
        result = cmp(int(x_str or "0"), int(y_str or "0"))
        if result != 0: return result

    return 0

############ End Minideblib's Version Compare Code ############


if __name__ == '__main__':
    # Open the status files and put the strings in a list.
    status_list = []
    for status in sys.argv[1:]:
        try:
            # Assume the full directory is given.
            status_list.append(open(status, 'rb').read())
        except IOError:
            # Then again, maybe it's in the current directory.
            status_list.append(open(os.path.join(os.getcwd(), status), 'rb').read())

    status1 = status_list.pop(0)

    for status2 in status_list:
        status1 = compare(status1, status2)
        print len(status1)

    open(os.path.join(os.getcwd(), 'StatusMerge_out'), 'wb').write(status1)
