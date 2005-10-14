from nevow import loaders, rend

class HelloWorld(rend.Page):
    addSlash = True
    docFactory = loaders.xmlfile('helloworld.html')

