from zope.interface import implements, Interface
from twisted.python.components import registerAdapter
from nevow import athena, inevow, loaders, tags, util

class ICalculator(Interface):
    def buttonClicked(button):
        pass

class Calculator(object):

    validSymbols = '0123456789/*-=+.C'
    defaultExpression = u'0'
    errorExpression = u'E'

    def __init__(self):
        self.expression = self.defaultExpression

    def buttonClicked(self, symbol):
        # Remember ... never trust a browser
        if symbol not in self.validSymbols:
            raise ValueError('Invalid symbol')
        # Clear
        if symbol == 'C':
            self.expression = self.defaultExpression
            return self.expression
        # Check the expression is currently valid
        if self.expression == self.errorExpression:
            return self.expression
        # Evaluate the expression
        if symbol == '=':
            try:
                self.expression = unicode(eval(self.expression))
            except ZeroDivisionError:
                self.expression = self.errorExpression
            return self.expression
        # Replace of add to the expression
        if self.expression == self.defaultExpression:
            self.expression = symbol
        else:
            self.expression += symbol
        return self.expression

class CalculatorResource(athena.LivePage):
    """
    A "live" calculator.

    All buttons presses in the browser are sent to the server. The server
    evaluates the expression and sets the output in the browser.
    """
    addSlash = True
    docFactory = loaders.xmlfile(
        util.resource_filename('calculator', 'calculator.html')
        )

if __name__ == '__main__':

    import sys
    from twisted.internet import reactor
    from twisted.python import log
    from nevow import appserver

    def calculatorResourceFactory(original):
        return CalculatorResource(ICalculator, original)

    registerAdapter(calculatorResourceFactory, Calculator, inevow.IResource)

    log.startLogging(sys.stdout)
    calculator = Calculator()
    site = appserver.NevowSite(calculator)
    reactor.listenTCP(8080, site)
    reactor.run()
