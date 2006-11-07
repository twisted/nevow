"""
Tests for L{nevow.testutil} -- a module of utilities for testing Nevow
applications.
"""

from twisted.trial import unittest

from nevow import testutil


class TestFakeRequest(unittest.TestCase):

    def test_headers(self):
        """
        Check that one can get headers from L{testutil.FakeRequest} after they
        have been set with L{testutil.FakeRequest.setHeader}.
        """
        host = 'divmod.com'
        req = testutil.FakeRequest()
        req.setHeader('host', host)
        self.assertEqual(req.getHeader('host'), host)
