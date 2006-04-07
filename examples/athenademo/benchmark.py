
from __future__ import division

from twisted.python import filepath

from nevow import tags, loaders, athena


class InitializationBenchmark(athena.LiveFragment):
    jsClass = u'Nevow.Benchmarks.InitializationBenchmark'

    docFactory = loaders.stan(
        tags.div(render=tags.directive('liveFragment'))[
            "Initialization Benchmark",
            " ",
            tags.span(class_='timing-result')])

    def __init__(self, page):
        super(InitializationBenchmark, self).__init__()
        self.setFragmentParent(page)


    def activate(self):
        pass
    athena.expose(activate)



class EvaluateBenchmark(athena.LiveFragment):
    jsClass = u'Nevow.Benchmarks.EvaluateBenchmark'

    docFactory = loaders.stan(
        tags.div(render=tags.directive('liveFragment'))[
            "Divmod.Runtime.Platform.evaluate() Benchmark",
            tags.button[athena.handler(event='onclick', handler='evaluateSomeThings'),
                        "Evaluate"],
            " ",
            tags.span(class_='timing-result')])

    def __init__(self, page):
        super(EvaluateBenchmark, self).__init__()
        self.setFragmentParent(page)



class Benchmark(athena.LivePage):
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue')),
        tags.body(render=tags.directive('body'))])

    def __init__(self, maxNodes, maxDepth):
        self.maxNodes = maxNodes
        self.maxDepth = maxDepth
        super(Benchmark, self).__init__()

        here = filepath.FilePath(__file__).parent().child('benchmark.js')

        self.jsModules.mapping.update({
            'Nevow.Benchmarks': here.path})

    def render_body(self, ctx, data):
        outermost = tags.div(style='border: solid thin black;')
        for j in range(self.maxNodes // self.maxDepth):
            top = t = tags.div()
            for i in range(self.maxDepth):
                m = tags.div()
                t[m]
                t = m
            t[InitializationBenchmark(self)]
            outermost[top]
        yield outermost

        yield tags.div(style='border: solid thin black;')[EvaluateBenchmark(self)]
