"""
Tests for L{nevow.testutil} -- a module of utilities for testing Nevow
applications.
"""

from twisted.trial.unittest import TestCase
from twisted.web.http import OK, BAD_REQUEST

from nevow.testutil import FakeRequest, renderPage
from nevow.url import root
from nevow.rend import Page
from nevow.loaders import stan


class TestFakeRequest(TestCase):

    def test_headers(self):
        """
        Check that one can get headers from L{FakeRequest} after they
        have been set with L{FakeRequest.setHeader}.
        """
        host = 'divmod.com'
        req = FakeRequest()
        req.setHeader('host', host)
        self.assertEqual(req.getHeader('host'), host)

    def test_urls(self):
        """
        Check that rendering URLs via L{renderPage} actually works.
        """
        class _URLPage(Page):
            docFactory = stan(
                root.child('foo'))

        def _checkForUrl(result):
            return self.assertEquals('http://localhost/foo', result)

        return renderPage(_URLPage()).addCallback(_checkForUrl)


    def test_defaultResponseCode(self):
        """
        Test that the default response code of a fake request is success.
        """
        self.assertEqual(FakeRequest().code, OK)


    def test_setResponseCode(self):
        """
        Test that the response code of a fake request can be set.
        """
        req = FakeRequest()
        req.setResponseCode(BAD_REQUEST)
        self.assertEqual(req.code, BAD_REQUEST)
