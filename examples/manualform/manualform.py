# Demonstrates one way of manually handling form post. This example uses a
# "pretend" segment, _submit, for the form to post to (the action attribute).


from nevow import loaders, page, tags as T, url


SUBMIT = '_submit'


class Page(page.Page):

    addSlash = True

    def locateChild(self, req, segments):

        # Handle the form post
        if segments[0] == SUBMIT:
            # Just print out the name
            print '*** name:', req.arg('name')
            # Redirect away from the POST
            return url.URL.fromContext(req), ()

        return page.Page.locateChild(self, req, segments)

    docFactory = loaders.stan(
        T.html[
            T.body[
                T.form(action=url.here.child(SUBMIT), method="post")[
                    T.label['Name:'], T.input(type="text", name="name"),
                    ],
                ],
            ]
        )

