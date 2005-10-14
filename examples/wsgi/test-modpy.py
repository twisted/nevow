# Modpython wsgi + Nevow
# You should modify 'prefix' variable

# The URL of this cgi script
prefix = 'http://localhost/test-modpy.py'


import os,sys
from mod_python import apache


def run_with_modpy(req, application):
    environ = dict(os.environ.items())
    environ['wsgi.input']        = req
    environ['wsgi.errors']       = sys.stderr
    environ['wsgi.version']      = (1,0)
    environ['wsgi.multithread']  = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once']    = True

    if environ.get('HTTPS','off') in ('on','1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'
        
    # mod_python has environment variables in 'req' object
    environ['PATH_INFO'] = req.path_info

    headers_set = []
    headers_sent = []

    def write(data):
        if not headers_set:
             raise AssertionError("write() before start_response()")

        elif not headers_sent:
            # Before the first output, send the stored headers
            status, response_headers = headers_sent[:] = headers_set
            req.headers_out['Status'] = status
            # log('status - %s' % status)
            from StringIO import StringIO
            for header in response_headers:
                key, value = header
                value = StringIO(value).read() # convert _apache string to python string
                if key == 'location':
                    # Perform an internal (apache) redirect
                    req.internal_redirect(value)
                # req.write('<li><b>'+str(key)+'</b>: '+str(value)+'</li>')
                if type(str(value)) is not type(str()):
                    raise 'oops'+ str(value)+str(type(str(value)))
                req.headers_out[str(key)] = str(value)
                
        req.write(data)
        req.flush()

    def start_response(status,response_headers,exc_info=None):
        global headers_sent
        if exc_info:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                exc_info = None     # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")
            
        headers_set[:] = [status,response_headers]
        return write

    result = application(environ, start_response)
    try:
        for data in result:
            if data:    # don't send headers until body appears
                write(data)
        if not headers_sent:
            write('')   # send headers now if body was empty
    finally:
        if hasattr(result,'close'):
            result.close()
    #TODO
    return apache.OK

################################## Nevow #################

from nevow import rend, loaders, url
from nevow import tags as T

# debug 
request = None
def log(st):
    pass
    #request.write('<br/><b>DEBUG</b>: %s' % st)

class Index(rend.Page):

    addSlash = True

    def __init__(self, name='main'):
        log('Creating instance - %s' % name)
        rend.Page.__init__(self)
        self.name = name

    def render_name(self, ctx, data):
        return self.name

    def render_links(self, ctx, data):
        inner = [T.li[T.a(href=url.here.child(x))[x]] for x in ['a', 'b', 'c']]
        return T.ul[inner]

    def childFactory(self, ctx, name):
        log('Looking child %s' % name)
        return Index(self.name+'/'+name)

    docFactory = loaders.stan(
        T.html[
            T.head[T.title['Nevow wsgi Test modpy app']],
            T.body[
                T.h1(render=T.directive('name')),
                T.invisible(render=T.directive('links'))
            ]
        ]
    )


#########################################################



#########################################################


def handler(req):
    global request
    request = req
    req.content_type = "text/html"
    from nevow import wsgi
    wsgiApp = wsgi.createWSGIApplication(Index(), prefix)
    return run_with_modpy(req, wsgiApp)
