# Copyright 2011 Google Inc. All Rights Reserved.
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

# Get the system logging module, not our local logging module.
from __future__ import absolute_import

import logging
import os.path
import re

from gslib.command import Command
from gslib.command import COMMAND_NAME
from gslib.command import COMMAND_NAME_ALIASES
from gslib.command import FILE_URIS_OK
from gslib.command import MAX_ARGS
from gslib.command import MIN_ARGS
from gslib.command import PROVIDER_URIS_OK
from gslib.command import SUPPORTED_SUB_ARGS
from gslib.command import URIS_START_ARG
from gslib.exception import CommandException
from gslib.help_provider import HELP_NAME
from gslib.help_provider import HELP_NAME_ALIASES
from gslib.help_provider import HELP_ONE_LINE_SUMMARY
from gslib.help_provider import HELP_TEXT
from gslib.help_provider import HELP_TYPE
from gslib.help_provider import HelpType
import gslib.tests as tests
from gslib.util import NO_MAX


# For Python 2.6, unittest2 is required to run the tests. If it's not available,
# display an error if the test command is run instead of breaking the whole
# program.
try:
  from gslib.tests.util import GetTestNames
  from gslib.tests.util import unittest
except ImportError as e:
  if 'unittest2' in str(e):
    unittest = None
    GetTestNames = None
  else:
    raise


_detailed_help_text = ("""
<B>SYNOPSIS</B>
  gsutil test [-l] [-u] [-f] [command command...]


<B>DESCRIPTION</B>
  The gsutil test command runs the gsutil unit tests and integration tests.
  The unit tests use an in-memory mock storage service implementation, while
  the integration tests send requests to the production service.

  To run both the unit tests and integration tests, run the command with no
  arguments:

    gsutil test

  To run the unit tests only (which run quickly):

    gsutil test -u

  To see additional details for test failures:

    gsutil -d test

  To have the tests stop running immediately when an error occurs:

    gsutil test -f

  To run tests for one or more individual commands add those commands as
  arguments. For example, the following command will run the cp and mv command
  tests:

    gsutil test cp mv

  To list available tests, run the test command with the -l argument:

    gsutil test -l

  The tests are defined in the code under the gslib/tests module. Each test
  file is of the format test_[name].py where [name] is the test name you can
  pass to this command. For example, running "gsutil test ls" would run the
  tests in "gslib/tests/test_ls.py".

  You can also run an individual test class or function name by passing the
  the test module followed by the class name and optionally a test name. For
  example, to run the an entire test class by name:

    gsutil test naming.GsutilNamingTests

  or an individual test function:

    gsutil test cp.TestCp.test_streaming

  You can list the available tests under a module or class by passing arguments
  with the -l option. For example, to list all available test functions in the
  cp module:

    gsutil test -l cp


<B>OPTIONS</B>
  -l          List available tests.

  -u          Only run unit tests.

  -f          Exit on first test failure.
""")


def MakeCustomTestResultClass(total_tests):
  """Creates a closure of CustomTestResult.

  Args:
    total_tests: The total number of tests being run.

  Returns:
    An instance of CustomTestResult.
  """

  class CustomTestResult(unittest.TextTestResult):
    """A subclass of unittest.TextTestResult that prints a progress report."""

    def startTest(self, test):
      super(CustomTestResult, self).startTest(test)
      if self.dots:
        id = '.'.join(test.id().split('.')[-2:])
        message = ('\r%d/%d finished - E[%d] F[%d] s[%d] - %s' % (
            self.testsRun, total_tests, len(self.errors),
            len(self.failures), len(self.skipped), id))
        message = message[:73]
        message = message.ljust(73)
        self.stream.write('%s - ' % message)

  return CustomTestResult


class TestCommand(Command):
  """Implementation of gsutil test command."""

  # Command specification (processed by parent class).
  command_spec = {
      # Name of command.
      COMMAND_NAME: 'test',
      # List of command name aliases.
      COMMAND_NAME_ALIASES: [],
      # Min number of args required by this command.
      MIN_ARGS: 0,
      # Max number of args required by this command, or NO_MAX.
      MAX_ARGS: NO_MAX,
      # Getopt-style string specifying acceptable sub args.
      SUPPORTED_SUB_ARGS: 'ufl',
      # True if file URIs acceptable for this command.
      FILE_URIS_OK: True,
      # True if provider-only URIs acceptable for this command.
      PROVIDER_URIS_OK: False,
      # Index in args of first URI arg.
      URIS_START_ARG: 0,
  }
  help_spec = {
      # Name of command or auxiliary help info for which this help applies.
      HELP_NAME: 'test',
      # List of help name aliases.
      HELP_NAME_ALIASES: [],
      # Type of help:
      HELP_TYPE: HelpType.COMMAND_HELP,
      # One line summary of this help.
      HELP_ONE_LINE_SUMMARY: 'Run gsutil tests',
      # The full help text.
      HELP_TEXT: _detailed_help_text,
  }

  # Command entry point.
  def RunCommand(self):
    if not unittest:
      raise CommandException('On Python 2.6, the unittest2 module is required '
                             'to run the gsutil tests.')

    failfast = False
    list_tests = False
    if self.sub_opts:
      for o, _ in self.sub_opts:
        if o == '-u':
          tests.util.RUN_INTEGRATION_TESTS = False
        elif o == '-f':
          failfast = True
        elif o == '-l':
          list_tests = True

    test_names = sorted(GetTestNames())
    if list_tests and not self.args:
      print 'Found %d test names:' % len(test_names)
      print ' ', '\n  '.join(sorted(test_names))
      return 0

    # Set list of commands to test if supplied.
    if self.args:
      commands_to_test = []
      for name in self.args:
        if name in test_names or name.split('.')[0] in test_names:
          commands_to_test.append('gslib.tests.test_%s' % name)
        else:
          commands_to_test.append(name)
    else:
      commands_to_test = ['gslib.tests.test_%s' % name for name in test_names]

    # Installs a ctrl-c handler that tries to cleanly tear down tests.
    unittest.installHandler()

    loader = unittest.TestLoader()

    if commands_to_test:
      try:
        suite = loader.loadTestsFromNames(commands_to_test)
      except (ImportError, AttributeError) as e:
        raise CommandException('Invalid test argument name: %s' % e)

    if list_tests:
      suites = [suite]
      test_names = []
      while suites:
        suite = suites.pop()
        for test in suite:
          if isinstance(test, unittest.TestSuite):
            suites.append(test)
          else:
            test_names.append(test.id().lstrip('gslib.tests.test_'))
      print 'Found %d test names:' % len(test_names)
      print ' ', '\n  '.join(sorted(test_names))
      return 0

    if logging.getLogger().getEffectiveLevel() <= logging.INFO:
      verbosity = 1
    else:
      verbosity = 2
      logging.disable(logging.ERROR)

    total_tests = suite.countTestCases()
    resultclass = MakeCustomTestResultClass(total_tests)

    runner = unittest.TextTestRunner(verbosity=verbosity,
                                     resultclass=resultclass, failfast=failfast)
    ret = runner.run(suite)
    if ret.wasSuccessful():
      return 0
    return 1
