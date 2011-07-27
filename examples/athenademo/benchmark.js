
// import Nevow.Athena

function timer() {
    var d = new Date();
    return d.getSeconds() + ':' + d.getMilliseconds();
}

document.documentElement.insertBefore(
    document.createTextNode(timer()),
    document.documentElement.firstChild);

Nevow.Benchmarks.InitializationBenchmark = Nevow.Athena.Widget.subclass('Nevow.Benchmarks.InitializationBenchmark');
Nevow.Benchmarks.InitializationBenchmark.methods(
    function __init__(self, node) {
	Nevow.Benchmarks.InitializationBenchmark.upcall(self, '__init__', node);
	self.stamptime();
	self.colorize('yellow');
    },

    function loaded(self) {
	self.stamptime();
	self.colorize('purple');
	var d = self.callRemote('activate');
	d.addCallback(function() { self.stamptime(); self.colorize('green'); });
	d.addErrback(function() { self.stamptime(); self.colorize('red'); });
    },

    function stamptime(self) {
	self.node.appendChild(document.createTextNode(' ' + timer()));
    },

    function colorize(self, color) {
	self.node.style.color = color;
    });
