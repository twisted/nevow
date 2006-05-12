from nevow import loaders, tags
from nevow.livetrial import testcase

class SetNodeContent(testcase.TestCase):
    jsClass = u'Divmod.Runtime.Tests.SetNodeContent'
    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['SetNodeContent'])

class AppendNodeContent(testcase.TestCase):
    jsClass = u'Divmod.Runtime.Tests.AppendNodeContent'
    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['AppendNodeContent'])

class AppendNodeContentScripts(testcase.TestCase):
    jsClass = u'Divmod.Runtime.Tests.AppendNodeContentScripts'
    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['AppendNodeContentScripts'])

class TraversalOrdering(testcase.TestCase):
    jsClass = u'Divmod.Runtime.Tests.TraversalOrdering'
    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))[
        'TraversalOrdering',
        tags.div(_class='container')[
            tags.div(_class='left_child')[
                tags.div(_class='left_grandchild')],
            tags.div(_class='right_child')[
                tags.div(_class='right_grandchild')]]])
