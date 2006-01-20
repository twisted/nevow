
// import Nevow.Athena

if (typeof WidgetDemo == 'undefined') {
    WidgetDemo = {};
}

WidgetDemo.Clock = Nevow.Athena.Widget.subclass('WidgetDemo.Clock');
WidgetDemo.Clock.methods(
    function start(self) {
        self.callRemote('start');
    },

    function stop(self) {
        self.callRemote('stop');
    },

    function setTime(self, toWhat) {
        Divmod.debug("clock", "Setting time " + toWhat);
        var time = Nevow.Athena.NodeByAttribute(self.node, "class", "clock-time");
        Divmod.debug("clock", "On " + time);
        time.innerHTML = toWhat;
        Divmod.debug("clock", "Hooray");
    });
