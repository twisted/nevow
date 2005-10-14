// Copyright (c) 2004 Divmod.
// See LICENSE for details.


// variables injected into the global namespace are:
//  cookie
//  port
//  prefix

// GLOBALS

var server = new XMLSocket();

var canvas = _root.createEmptyMovieClip('canvas', 0);

function sendEvent(evtTxt) {
    server.send(evtTxt); }

// The flash movie can control which event handlers are installed.
// The following names should be defined in the movie's namespace:

//  onKeyDown
//  onKeyUp
//  onMouseDown
//  onMouseUp
//  onMouseMove

if (onKeyDown) {
  Key.addListener(canvas);
  canvas.onKeyDown = function() {
    sendEvent('onKeyDown '+Key.getCode()); } }

if (onKeyUp) {
  canvas.onKeyUp = function() {
    sendEvent('onKeyUp '+Key.getCode()); } }

if (onMouseDown) {
  canvas.onMouseDown = function() {
    sendEvent('onMouseDown '+_root._xmouse+' '+_root._ymouse); } }

if (onMouseUp) {
  canvas.onMouseUp = function() {
    sendEvent('onMouseUp '+_root._xmouse+' '+_root._ymouse); } }

if (onMouseMove) {
  canvas.onMouseMove = function() {
    sendEvent('onMouseMove '+_root._xmouse+' '+_root._ymouse); } }


// RPC UTILITIES

function extractList(nodes) {
    var rv = [];
    for (i=0; i<nodes.length; i++) {
        rv.push(
            Number(nodes[i].attributes['v'])); }
    return rv; }

function extractDict(nodes) {
    var rv = {};
    for (i=0; i<nodes.length; i++) {
        var nod = nodes[i];
        var val = nod.attributes['v'];
        if (val == "matrixType") {
            rv[nod.attributes['k']] = val; }
        else {
            rv[nod.attributes['k']] = Number(val); } }
    return rv; }

function extractGroup(path) {
    var groupTarget = _root;
    var segments = path.split('.');
    for (var i = 0; i < segments.length; i++) {
        groupTarget = groupTarget[segments[i]]; }
    return groupTarget; }

// DRAWING APIS

function reposition(canvas, x, y) {
    canvas._x = Number(x);
    canvas._y = Number(y); }

function rotate(canvas, angle) {
    canvas._rotation = Number(angle); }

function alpha(canvas, percent) {
    canvas._alpha = Number(percent); }

function scale(canvas, x, y) {
    canvas._xscale = Number(x);
    canvas._yscale = Number(y); }

function swapGroup(canvas, other) {
    var groupTarget = extractGroup(other);
    canvas.swapDepths(groupTarget); }

function swapInt(canvas, other) {
    canvas.swapDepths(Number(other)); }

function gradient(canvas, type, colors, alphas, ratios, matrix) {
    var cl = extractList(colors);
    var al = extractList(alphas);
    var ra = extractList(ratios);
    var ma = extractDict(matrix);
    canvas.beginGradientFill(
        type, cl, al, ra, ma) }

function curve(canvas, controlX, controlY, anchorX, anchorY) {
    canvas.curveTo(
        Number(controlX),
        Number(controlY),
        Number(anchorX),
        Number(anchorY)); }

function fill(canvas, rgb, alpha) {
    canvas.beginFill(Number(rgb), Number(alpha)); }

function close(canvas) {
    canvas.endFill(); }

function move(canvas, x, y) {
    canvas.moveTo(Number(x), Number(y)); }

function line(canvas, x, y) {
	canvas.lineTo(Number(x), Number(y));	}

function pen(canvas, w, c, a) {
    if (a) {
        canvas.lineStyle(Number(w), Number(c), Number(a)) }
    else if (c) {
        canvas.lineStyle(Number(w), Number(c)); } 
    else if (w) {
        canvas.lineStyle(Number(w)); }
    else {
        canvas.lineStyle(); } }


function clear(canvas) {
    canvas.clear(); }

// TEXT APIS

function text(canvas, cookie, val, x, y, height, width) {
    canvas.createTextField(
        "T_" + cookie, Number(cookie), 
        Number(x), Number(y), Number(height), Number(width));
    var T = canvas["T_" + cookie]
    T.text = val;
    T.selectable = false;
//    T.background = true;
//    T.backgroundColor = 0xefefef;
    }

function changeText(canvas, cookie, val) {
    canvas["T_" + cookie].text = val; }

function moveText(canvas, cookie, x, y) {
    var T = canvas["T_" + cookie];
    T._x = Number(x);
    T._y = Number(y); }

function rotateText(canvas, cookie, angle) {
    var A = Number(angle);
    canvas["T_" + cookie]._rotation = A; }

function listFonts(canvas, identifier) {
    var fonts = TextField.getFontList();
    sendEvent(
        identifier + " " + fonts); }

function font(canvas, cookie, fn) {
    var T = canvas["T_" + cookie];
    var F = T.getTextFormat();
    F.font = fn;
    T.setTextFormat(F); }

function size(canvas, cookie, s) {
    var T = canvas["T_" + cookie];
    var F = T.getTextFormat();
    F.size = Number(s);
    T.setTextFormat(F); }

// GROUP APIs

function group(canvas, cookie) {
    canvas.createEmptyMovieClip('G_'+cookie, Number(cookie));
    var G = canvas['G_'+cookie]; }

function setMask(canvas, otherCanvas) {
    if (!otherCanvas) {
        canvas.setMask(null); }
    else {
        var G = extractGroup(otherCanvas);
        canvas.setMask(G); } }

function setVisible(canvas, visible) {
    if (visible == 'True') {
        canvas._visible = true; }
    else {
        canvas._visible = false; } }

// IMAGE APIs

function image(canvas, cookie, where) {
    canvas.createEmptyMovieClip("I_"+cookie, Number(cookie));
    var I = canvas["I_"+cookie];
    I.loadMovie(where); }

function moveImage(canvas, cookie, x, y) {
    var I = canvas["I_" + cookie];
    I._x = Number(x);
    I._y = Number(y); }

function scaleImage(canvas, cookie, x, y) {
    var I = canvas["I_" + cookie];
    I._xscale = Number(x);
    I._yscale = Number(y); }

function alphaImage(canvas, cookie, alpha) {
    var I = canvas["I_" + cookie];
    I._alpha = Number(alpha); }

function rotateImage(canvas, cookie, angle) {
    var T = canvas["I_" + cookie];
    T._rotation = Number(angle); }


// SOUND APIs

function sound(canvas, cookie, where, streaming) {
    var S = new Sound();
    canvas["S_"+cookie] = S;
    S.loadSound(where, Boolean(streaming));
    S.stop(); }

function playSound(canvas, cookie, offset, timesLoop) {
    var S = canvas["S_"+cookie]
    S.start(Number(offset), Number(timesLoop)); }

// SERVER GLUE

server.onXML = function(xml) {
	xml = xml.firstChild;
	var funcName = xml.attributes['n'];
	var func = eval(funcName);
	var parms = [];

    parms.push(
        extractGroup(xml.attributes['t']));

	for(i=0; i<xml.childNodes.length; i++) {
        if (xml.childNodes[i].attributes['v']){
            parms.push(
                xml.childNodes[i].attributes['v']); }
        else {
            parms.push(
                xml.childNodes[i].childNodes[0].childNodes); } }

	func.apply(groupTarget, parms); }

server.onConnect = function(success) {
	if (success) {
		server.send(
			"GET " + prefix + "canvas_socket/"+
			cookie+
			" HTTP/1.0\r\n\r\n"); } }

server.connect(null, port);
