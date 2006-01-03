
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
    '__init__',
    function(self, node) {
	Nevow.Benchmarks.InitializationBenchmark.upcall(self, '__init__', node);
	self.node.style.color = 'yellow';
	self.node.appendChild(document.createTextNode(' ' + timer()));
    });

Nevow.Benchmarks.InitializationBenchmark.method(
    'loaded',
    function(self) {
	self.node.style.color = 'green';
	self.node.appendChild(document.createTextNode(' ' + timer()));
    });

