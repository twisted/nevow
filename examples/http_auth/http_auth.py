
"""
Example of using HTTP Auth directly to require authentication before
rendering a page for a client.

This is an example of extremely low-level authentication.  Most applications
are better served by using L{nevow.guard} instead of manually managing HTTP
Auth.  See the C{guarded/} example for more information.
"""

try:
    from twisted.web import http
except ImportError:
    from twisted.protocols import http

from nevow import rend, loaders, tags, inevow

class AuthorizationRequired(rend.Page):
    ## We are a directory-like resource because we are at the root
    addSlash = True
    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)
        username, password = request.getUser(), request.getPassword()
        if (username, password) == ('', ''):
            request.setHeader('WWW-Authenticate', 'Basic realm="Whatever"')
            request.setResponseCode(http.UNAUTHORIZED)
            return "Authentication required."
        ## They provided a username and password, so let's let them in! horray
        self.data_username, self.data_password = username, password
        return rend.Page.renderHTTP(self, ctx)

    docFactory = loaders.stan(tags.html[
    tags.body[
        tags.h1["Welcome user!"],
        tags.div["You said: ",
            tags.span(data=tags.directive('username'), render=str),
            " ",
            tags.span(data=tags.directive('password'), render=str)]]])

