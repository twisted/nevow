import sys

from twisted.application import internet, service, app
from twisted.python import usage
from twisted.python.runtime import platform

from nevow import appserver
from nevow.livetrial import runner, testcase

if platform.isWinNT():
    from twisted.scripts import _twistw as twistd
else:
    from twisted.scripts import twistd

class Options(twistd.ServerOptions):
    def opt_port(self, value):
        """Specify the TCP port to which to bind the test server (defaults to 8080).
        """
        try:
            self['port'] = int(value)
        except ValueError:
            raise usage.UsageError("Invalid port: %r" % (value,))

    def parseArgs(self, *args):
        self['testmodules'] = args

    def postOptions(self):
        app.installReactor(self['reactor'])
        self['no_save'] = True
        self['nodaemon'] = True

        if 'port' not in self:
            self['port'] = 8080

        oldstdout = sys.stdout
        oldstderr = sys.stderr
        self._startLogging()

        self.suite = self._getSuite(self['testmodules'])
        self.application = self._constructApplication()
        self._startApplication()
        app.runReactorWithLogging(self, oldstdout, oldstderr)

    def _getSuite(self, modules):
        loader = testcase.TestLoader()
        suite = testcase.TestSuite('root')
        for module in modules:
            suite.addTest(loader.loadByName(module, True))
        return suite

    def _constructApplication(self):
        application = service.Application('Athena Livetest')
        site = appserver.NevowSite(runner.TestFrameworkRoot(self.suite))
        internet.TCPServer(self['port'], site).setServiceParent(application)
        return application

    def _startApplication(self):
        if not platform.isWinNT():
            twistd.startApplication(self, self.application)
        else:
            service.IService(self.application).privilegedStartService()
            app.startApplication(self.application, False)

    def _startLogging(self):
        if not platform.isWinNT():
            twistd.startLogging(self['logfile'], self['syslog'], self['prefix'], self['nodaemon'])
        else:
            twistd.startLogging('-')

def run():
    config = Options()
    try:
        config.parseOptions()
    except usage.error, ue:
        raise SystemExit, "%s: %s" % (sys.argv[0], ue)

if __name__ == '__main__':
    run()
