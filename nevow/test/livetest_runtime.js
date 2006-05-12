
// import Nevow.Athena.Test
// import Divmod.Runtime

Divmod.Runtime.Tests.AppendNodeContent = Nevow.Athena.Test.TestCase.subclass('AppendNodeContent');
Divmod.Runtime.Tests.AppendNodeContent.methods(
    function run(self) {
        var html = '<div xmlns="http://www.w3.org/1999/xhtml">foo</div>';
        Divmod.Runtime.theRuntime.appendNodeContent(self.node, html);
        self.assertEquals(self.node.lastChild.tagName.toLowerCase(), 'div');
        self.assertEquals(self.node.lastChild.childNodes[0].nodeValue, 'foo');
        self.node.removeChild(self.node.lastChild);
    });

Divmod.Runtime.Tests.SetNodeContent = Nevow.Athena.Test.TestCase.subclass('SetNodeContent');
Divmod.Runtime.Tests.SetNodeContent.methods(
    function run(self) {
        var html = '<div xmlns="http://www.w3.org/1999/xhtml">foo</div>';
        Divmod.Runtime.theRuntime.setNodeContent(self.node, html);
        self.assertEquals(self.node.childNodes.length, 1);
        self.assertEquals(self.node.firstChild.tagName.toLowerCase(), 'div');
        self.assertEquals(self.node.firstChild.childNodes[0].nodeValue, 'foo');
    });

Divmod.Runtime.Tests.AppendNodeContentScripts = Nevow.Athena.Test.TestCase.subclass('AppendNodeContentScripts');
Divmod.Runtime.Tests.AppendNodeContentScripts.methods(
    function run(self) {
        Divmod.Runtime.Tests.AppendNodeContentScripts.runCount = 0;
        var html = (
            '<div xmlns="http://www.w3.org/1999/xhtml">' +
                '<script type="text/javascript">Divmod.Runtime.Tests.AppendNodeContentScripts.runCount++;</script>' +
                '<script type="text/javascript">Divmod.Runtime.Tests.AppendNodeContentScripts.runCount++;</script>' +
                '<script type="text/javascript">Divmod.Runtime.Tests.AppendNodeContentScripts.runCount++;</script>' +
           '</div>');
        Divmod.Runtime.theRuntime.appendNodeContent(self.node, html);
        self.assertEquals(Divmod.Runtime.Tests.AppendNodeContentScripts.runCount, 3);
    });


Divmod.Runtime.Tests.TraversalOrdering = Nevow.Athena.Test.TestCase.subclass('Divmod.Runtime.Tests.TraversalOrdering');
Divmod.Runtime.Tests.TraversalOrdering.methods(
    function run(self) {
        var classes = [];
        Divmod.Runtime.theRuntime.traverse(
            self.node,
            function(node) {
                if (node.className) {
                    classes.push(node.className);
                }
                return Divmod.Runtime.Platform.DOM_DESCEND;
            });

        self.assertEquals(classes[1], 'container');
        self.assertEquals(classes[2], 'left_child');
        self.assertEquals(classes[3], 'left_grandchild');
        self.assertEquals(classes[4], 'right_child');
        self.assertEquals(classes[5], 'right_grandchild');
    });
