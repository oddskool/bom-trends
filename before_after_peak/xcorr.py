import sys,glob

class Feature(object):

    def _read(self, fn, source):
        lines = open(fn).read().split('\n')
        for l in lines:
            l = l.strip()
            #print "<%s>"%l
            k,v=(None,0)
            try:
                k,v = l.split('\t')
            except ValueError:
                k = l
            try:
                tag,trid = k.split(':')
                v = float(v)
                self.time_ranges.add(trid)
                self.tags.add(tag)
                #print source,tag,trid,'=>',v
                self.data['%s:%s:%s'%(source,tag,trid)] = v
            except ValueError:
                pass
    
    def __init__(self, name):
        self.name = name
        self.time_ranges = set()
        self.tags = set()
        self.data = {}
        for fn in glob.glob('features/raw_features/BOM/%s/part*'%self.name):
            #print "reading", fn
            self._read(fn,'bom')
        for fn in glob.glob('features/raw_features/TWITTER/%s/part*'%self.name):
            #print "reading", fn
            self._read(fn,'twt')

    def values(self, source, tag):
        sorted_trids = list(self.time_ranges)
        sorted_trids.sort()
        def _na(source,tag,trid):
            try:
                return self.data['%s:%s:%s'%(source,tag,trid)]
            except KeyError:
                return 0.0
        return [ _na(source,tag,trid) for trid in sorted_trids  ]


dq = Feature(sys.argv[1])

from scipy.stats.stats import pearsonr
from numpy import isnan

def xcor(tag):
    x,y = (dq.values('bom',tag),
           dq.values('twt',tag))
    ml = max(len(x),len(y))
    x = x[0:ml]
    y = y[0:ml]
    if not sum(x) or not sum(y):
        return None
    r = pearsonr(x,y)
    #if not isnan(r[0]):
    #    print tag, r
    return r

pvalue = 0.05

cors = [ xcor(tag) for tag in dq.tags ]
cors = [ c for c in cors if c is not None ]
cors = [ c[0] for c in cors if not isnan(c[0]) and c[1] < pvalue ] 

print "retained %d points"%len(cors)
if not len(cors):
    sys.exit(-1)

tag_cors = [ (xcor(tag), tag) for tag in dq.tags ]
tag_cors = [ t for t in tag_cors if t[0] and not isnan(t[0][0]) and t[0][1] < pvalue ] 
tag_cors.sort()

fn = 'cor_top-flop_%s.txt'%dq.name
fd = open(fn,'w')
print >>fd, ">>> top_corrs:"
for t,r in tag_cors[-30:-1]:
    print >>fd, t, r
print >>fd, ">>> flop_corrs:"
for t,r in tag_cors[1:30]:
    print >>fd, t, r

import numpy as n
from pylab import *
import matplotlib.cm as cm
import matplotlib.colors as colors

fig = figure()
suptitle("Distribution of Correlations between BOM/TWT Feature '%s' \n with p-value < %f "%(dq.name,pvalue))
ax = fig.add_subplot(111)
Ntotal = 1000
N, bins, patches = ax.hist(cors,30)

fracs = N.astype(float)/N.max()
norm = colors.normalize(fracs.min(), fracs.max())

for thisfrac, thispatch in zip(fracs, patches):
    color = cm.jet(norm(thisfrac))
    thispatch.set_facecolor(color)


#show()
savefig('cor_hist_%s.png'%dq.name)

