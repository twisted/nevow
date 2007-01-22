# Copyright (c) 2007 Divmod, Inc.
# See LICENSE for details.

"""
Tests for DOM-independent JavaScript functionality included in Athena.
"""

from nevow.testutil import JavaScriptTestCase


class JSUnitTests(JavaScriptTestCase):
    def test_jsunit(self):
        return 'Divmod.Test.TestUnitTest'


    def test_deferred(self):
        return 'Divmod.Test.TestDeferred'


    def test_base(self):
        return 'Divmod.Test.TestBase'


    def test_livetrial(self):
        return 'Divmod.Test.TestLivetrial'


    def test_inspect(self):
        return 'Divmod.Test.TestInspect'


    def test_object(self):
        return 'Divmod.Test.TestObject'
