// import Nevow.Athena
// import Divmod.Runtime

CalculatorDemo.Calculator = Nevow.Athena.Widget.subclass("CalculatorDemo.Calculator");
CalculatorDemo.Calculator.methods(
    /**
     * Handle click events on any of the calculator buttons.
     */
    function buttonClicked(self, node) {
        var symbol = node.value;
        d = self.callRemote("buttonClicked", symbol);
        d.addCallback(
            function(expression) {
                var output = self.nodeById("output");
                output.replaceChild(
                    document.createTextNode(expression),
                    output.firstChild);
            });
        return false;
    });
