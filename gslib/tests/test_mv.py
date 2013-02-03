# Copyright 2013 Google Inc.
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

import gslib.tests.testcase as testcase
from gslib.tests.util import ObjectToURI as suri


class TestMv(testcase.GsUtilIntegrationTestCase):
  """Integration tests for mv command."""

  def test_moving(self):
    # Create two buckets, one with 2 objects and one with 0 objects, and verify.
    bucket1_uri = self.CreateBucket(test_objects=2)
    stdout = self.RunGsUtil(['ls', suri(bucket1_uri)], return_stdout=True)
    self.assertNumLines(stdout, 2)
    bucket2_uri = self.CreateBucket()
    stdout = self.RunGsUtil(['ls', suri(bucket2_uri)], return_stdout=True)
    self.assertNumLines(stdout, 0)

    # Move two objects from bucket1 to bucket2.
    objs = [suri(bucket1_uri.clone_replace_key(key))
            for key in bucket1_uri.list_bucket()]
    cmd = (['-m', 'mv'] + objs + [suri(bucket2_uri)])
    stderr = self.RunGsUtil(cmd, return_stderr=True)
    self.assertEqual(stderr.count('Copying'), 2)
    self.assertEqual(stderr.count('Removing'), 2)

    # Verify objects were moved.
    stdout = self.RunGsUtil(['ls', suri(bucket1_uri)], return_stdout=True)
    self.assertNumLines(stdout, 0)
    stdout = self.RunGsUtil(['ls', suri(bucket2_uri)], return_stdout=True)
    self.assertNumLines(stdout, 2)

    # Remove one of the objects.
    objs = [suri(bucket2_uri.clone_replace_key(key))
            for key in bucket2_uri.list_bucket()]
    obj1 = objs[0]
    self.RunGsUtil(['rm', obj1])

    # Verify there are now 1 and 0 objects.
    stdout = self.RunGsUtil(['ls', suri(bucket1_uri)], return_stdout=True)
    self.assertNumLines(stdout, 0)
    stdout = self.RunGsUtil(['ls', suri(bucket2_uri)], return_stdout=True)
    self.assertNumLines(stdout, 1)

    # Move the 1 remaining object back.
    objs = [suri(bucket2_uri.clone_replace_key(key))
            for key in bucket2_uri.list_bucket()]
    cmd = (['-m', 'mv'] + objs + [suri(bucket1_uri)])
    stderr = self.RunGsUtil(cmd, return_stderr=True)
    self.assertEqual(stderr.count('Copying'), 1)
    self.assertEqual(stderr.count('Removing'), 1)

    # Verify object moved.
    stdout = self.RunGsUtil(['ls', suri(bucket1_uri)], return_stdout=True)
    self.assertNumLines(stdout, 1)
    stdout = self.RunGsUtil(['ls', suri(bucket2_uri)], return_stdout=True)
    self.assertNumLines(stdout, 0)
