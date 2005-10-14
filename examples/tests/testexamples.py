from nevow import livetest


all_suites = dict(
    most_basic=[
        ('visit', '/most_basic/', ''),
        ('assert', 'foo', 'foo'),
        ('follow', 'foo', ''),
        ('assert', 'heading', 'You are in Foo'),
        ('follow', 'baz', ''),
        ('assert', 'heading', 'You are in Baz')],
    hellostan=[
        ('visit', '/hellostan/', ''),
        ('assert', 'body', 'Welcome to the wonderful world of Nevow!')],
    hellohtml=[
        ('visit', '/hellohtml/', ''),
        ('assert', 'body', 'Welcome to the wonderful world of Nevow!')],
    simple=[
        ('visit', '/simple/', ''),
        ('assert', 'count', '1'),
        ('visit', '/simple/', ''),
        ('assert', 'count', '2'),
        ('visit', '/simple/reset', ''),
        ('assert', 'reset', 'Count reset')],
    simplehtml=[
        ('visit', '/simplehtml/', ''),
        ('assert', 'count', '1'),
        ('visit', '/simplehtml/', ''),
        ('assert', 'count', '2'),
        ('visit', '/simplehtml/reset', ''),
        ('assert', 'reset', 'Count reset')],
    tables=[
        ('visit', '/tablehtml/', ''),
        ('assert', 'firstHeader', 'First Column'),
        ('assert', 'secondHeader', 'Second Column'),
        ('assert', 'firstFooter', 'First Footer'),
        ('assert', 'secondFooter', 'Second Footer')],
    disktemplates_stan=[
        ('visit', '/disktemplates_stan/', ''),
        ('assert', 'header', 'Welcome')],
    disktemplates=[
        ('visit', '/disktemplates/', ''),
        ('assert', 'header', 'Welcome')],
    children=[
        ('visit', '/children/', ''),
        ('follow', 'foo', ''),
        ('assert', 'name', 'foo'),
        ('follow', 'child', ''),
        ('assert', 'parentName', 'foo'),
        ('visit', '/children/', ''),
        ('follow', 'bar', ''),
        ('assert', 'name', 'bar'),
        ('follow', 'child', ''),
        ('assert', 'parentName', 'bar'),
        ('visit', '/children/', ''),
        ('follow', 'd1', ''),
        ('assert', 'name', '1'),
        ('follow', 'child', ''),
        ('assert', 'parentName', '1'),
        ('visit', '/children/', ''),
        ('follow', 'd2', ''),
        ('assert', 'name', '2'),
        ('follow', 'child', ''),
        ('assert', 'parentName', '2'),
        ('visit', '/children/', ''),
        ('follow', 'd3', ''),
        ('assert', 'name', '3'),
        ('follow', 'child', ''),
        ('assert', 'parentName', '3'),
        ('visit', '/children/', ''),
        ('follow', 'd4', ''),
        ('assert', 'name', '4'),
        ('visit', '/children/', ''),
        ('follow', 'd5', ''),
        ('assert', 'name', '5'),
        ('visit', '/children/', ''),
        ('follow', 'd6/7', ''),
        ('assert', 'name', '6/7')],
    objcontainer=[
        ('visit', '/objcontainer/', ''),
        ],
    manualform=[
        ('visit', '/manualform/', ''),
        ],
    advanced_manualform=[
        ('visit', '/advanced_manualform/', ''),
        ],
    formpost=[
        ('visit', '/formpost/', ''),
        ],
    formpost2=[
        ('visit', '/formpost2/', ''),
        ],
    db=[
        ('visit', '/db/', ''),
        ],
    http_auth=[
        ('visit', '/http_auth/', ''),
        ],
    guarded=[
        ('visit', '/guarded/', ''),
        ],
    guarded2=[
        ('visit', '/guarded2/', ''),
        ],
    logout_guard=[
        ('visit', '/logout_guard/', ''),
        ],
    logout_guard2=[
        ('visit', '/logout_guard2/', ''),
        ],
    customform=[
        ('visit', '/customform/', ''),
        ],
    formbuilder=[
        ('visit', '/formbuilder/', ''),
        ],
    simple_irenderer=[
        ('visit', '/simple_irenderer/', ''),
        ],
    irenderer=[
        ('visit', '/irenderer/', ''),
        ],
    tree=[
        ('visit', '/tree/', ''),
        ],
    i18n=[
        ('visit', '/i18n/', ''),
        ],
    xmli18n=[
        ('visit', '/xmli18n/', ''),
        ],
    # Tag Library Examples
    calendar=[
        ('visit', '/calendar/', ''),
        ],
    tabbed=[
        ('visit', '/tabbed/', ''),
        ],
    progress=[
        ('visit', '/progress/', ''),
        ],
    ## TODO: There are many more tests to be written here, but it is boring
)

live_suites = dict(
    ## Now the fun stuff: The livepage example tests.
liveanimal=[
        ('visit', '/liveanimal/?fresh=true', ''),
        ('assert', 'question', 'I give up. What is the animal, and what question describes it?'),
        ('submit', 'new-question', {'animal': "Monkey", 'new-question': 'is it crazy'}),
        ('assert', 'question', 'is it crazy'),
        ('click', 'yes-response', ''),
        ('assert', 'question', 'Is it Monkey?'),
        ('click', 'no-response', ''),
        ('assert', 'question', 'I give up. What is the animal, and what question describes it?'),
        ('submit', 'new-question', {'animal': 'Mongoose', 'new-question': 'does it eat snakes'}),
        ('assert', 'question', 'is it crazy'),
        ('click', 'yes-response', ''),
        ('assert', 'question', 'does it eat snakes'),
        ('click', 'yes-response', ''),
        ('assert', 'question', 'Is it Mongoose?'),
        ('click', 'yes-response', ''),
        ('assert', 'question', 'I win!'),
        ('click', 'start-over', ''),
        ('assert', 'question', 'is it crazy')
    ],
#chatola=[
#    ('visit', '/chatola/', ''),
#    ('submit', 'topicform', {'change-topic': 'Hello, world!'}),
#    ('submit', 'inputform', {'inputline': 'Greetings humans of earth'}),
#    ('submit', 'inputform', {'inputline': 'Take me to your leader'}),
#]
)



def createResource(whichOne=None):
    if whichOne is None:
        suite = []
        for subsuite in all_suites.values():
            suite.extend(subsuite)
        return livetest.Tester(suite)

    return livetest.Tester(all_suites[whichOne])


def createLiveSuite(whichOne=None):
    suite = []
    for subsuite in live_suites.values():
        suite.extend(subsuite)
    return livetest.Tester(suite)


