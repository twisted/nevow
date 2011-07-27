
// import Nevow.Athena

WidgetDemo.Clock = Nevow.Athena.Widget.subclass('WidgetDemo.Clock');
WidgetDemo.Clock.methods(
    function start(self, node, event) {
        self.callRemote('start');
        return false;
    },

    function stop(self, node, event) {
        self.callRemote('stop');
        return false;
    },

    function setTime(self, toWhat) {
        Divmod.debug("clock", "Setting time " + toWhat);
        var time = Nevow.Athena.NodeByAttribute(self.node, "class", "clock-time");
        Divmod.debug("clock", "On " + time);
        time.innerHTML = toWhat;
        Divmod.debug("clock", "Hooray");
    });
