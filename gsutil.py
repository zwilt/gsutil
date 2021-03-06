#!/usr/bin/env python
# coding=utf8
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Wrapper module for running gslib.__main__.main() from the command line."""

import os
import sys
import warnings


if not (2, 6) <= sys.version_info[:3] < (3,):
  sys.exit('gsutil requires python 2.6 or 2.7.')


def _OutputAndExit(message):
  sys.stderr.write('%s\n' % message)
  sys.exit(1)


GSUTIL_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
if not GSUTIL_DIR:
  _OutputAndExit('Unable to determine where gsutil is installed. Sorry, '
                 'cannot run correctly without this.\n')

# The wrapper script adds all third_party libraries to the Python path, since
# we don't assume any third party libraries are installed system-wide.
THIRD_PARTY_DIR = os.path.join(GSUTIL_DIR, 'third_party')


# Filter out "module was already imported" warnings that get printed after we
# add our bundled version of modules to the Python path.
warnings.filterwarnings('ignore', category=UserWarning,
                        message=r'.* httplib2 was already imported from')
warnings.filterwarnings('ignore', category=UserWarning,
                        message=r'.* oauth2client was already imported from')


# List of third-party libraries. The first element of the tuple is the name of
# the directory under third_party and the second element is the subdirectory
# that needs to be added to sys.path.
THIRD_PARTY_LIBS = [
    ('python-gflags', ''),
    ('google-api-python-client', ''),
    ('httplib2', 'python2'),
    ('boto', ''),
    ('socksipy-branch', ''),
    ('retry-decorator', ''),
]
for libdir, subdir in THIRD_PARTY_LIBS:
  if not os.path.isdir(os.path.join(THIRD_PARTY_DIR, libdir)):
    _OutputAndExit(
        'There is no %s library under the gsutil third-party directory (%s).\n'
        'The gsutil command cannot work properly when installed this way.\n'
        'Please re-install gsutil per the installation instructions.' % (
            libdir, THIRD_PARTY_DIR))
  sys.path.insert(0, os.path.join(THIRD_PARTY_DIR, libdir, subdir))

def RunMain():
  import gslib.__main__
  sys.exit(gslib.__main__.main())

if __name__ == '__main__':
  RunMain()
