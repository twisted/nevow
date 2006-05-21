import string
import urllib

from zope.interface import implements

from twisted.internet import defer
from twisted.python import failure
from twisted.application import strports
from twisted.application import service
from twisted.python import components
from twisted.web import util
from twisted.cred import portal
from twisted.cred import checkers
from twisted.cred import credentials
from twisted.cred import error

from nevow import inevow
from nevow import loaders
from nevow import rend
from nevow import appserver
from nevow import static
from nevow import url
from nevow import guard
from nevow.tags import *

from formless import annotate
from formless import iformless
from formless import webform

#=============================================================================
# Domain Objects
#=============================================================================
class User(object):
    """ultra-basic domain object"""
    def __init__(self, username, password, email, role="USER"):
        self.username = username
        self.password = password
        self.email = email
        self.role = role

    def __repr__(self):
        return "UserObject id: %d, %s"%(id(self), self.__dict__)

class UserDictDB(object):
    """In memory data-manager for User objects"""
    def __init__(self):
        self.users = {}

    def createUser(self, username, password, email, role=None):
        #XXX--should check for duplicates
        if not role:
            role = "USER"
        user = User(username, password, email, role)
        self.users[username] = user
        return user

    def deleteUser(self, username):
        del self.users[username]

    def findAllUsers(self):
        return self.users.values()

    def findUser(self, username):
        return self.users.get(username)

#=============================================================================
# Formless Interfaces
#=============================================================================
class ICreateUser(annotate.TypedInterface):
    """createUser is an autocallable method to create a new user in the userDB"""
    def createUser(
        self,
        request=annotate.Request(),
        username=annotate.String(
            label="Username: ",
            description="Unique system name for this user.",
            required=True),
        password=annotate.Password(
            label="Password: ",
            description="Password for this user. Used in authentication.",
            required=True),
        email=annotate.String(
            label="Email: ",
            description="Primary email address for this user."),
        role=annotate.Choice(
            label="Role: ",
            #description="Role for this user. Choices are: USER, ADMIN",
            #show how you can inline stan tags in the description--cool!
            description=span["Role for this user. Choices are: ",
                             strong["USER, ADMIN"]],
            choices=["USER","ADMIN"],
            default="USER")):
        """Create User:

        Create a new User
        """
        pass

    createUser = annotate.autocallable(createUser, action="Create")

class IEditUser(annotate.TypedInterface):
    """used in edit screens. we can only edit the email address,
    not the username"""
    email = annotate.String(
        label="Email: ",
        description="Primary email address for this user.")
    password = annotate.Password(
        label="Password: ",
        description="Password for this user. Used in authentication.")


class IDeleteUser(annotate.TypedInterface):
    """deleteUser is an autocallable method to delete a user in the userDB"""
    def deleteUser(self, request=annotate.Request()):
        """Delete User:

        Delete this User.
        """
        pass

    deleteUser = annotate.autocallable(deleteUser, action="Delete")

class ILogout(annotate.TypedInterface):
    """Call this to logout and destroy the current session"""
    def logout(self, request=annotate.Request()):
        """Logout:

        Sorry to see you go. Please visit again.
        """
        pass

    logout = annotate.autocallable(logout, action="logout")

#=============================================================================
# Pages
#=============================================================================
class ICurrentUser(components.Interface):
    """The current logged-in user object
    """

class IUserManager(components.Interface):
    """The user manager object
    """

class NotLoggedIn(rend.Page):
    """The resource that is returned when you are not logged in"""

    addSlash = True
    
    docFactory = loaders.stan(html[
        head[title["Not Logged In"]],
        body[
            p[
              """Welcome to the wonderful world of the UserDB app.""",
              br(),
              """Login to begin. (Hint: admin's password is admin, foo's password
              is foo, can you guess what bar's password is? ;-)"""
            ],
            form(action=guard.LOGIN_AVATAR, method='post')[
                table[
                    tr[
                        td[ "Username:" ],
                        td[ input(type='text',name='username') ],
                    ],
                    tr[
                        td[ "Password:" ],
                        td[ input(type='password',name='password') ],
                    ]
                ],
                input(type='submit'),
                p,
            ]
        ]
    ])

class Logout(rend.Page):
    implements(ILogout)

    def logout(self, request):
        request.getSession().expire()
        request.setComponent(iformless.IRedirectAfterPost, "/"+guard.LOGOUT_AVATAR)

    docFactory = loaders.stan(html[webform.renderForms()])

