#!/usr/bin/python
# You should modify 'prefix' variable

import os,sys

def run_with_cgi(application):
    """Stolen from WSGI PEP"""
    environ = dict(os.environ.items())
    environ['wsgi.input']        = sys.stdin
    environ['wsgi.errors']       = sys.stderr
    environ['wsgi.version']      = (1,0)
    environ['wsgi.multithread']  = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once']    = True

    if environ.get('HTTPS','off') in ('on','1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'

    headers_set = []
    headers_sent = []

    def write(data):
        if not headers_set:
             raise AssertionError("write() before start_response()")

        elif not headers_sent:
             # Before the first output, send the stored headers
             status, response_headers = headers_sent[:] = headers_set
             sys.stdout.write('Status: %s\r\n' % status)
             for header in response_headers:
                 sys.stdout.write('%s: %s\r\n' % header)
             sys.stdout.write('\r\n')

        sys.stdout.write(data)
        sys.stdout.flush()

    def start_response(status,response_headers,exc_info=None):
        global headers_sent
        if exc_info:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[0], exc_info[1], exc_info[2]
                else:
                    sys.stdout.write('content-type: text/plain\r\n')
                    sys.stdout.write('\r\n')
                    #headers_sent = True
                    headers_set[:] = [status,response_headers]
                    sys.stdout.write('except!')
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

################################## Nevow #################

from nevow import rend, loaders, url
from nevow import tags as T

class Index(rend.Page):

    addSlash = True

    def __init__(self, name='main'):
        rend.Page.__init__(self)
        self.name = name

    def render_name(self, ctx, data):
        return self.name

    def render_links(self, ctx, data):
        inner = [T.li[T.a(href=url.here.child(x))[x]] for x in ['a', 'b', 'c']]
        return T.ul[inner]

    def childFactory(self, ctx, name):
        return Index(self.name+'/'+name)

    docFactory = loaders.stan(
        T.html[
            T.head[T.title['Nevow wsgi Test cgi app']],
            T.body[
                T.h1(render=T.directive('name')),
                T.invisible(render=T.directive('links'))
            ]
        ]
    )


#########################################################



#########################################################



from nevow import wsgi
# Pages for test
#   1. Index() - Simple URL test
#   2. 
wsgiApp = wsgi.createWSGIApplication(Index())
run_with_cgi(wsgiApp)
