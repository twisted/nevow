
// import Nevow.Athena

Nevow.Benchmarks = {};

function timer() {
    var d = new Date();
    return d.getSeconds() + ':' + d.getMilliseconds();
}

document.documentElement.insertBefore(
    document.createTextNode(timer()),
    document.documentElement.firstChild);

Nevow.Benchmarks.InitializationBenchmark = Nevow.Athena.Widget.subclass();
Nevow.Benchmarks.InitializationBenchmark.method(
    function __init__(self, node) {
	Nevow.Benchmarks.InitializationBenchmark.upcall(self, '__init__', node);
	self.stamptime();
	self.colorize('yellow');
    });

Nevow.Benchmarks.InitializationBenchmark.method(
    function loaded(self) {
	self.stamptime();
	self.colorize('purple');
	var d = self.callRemote('activate');
	d.addCallback(function() { self.stamptime(); self.colorize('green'); });
	d.addErrback(function() { self.stamptime(); self.colorize('red'); });
    });

Nevow.Benchmarks.InitializationBenchmark.method(
    function stamptime(self) {
	self.node.appendChild(document.createTextNode(' ' + timer()));
    });

Nevow.Benchmarks.InitializationBenchmark.method(
    function colorize(self, color) {
	self.node.style.color = color;
    });
