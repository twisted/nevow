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
