# -*- test-case-name: nevow.test.test_athena -*-

"""
twistd subcommand plugin for launching an athena widget server.
"""

from twisted.application.internet import TCPServer
from twisted.python.reflect import namedAny
from twisted.python.usage import Options, UsageError

from nevow.appserver import NevowSite
from nevow.athena import LivePage
from nevow.loaders import stan
from nevow.tags import html, head, title, body, div, directive


class ElementRenderingLivePage(LivePage):
    """
    Trivial LivePage which renders an instance of a particular element class.
    """
    docFactory = stan(html[
            head(render=directive('liveglue'))[
                title(render=directive('title'))],
            body[
                div(render=directive('element'))]])

    def __init__(self, element):
        LivePage.__init__(self)
        self.element = element


    def render_title(self, ctx, data):
        return ctx.tag[self.element.__class__.__name__]


    def render_element(self, ctx, data):
        self.element.setFragmentParent(self)
        return ctx.tag[self.element]



class Options(Options):
    """
    Command-line parameters for the athena widget twistd plugin.
    """
    def opt_port(self, portstr):
        """
        Specify the port number to listen on.
        """
        try:
            self['port'] = int(portstr)
        except ValueError:
            raise UsageError(
                "Specify an integer between 0 and 65535 as a port number.")
        if self['port'] >= 2 ** 16:
            raise UsageError(
                "Specify an integer between 0 and 65535 as a port number.")
        elif self['port'] < 0:
            raise UsageError(
                "Specify an integer between 0 and 65535 as a port number.")


    def opt_element(self, qualifiedName):
        """
        Specify the LiveElement or LiveFragment class to serve.
        """
        try:
            classObj = namedAny(qualifiedName)
        except (ValueError, AttributeError):
            raise UsageError("Specify a valid class name to --element")
        self['element'] = classObj()


    def postOptions(self):
        """
        Assign default values for those arguments not specified.
        """
        if 'port' not in self:
            self['port'] = 8080
        if 'element' not in self:
            raise UsageError("Specify a class name to --element")



def makeService(options):
    """
    @type options: C{dict}

    @param options: Configuration for the NevowSite to start.  Required
    keys are::

        C{'element'}: a LiveElement or LiveFragment instance.

        C{'port'}: an C{int} giving the port number to which to bind.

    """
    element = options['element']
    page = ElementRenderingLivePage(element)
    return TCPServer(options['port'], NevowSite(page))
