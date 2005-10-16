from zope.interface import implements
from nevow import athena, inevow, loaders, tags, util


class Calculator(athena.LivePage):
    """
    A "live" calculator.

    All buttons presses in the browser are sent to the server. The server
    evaluates the expression and sets the output in the browser.
    """

    docFactory = loaders.xmlfile(
        util.resource_filename('calculator', 'calculator.html')
        )

    validSymbols = '0123456789/*-=+.C'
    defaultExpression = u'0'
    errorExpression = u'E'
    
    def __init__(self, *a, **kw):
        super(Calculator, self).__init__(*a, **kw)
        self.expression = self.defaultExpression
    
    def child_(self, ctx):
        return self
        
    def remote_buttonClicked(self, ctx, symbol):      
        """
        Calculator button pressed.
        """
        # Remember ... never trust a browser
        if symbol not in self.validSymbols:
            raise ValueError('Invalid symbol')
        # Clear
        if symbol == 'C':
            self.expression = self.defaultExpression  
            return self.updateOutput()
        # Check the expression is currently valid
        if self.expression == self.errorExpression:
            return
        # Evaluate the expression
        if symbol == '=':
            try:
                self.expression = unicode(eval(self.expression))
            except ZeroDivisionError:
                self.expression = self.errorExpression
            return self.updateOutput()
        # Replace of add to the expression
        if self.expression == self.defaultExpression:
            self.expression = symbol
        else:
            self.expression += symbol
        return self.updateOutput()

    def updateOutput(self):
        """
        Send the current expression to the browser.
        """
        return self.callRemote('setOutput', self.expression)


if __name__ == '__main__':

    import sys
    from twisted.internet import reactor
    from twisted.python import log
    from nevow import appserver

    class Root(object):
        """
        Strange root resource that only exists to create a Calculator
        LivePage for each request.
        """
        implements(inevow.IResource)
        calculatorFactory = athena.LivePageFactory(Calculator)
        def locateChild(self, ctx, segments):
            return self.makeCalculator(ctx), segments
        def renderHTTP(self, ctx):
            return self.makeCalculator(ctx)
        def makeCalculator(self, ctx):
            return self.calculatorFactory.clientFactory(ctx)

    log.startLogging(sys.stdout)
    site = appserver.NevowSite(Root())
    reactor.listenTCP(8080, site)
    reactor.run()