class UserPage(rend.Page):
    implements(IEditUser, IDeleteUser)

    def __init__(self, user):
        rend.Page.__init__(self)
        self.user = user

    def beforeRender(self, ctx):
        #get user, usermanager from the session
        self.currentUser = inevow.ISession(ctx).getComponent(ICurrentUser)
        self.userManager = inevow.ISession(ctx).getComponent(IUserManager)

    def setEmail(self, newEmail):
        self.user.email = newEmail
    email = property(lambda self: self.user.email, setEmail)

    def setPassword(self, newPassword):
        self.user.password = newPassword
    password = property(lambda self: self.user.password, setPassword)

    def deleteUser(self, request):
        self.userManager = request.session.getComponent(IUserManager)
        self.userManager.deleteUser(self.user.username)
        request.setComponent(iformless.IRedirectAfterPost, "/")

    def canModify(self):
        #determine our capabilities
        if self.currentUser.role == "ADMIN":
            return True
        if self.currentUser.username == self.user.username:
            return True
        return False

    def render_desc(self, ctx, data):
        args = inevow.IRequest(ctx).args
        view = args.get('action', ['view'])[0]
        if not self.canModify():
            #if they don't have required role, bump to "view"
            #regardless of what they passed in
            view = "view"

        if view == "view":
            msg = "Viewing attributes for user: %s"
        elif view == "edit":
            msg = "Editing attributes for user: %s"
        elif view == "delete":
            msg = "Deleting user: %s"
        else:
            msg = "Unknown action command on user: %s"
        return msg%self.user.username

    def render_viewSelector(self, context, data):
        args = inevow.IRequest(context).args
        view = args.get('action', ['view'])[0]
        if not self.canModify():
            view = "view"
        actionRenderer = ''

        if view == 'view':
            if not self.canModify():
                #if they don't have required role, don't show
                #edit/delete to them
                selector = ""
            else:
                selector = "View | ", a(href=url.here.add('action','edit'))[ "Edit | " ], a(href=url.here.add('action','delete'))[ "Delete" ]
            actionRenderer = context.onePattern('view')() # get one copy of the view pattern
        elif view == 'edit':
            selector = a(href=url.here.add('action','view'))["View"], " | Edit |", a(href=url.here.add('action','delete'))[ "Delete" ]
            actionRenderer = context.onePattern('edit')() # get one copy of the edit pattern
            actionRenderer[webform.renderForms(bindingNames=['password'])],
            actionRenderer[webform.renderForms(bindingNames=['email'])],
        elif view == 'delete':
            selector = a(href=url.here.add('action','view'))["View"], a(href=url.here.add('action','edit'))[ "| Edit" ], " | Delete"
            actionRenderer = context.onePattern('delete')() # get one copy of the delete pattern
            actionRenderer[webform.renderForms(bindingNames=['deleteUser'])],
        else:
            return "Unknown view: ",view

        return selector, actionRenderer


    def render_userDetail(self, context, data):
        return ul[
            li["username: ",self.user.username],
            li["email: ", self.user.email],
            ]

    docFactory = loaders.stan(html[
    head[
        link(href="/webform_css", rel="stylesheet")
        ],
    body[
        p[
            a(href=url.here.parent())["Up"]
        ],
        br(),
        a(href="/logout")["logout"],
        br(),
        render_desc,
        br(),
        div(render=render_viewSelector)[
            #only one of the patterns below will be
            #rendered based on the "action" param passed
            #in the request (default is "view")
            p(pattern="view")[
              render_userDetail
            ],
            p(pattern="edit"),
            p(pattern="delete")
        ]
    ]
    ])

