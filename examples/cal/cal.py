from nevow import rend, loaders, tags as t
from nevow.taglibrary import cal

class Calendar(rend.Page):
    addSlash = True
    year = None
    month = None
    def __init__(self, year=None, month=None):
        if year is not None and month is not None:
            self.year = year
            self.month = month

    def locateChild(self, ctx, segments):
        if len(segments) >= 2:
            year, month = segments[:2]
            return Calendar(int(year), int(month)), segments[2:]
        return super(Calendar, self).locateChild(ctx, segments)

    def data_date(self, ctx, data):
        if self.year is None or  self.month is None:
            return None
        return int(self.year), int(self.month)
        
    docFactory = loaders.stan(
        t.html[
            t.head[
                t.title["Calendar Example"],
                cal.calendarCSS
            ],
            t.body[
                t.invisible(data=t.directive('date'), render=cal.cal)
            ]
        ]
    )
