// -*- test-case-name: nevow.test.test_javascript.JSUnitTests.test_init -*-

// import Divmod.UnitTest
// import Nevow.Athena

Nevow.Test.TestInit.InitTests = Divmod.UnitTest.TestCase.subclass(
    'Nevow.Test.TestInit.InitTests');
Nevow.Test.TestInit.InitTests.methods(
    /**
     * Bootstrapping the Nevow.Athena module should set its 'livepageId'
     * attribute.
     */
    function test_bootstrap(self) {
        var notAthena = {};
        var SOME_ID = 'asdfjkl;';
        notAthena.bootstrap = Nevow.Athena.bootstrap;
        notAthena.bootstrap(SOME_ID);
        self.assertIdentical(notAthena.livepageId, SOME_ID);
    });
