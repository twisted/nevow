# from moe, adapted to use the methodology outlined here:
#  http://oubiwann.blogspot.com/2006/08/python-and-kcachegrind.html
#
import csv
import cProfile
import lsprofcalltree
 
from nevow import loaders, tags, inevow
 
docFactory = loaders.stan(tags.invisible[tags.invisible(pattern='hi')])
iq = inevow.IQ(docFactory)
 
def onePatternRepeated(times):
    for i in xrange(times):
        iq.onePattern('hi')

p = cProfile.Profile()
p.run('onePatternRepeated(100000)')

rows = [("Code Filename", "Code Name", "Code Names", "Variable Names",
    "Constants", "Call Count", "Recall Count", "Total Time",
    "Inline Time"),]

for stat in p.getstats():
    row = []
    code, callcount, recallcount, totaltime, inlinetime, calls = stat
    try:
        row.extend([code.co_filename, code.co_name, str(code.co_names),
            str(code.co_varnames), str(code.co_consts)])

    except AttributeError:
        row.extend([str(code), '', '', '', ''])
    row.extend([callcount, recallcount, totaltime, inlinetime])
    rows.append(row)
    #calls = calls or []
    #for call in calls:
        #print "\t%s" % str(call)
        #print "\t%s" % str(dir(call))

# csv data for viewing in NeoOffice
writer = csv.writer(open("profile_one_pattern.csv", "w+"))
writer.writerows(rows)

# for kcachegrind
k = lsprofcalltree.KCacheGrind(p)
data = open('profile_one_pattern.kgrind', 'w+')
k.output(data)
data.close()
