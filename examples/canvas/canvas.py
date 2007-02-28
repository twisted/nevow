import os, string, random

from twisted.internet import task

from nevow import canvas, rend


DEBUG = False


try:
    words = open('/usr/share/dict/words').readlines()
except:
    words = open(os.path.join('.','files','words')).readlines()


## Some random helpers
rndpt = lambda w, h: (random.randint(-w/2, w/2), random.randint(-h/2, h/2))
rndrct = lambda w, h: rndpt(w, h) + rndpt(w, h)
rndtxt = lambda: ''.join([random.choice(string.letters) for x in range(random.randint(5, 10))])
rndp = lambda: (random.randint(0, 100), )*2
mv = lambda: random.choice( [1, -1, 2, -2, 3, -3, 4, -4, 5, -5] )


class Looper(object):
    def __init__(self, canvas):
        self.canvas = canvas
        self.stride = mv()
        self.looper = task.LoopingCall(self.loop)
        self.looper.start(0.25)

    def loop(self):
        if self.canvas.closed:
            self.looper.stop()
        else:
            self.perform()


class Textorizer(Looper):
    firstTime = True
    def __init__(self, T, w, h):
        self.T = T
        self.w = w
        self.h = h
        self.hstride = mv()
        Looper.__init__(self, T.canvas)

    def perform(self):
        T = self.T
        if not self.firstTime:
            hw = self.w/2
            hh = self.h/2
            if T.x < -hw or T.x+400>hw:
                self.hstride = -self.hstride
            if T.y < -hh or T.y+100>hh:
                self.stride = -self.stride
            T.move(T.x+self.hstride, T.y+self.stride)
        else:
            self.firstTime = False
            T.size(random.randint(9, 48))
            T.listFonts().addCallback(lambda fnts: T.font(random.choice(fnts)))


class Rotatorizer(Looper):
    angle = 0
    def perform(self):
        self.canvas.rotate(self.angle)
        self.angle += self.stride


class Alphaerizer(Looper):
    def __init__(self, canvas):
        canvas.alpha(random.randint(0, 100))
        Looper.__init__(self, canvas)

    def perform(self):
        self.canvas.alpha(self.canvas._alpha+self.stride)
        if self.canvas._alpha < 0 or self.canvas._alpha > 100:
            self.stride = -self.stride


class CanvasDemo(canvas.Canvas):
    def onload(self, canvas):
        """Demo of drawing with a CanvasSocket object.
        """
        ## Create a bunch of groups
        for x in xrange(random.randint(5, 15)):
            newGroup = canvas.group()
            if random.choice([True, False]):
                Alphaerizer(newGroup)
                self.manipulateACanvas(newGroup)
            else:
                newGroup.pen(2, 0, 100)
                newGroup.reposition(*rndpt(self.width, self.height))
                newGroup.move(-25, -25)
                newGroup.line(25, 25)
                newGroup.move(-25, 25)
                newGroup.line(25, -25)
                Rotatorizer(newGroup)

    def manipulateACanvas(self, canvas):
        canvas.reposition(*rndpt(self.width, self.height))
        canvas.S = S = canvas.sound('http://localhost/amen.mp3')
        S.play(timesLoop=5)
        for x in range(random.randint(1, 4)):
            canvas.pen( 
                random.randint(1, 10),
                random.randint(0, 0xffffff),
                random.randint(0, 100))
            canvas.move(*rndpt(self.width, self.height))
            choice = random.randint(0, 4)
            if choice == 0:
                canvas.line(*rndpt(self.width, self.height))
            elif choice == 1:
                canvas.fill(random.randint(0, 0xffffff), random.randint(0, 100))
                for x in range(random.randint(3, 20)):
                    if random.randint(0, 1):
                        canvas.line(*rndpt(self.width, self.height))
                    else:
                        canvas.curve(*rndrct(self.width, self.height))
                canvas.close()
            elif choice == 2:
                canvas.curve(*rndrct(self.width, self.height))
            elif choice == 3:
                T = canvas.text(random.choice(self.original), *(0,0,400,100))
                # This is an example of how you can hold on to drawing objects and continue to
                # draw on them later, because the CanvasSocket holds itself open until done() is called
                Textorizer(T, self.width, self.height)
            else:
                # This demo requires a folder of images which I don't want to put in
                # the nevow source. Hooking this up is left as an exercise for the reader.
                continue
                imgname = random.choice(os.listdir("flsh/images"))
                I = canvas.image('/images/%s' % imgname)
                I.scale(*rndp())
                I.alpha(random.randint(0, 100))
                rotate = random.randint(-180, 180)
                I.rotate(rotate)
                I.move(*rndpt(self.width, self.height))

    # See above comment
    #from nevow import static
    #child_images = static.File('images')

    def onMouseDown(self, canvas, x, y):
        canvas.x = x
        canvas.y = y
        canvas.pen(10, 0xDF34AB, 50)
        canvas.move(x-25, y-25)
        canvas.line(x+25, y+25)
        canvas.move(x+25, y-25)
        canvas.line(x-25, y+25)
        #canvas.S.play()

    def onKeyDown(self, canvas, key):
        if hasattr(canvas, 'x'):
            T = canvas.text(key, canvas.x, canvas.y, 200, 200)
            T.size(random.randint(9, 48))
            T.listFonts().addCallback(lambda fnts: T.font(random.choice(fnts)))
            canvas.x += 15


class Reloader(rend.Page):
    canvas = None
    def locateChild(self, ctx, segs):
        if segs == ('',):
            reload(__import__(__name__))
            self.canvas = CanvasDemo(words)
            self.canvas.addSlash = True
            return self.canvas, segs
        return self.canvas, segs


def createResource():
    if DEBUG:
        return Reloader()
    return CanvasDemo(words)
