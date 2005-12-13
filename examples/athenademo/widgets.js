
if (typeof WidgetDemo == 'undefined') {
    WidgetDemo = {};
}

WidgetDemo.Clock = Nevow.Athena.Widget.subclass();
WidgetDemo.Clock.prototype.start = function() {
    this.callRemote('start');
};

WidgetDemo.Clock.prototype.stop = function() {
    this.callRemote('stop');
};

WidgetDemo.Clock.prototype.setTime = function(toWhat) {
    Divmod.debug("Setting time " + toWhat);
    var time = Nevow.Athena.NodeByAttribute(this.node, "class", "clock-time");
    Divmod.debug("On " + time);
    time.innerHTML = toWhat;
    Divmod.debug("Hooray");
};