class UserBrowserPage(rend.Page):
    implements(ICreateUser)

    addSlash = True
    
    # Fixed name children
    child_logout = Logout()

    def __init__(self, um, user):
        rend.Page.__init__(self)
        self.userManager = um
        self.user = user #user we are logged in as

    def setupSession(self, ctx):
        #need to place the user, usermanager in the session
        inevow.ISession(ctx).setComponent(ICurrentUser, self.user)
        inevow.ISession(ctx).setComponent(IUserManager, self.userManager)

    def beforeRender(self, ctx):
        self.setupSession(ctx)

    def childFactory(self, ctx, name):
        #make sure our child nodes have access to these session objects
        self.setupSession(ctx)

        # name == the username of the user in the database.
        user = self.userManager.findUser(name)
        if user is None:
            return None

        #return page for a particular user object
        return UserPage(user)

    def createUser(self, request, username, password, email, role):
        self.userManager.createUser(username, password, email, role=role)
        request.setComponent(iformless.IRedirectAfterPost, "/")

    def data_getAllUsers(self, context, data):
        users = self.userManager.findAllUsers()
        return users

    def render_greeting(self, context, data):
        return "Welcome to the UserDB browser, %s."%self.user.username

    def render_user(self, context, data):
        user = data
        #determine our capabilities
        canModify = False
        if self.user.role == "ADMIN":
            canModify =  True
        if self.user.username == user.username:
            canModify =  True

        if canModify:
            return context.tag[
                user.username, " [ ",
                a(href=user.username+"?action=view")[" view "]," | ",
                a(href=user.username+"?action=edit")[ "edit" ]," | ",
                a(href=user.username+"?action=delete")[ "delete" ]," ]"
                ]
        else:
            return context.tag[
                user.username, " [ ",
                a(href=user.username+"?action=view")[" view "]," ] "
                ]


    def render_createForm(self, context, data):
        #only people in ADMIN role can create new users
        if self.user.role == "ADMIN":
            return webform.renderForms()
        else:
            return ""

    child_webform_css = webform.defaultCSS

    docFactory = loaders.stan(html[
        head[
          link(href="/webform_css", rel="stylesheet")
        ],
        body[
          render_greeting,
          br(),
          a(href="/logout")["logout"],
          br(),
          p[
            span["Existing users:"]
          ],
          ul(data=directive("getAllUsers"), render=directive("sequence"))[
            li(pattern="item", render=render_user)
          ],
          render_createForm
        ]])

#=============================================================================
# Cred/Auth/Realm
#=============================================================================
def noLogout():
    return None

class SimpleChecker:
    """
    A simple checker implementation. Delegates storage/retrieval to userdb object
    """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, userdb):
        self.userdb = userdb

    #implements ICredentialChecker
    def requestAvatarId(self, credentials):
        """Return the avatar id of the avatar which can be accessed using
        the given credentials.

        credentials will be an object with username and password attributes
        we need to raise an error to indicate failure or return a username
        to indicate success. requestAvatar will then be called with the avatar
        id we returned.
        """
        user = self.userdb.findUser(credentials.username)
        if user is not None:
            return defer.maybeDeferred(
                credentials.checkPassword, user.password).addCallback(
                self._cbPasswordMatch, credentials.username)
        else:
            print "No user named: ",credentials.username
            raise error.UnauthorizedLogin()

    def _cbPasswordMatch(self, matched, username):
        if matched:
            return username
        else:
            print "password didn't match: ",username
            return failure.Failure(error.UnauthorizedLogin())

class SimpleRealm:
    """A simple implementor of cred's IRealm.
    For web, this gives us the LoggedIn page.
    """
    implements(portal.IRealm)

    def __init__(self, userdb):
        #we need this to pass into UserDB page
        self.userdb = userdb

    #implements IRealm
    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is inevow.IResource:
                # do web stuff
                if avatarId is checkers.ANONYMOUS:
                    resc = NotLoggedIn()
                    resc.realm = self
                    return (inevow.IResource, resc, noLogout)
                else:
                    user = self.userdb.findUser(avatarId)
                    resc = UserBrowserPage(self.userdb, user)
                    resc.realm = self
                    return (inevow.IResource, resc, noLogout)

        raise NotImplementedError("Can't support that interface.")

#=============================================================================
# Initialization
#=============================================================================
def main():
    userdb = UserDictDB()
    userdb.users["admin"] = User("admin", "admin", "admin@blah.com", role="ADMIN")
    userdb.users["foo"] = User("foo", "foo", "foo@blah.com")
    userdb.users["bar"] = User("bar", "bar", "bar@blah.com")


    realm = SimpleRealm(userdb)
    ptl = portal.Portal(realm)
    myChecker = SimpleChecker(userdb)
    # Allow anonymous access.  Needed for access to NotLoggedIn
    ptl.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)
    # Allow users registered in the userdb
    ptl.registerChecker(myChecker)

    site = appserver.NevowSite(
        resource=guard.SessionWrapper(ptl)
    )
    return strports.service("8080", site)

application = service.Application("UserManager1")
main().setServiceParent(application)
