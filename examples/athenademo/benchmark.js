
// import Nevow.Athena

Nevow.Benchmarks = {};

function timer() {
    var d = new Date();
    return d.getSeconds() + ':' + d.getMilliseconds();
}

document.documentElement.insertBefore(
    document.createTextNode(timer()),
    document.documentElement.firstChild);

Nevow.Benchmarks.BenchmarkBase = Nevow.Athena.Widget.subclass('Nevow.Benchmarks.BenchmarkBase');
Nevow.Benchmarks.BenchmarkBase.methods(
    function starttime(self) {
        self._starttime = new Date();
    },

    function endtime(self) {
        var endtime = new Date();
        var starttime = self._starttime;
        delete self._starttime;
        Divmod.Runtime.theRuntime.setNodeContent(
            self.nodeByAttribute('class', 'timing-result'),
            '<span xmlns="http://www.w3.org/1999/xhtml">Seconds Elapsed: ' + ((endtime - starttime) / 1000.0) + "</span>");
    },

    function colorize(self, color) {
	self.node.style.color = color;
    });


Nevow.Benchmarks.InitializationBenchmark = Nevow.Benchmarks.BenchmarkBase.subclass('Nevow.Benchmarks.InitializationBenchmark');
Nevow.Benchmarks.InitializationBenchmark.methods(
    function __init__(self, node) {
	Nevow.Benchmarks.InitializationBenchmark.upcall(self, '__init__', node);
	self.starttime();
	self.colorize('yellow');
	var d = self.callRemote('activate');
	d.addCallback(function() { self.endtime(); self.colorize('green'); });
	d.addErrback(function() { self.endtime(); self.colorize('red'); });
    });


Nevow.Benchmarks.EvaluateBenchmark = Nevow.Benchmarks.BenchmarkBase.subclass('Nevow.Benchmarks.EvaluateBenchmark');
Nevow.Benchmarks.EvaluateBenchmark.methods(
    function __init__(self, node) {
        Nevow.Benchmarks.EvaluateBenchmark.upcall(self, '__init__', node);
    },

    function _evaluateRepeatedly(self, expr, times) {
        var d = Divmod.Defer.Deferred();
        function evaluateOnce() {
            // Divmod.Runtime.theRuntime.evaluate(expr);
            eval(expr);
            if (--times >= 0) {
                setTimeout(evaluateOnce, 0);
            } else {
                d.callback(null);
            }
        };
        evaluateOnce();
        return d;
    },

    function evaluateSomeThings(self) {
        var a = new Array();
        for (var i = 0; i < 1000; ++i) {
            a.push(["hello", {world: "how"}, "are", "you", "d", 0.1, "ng"]);
        }
        var expr = a.toSource();
        self.starttime();
        self.colorize('yellow');
        self._evaluateRepeatedly(expr, 100).addCallback(function() {
            self.endtime();
            self.colorize('green');
        }).addErrback(function() {
            self.endtime();
            self.colorize('red');
        });
    });
