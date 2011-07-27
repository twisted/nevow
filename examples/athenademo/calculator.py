# Copyright (c) 2008 Divmod.  See LICENSE for details.

"""
Demonstration of an Athena Widget which accepts input from the browser and
sends back responses.
"""

import sys

from twisted.python.filepath import FilePath
from twisted.python import log
from twisted.internet import reactor

from nevow.athena import LivePage, LiveElement, expose
from nevow.loaders import xmlfile
from nevow.appserver import NevowSite

# Handy helper for finding external resources nearby.
sibling = FilePath(__file__).sibling


class Calculator(object):
    """
    The model object for the calculator demo.  This is the object which
    actually knows how to perform calculations.

    @ivar expression: A C{str} giving the current expression which has been
        entered into the calculator.  For example, if the buttons '3', '5', and
        '+' have been pressed (in that order), C{expression} will be C{'35+'}.
    """
    defaultExpression = u'0'
    errorExpression = u'E'

    def __init__(self):
        self.expression = self.defaultExpression


    def buttonClicked(self, symbol):
        """
        Change the current expression by performing the operation indicated by
        C{symbol} (clearing it or computing it) or by extending it (with a
        digit or operator).

        @param symbol: C{'C'} to clear the expression, C{'='} to evaluate the
            expression, or one of C{'0'}-C{'9'}.

        @rtype: C{unicode}
        @return: The expression after interpreting the new symbol.
        """
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



class CalculatorElement(LiveElement):
    """
    A "live" calculator.

    All buttons presses in the browser are sent to the server. The server
    evaluates the expression and sets the output in the browser.

    @ivar validSymbols: A C{str} giving all of the symbols which the browser is
        allowed to submit to us.  Input is checked against this before being
        submitted to the model.

    @ivar calc: A L{Calculator} which will be used to handle all inputs and
        generate computed outputs.
    """
    docFactory = xmlfile(sibling('calculator.html').path, 'CalculatorPattern')

    jsClass = u"CalculatorDemo.Calculator"

    validSymbols = '0123456789/*-=+.C'

    def __init__(self, calc):
        LiveElement.__init__(self)
        self.calc = calc


    def buttonClicked(self, symbol):
        """
        Accept a symbol from the browser, perform input validation on it,
        provide it to the underlying L{Calculator} if appropriate, and return
        the result.

        @type symbol: C{unicode}
        @rtype: C{unicode}
        """
        # Remember ... never trust a browser
        if symbol not in self.validSymbols:
            raise ValueError('Invalid symbol')
        return self.calc.buttonClicked(symbol)
    expose(buttonClicked)



class CalculatorParentPage(LivePage):
    """
    A "live" container page for L{CalculatorElement}.
    """
    docFactory = xmlfile(sibling('calculator.html').path)

    def __init__(self, *a, **kw):
        LivePage.__init__(self)
        # Update the mapping of known JavaScript modules so that the
        # client-side code for this example can be found and served to the
        # browser.
        self.jsModules.mapping[u'CalculatorDemo'] = sibling(
            'calculator.js').path


    def render_calculator(self, ctx, data):
        """
        Replace the tag with a new L{CalculatorElement}.
        """
        c = CalculatorElement(Calculator())
        c.setFragmentParent(self)
        return c



def main():
    log.startLogging(sys.stdout)
    site = NevowSite(CalculatorParentPage(calc=Calculator()))
    reactor.listenTCP(8080, site)
    reactor.run()



if __name__ == '__main__':
    main()
