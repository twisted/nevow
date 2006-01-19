
// import Divmod
// import Divmod.Runtime

Divmod.XML = {};
Divmod.XML.parseString = function(s) {
    return Divmod.Runtime.theRuntime.parseXHTMLString(s);
};
