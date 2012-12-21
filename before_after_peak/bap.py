# -*- encoding: utf-8 -*-

import sys,glob,math
import numpy as np
import pylab as pl
import matplotlib as mpl
from scipy.stats import describe
from sklearn.cluster import *
from sklearn.mixture import *

from tplot import ternaryPlot
from violin import violin_plot

class Feature(object):

    def _read(self, fn):
        lines = open(fn).read().split('\n')
        tags = [ t.strip() for t in lines[0].split(';')[1:] ]
        print "read",len(tags),"tags"
        self.tags = set(tags)
        for l in lines[3:]:
            l = l.strip()
            bits = l.split(';')
            tid = bits[0]
            self.time_ranges.add(tid)
            for b_index in range(0,len(bits[1:])):
                tag = tags[b_index]
                bit = bits[b_index]
                try:
                    self.data['%s:%s'%(tag,tid)] = float(bit)
                except ValueError:
                    self.data['%s:%s'%(tag,tid)] = 0.0
        print "read", len(self.time_ranges),"time ranges"
                          
    def __init__(self, name):
        self.name = name
        self.time_ranges = set()
        self.tags = set()
        self.data = {}
        self._read(name)

    def values(self, tag):
        sorted_trids = list(self.time_ranges)
        sorted_trids.sort()
        def _na(tag,trid):
            try:
                v = self.data['%s:%s'%(tag,trid)]
                if v == 'NA':
                    return 0.0
                return v
            except KeyError:
                return 0.0
        return [ _na(tag,trid) for trid in sorted_trids  ]

f = Feature(sys.argv[1])

print "peak detection..."
X = np.zeros(shape=(len(f.tags),3))


L=3 # half slide window size
D=5 # minimum increment to become a buzz
N=2 # noise threshold
S=1 # scaling factor for B/A

row = 0
peak_tags = []
peak_times = []
peak_stats = []
for tag in f.tags:
    ts = [ float(v) for v in f.values(tag) ]
    #print "TS",ts
    mts = [ ts[_-L:_+L+1] for _ in range(0,len(ts))  ]
    #print "MTS",mts
    mts = [ float(np.median(v)) for v in mts ]
    #print "MTS'",mts
    pis = [ (ts[_] - mts[_])/max(mts[_],N) for _ in range(0,len(ts)) ]
    #print "PIS",pis
    peaks = [ _ for _ in range(0,len(ts)) if pis[_] > D ]
    if not len(peaks) >= 1:
        continue
    for i in xrange(len(peaks)-1,0,-1):
        if peaks[i] - peaks[i-1] < 3:
            del peaks[i]
    #if len(peaks)>1:
    #    continue
    peak_values = [ ts[p] for p in peaks ]
    max_peak_value = max(peak_values)
    peak = peaks[peak_values.index(max_peak_value)]
    print "PEAK %s @ %s\t med:%.3f val:%.3f inc:%.3f"%(tag,
                                                       peak,
                                                       mts[peak],
                                                       ts[peak],
                                                       pis[peak]),
    peak_value = ts[peak]
    peak_times.append(peak)
    peak_stats.append((ts[peak],mts[peak]))
    b = sum([ v for v in ts[peak-L*S:peak] ])
    a = sum([ v for v in ts[peak+1:peak+L*S] ])
    p = peak_value
    scale = float(b+a+p)
    b /= scale
    a /= scale
    p /= scale
    print "bpa: %.3f/%.3f/%.3f"%(b,p,a)
    X[row,0] = p
    X[row,1] = b
    X[row,2] = a
    peak_tags.append(tag)
    row +=1
 
#print X
print "removing empty cells..."
X = X[X.all(1)]
#print X

#pl.boxplot(X)

print "clustering..."
centroids, labels = None,None

if sys.argv[2] == 'meanshift':
    centroids, labels = mean_shift(X,max_iterations=3000)
if sys.argv[2] == 'kmeans':
    best_bic = 1e8
    best_labels = None
    for k in range(2,30):
        centroids, labels, inertia = k_means(X,k)
        bic = math.log(inertia)/(X.shape[0]-float(k*k*k))
        print k, inertia, bic
        if bic < best_bic:
            best_bic = bic
            best_labels = labels
    labels = best_labels
newdata,ax = ternaryPlot(X,
                         ('peak',
                          'before',
                          'after'),
                         )
print "plotting..."
markers = 'o*^psxDh+'
markers += markers
markers += markers
markers += markers
markers += markers
_colors='bgrcmyk'
_colors0='bgrcmyk'[::-1]
colors = _colors+_colors0+_colors+_colors0
colors += colors
for i in range(0,len(newdata)):
    l = labels[i]
    pl.plot(newdata[i,0],
            newdata[i,1],
            markers[l],
            color=colors[l])

for label in set(labels):
    for i in range(0,X.shape[0]):
        if labels[i] == label:
            print "[%s] %s \t pba:"%(label,peak_tags[i]),
            print "%.3f %.3f %.3f"%(X[i,0],X[i,1],X[i,2]),
            print "tid:%s v/med:%s"%(peak_times[i],
                                     peak_stats[i])

pl.show()
