import math
import PIL.Image

from . import layer


def _grow((rows, cols), d, r, c):
    d[r, c] = (0,0,0)
    opts = []
    if r+1 < rows:
        opts.append( (r+1, c) )
    if c+1 < cols:
        opts.append( (r, c+1) )
    rets = [(r,c)]
    for (a,b) in opts:
        if d[a,b] in MARKER_COLORS:
            rets += _grow((rows, cols), d, a, b)
    return rets


def average(*a):
    return sum(a) / float(len(a))

MARKER_COLORS = ((127, 127, 127), (108, 108, 108, 255))

class Result(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.size = ((p2[0] - p1[0]) or 1,
                     (p2[1] - p1[1]) or 1)
        self.centre = (average(p1[0], p2[0]),
                       average(p1[1], p2[1]))
        self.aspect = self.size[0] / float(self.size[1])

    def point_relative(self, l, (off_x, off_y)):
        a = int(self.centre[0] + off_x)
        b = int(self.centre[1] + off_y)
        return (min(max(0, a), l.size[0]-1),
                min(max(0, b), l.size[1]-1))

def load_results(fullname, desired_size):
    results = []
    om = PIL.Image.open(fullname)
    assert om.size == desired_size
    assert om.mode in ('RGB', 'RGBA')

    d = om.load()
    for r in xrange(om.size[0]):
        for c in xrange(om.size[1]):
            if d[r, c] in MARKER_COLORS:
                rets = _grow(om.size, d, r, c)
                rows, cols = zip(*rets)
                # clear all the pixels within detected rectangle
                for aa in xrange(min(rows), max(rows)):
                    for bb in xrange(min(cols), max(cols)):
                        d[aa, bb]  = (0,0,0)
                results.append(Result((min(rows), min(cols)),
                                      (max(rows), max(cols))))
    return results


def _draw_rectangle_contour(l, r):
    for x in xrange(r.p1[0], r.p2[0]):
        l[x, r.p1[1]] = 1.
        l[x, r.p2[1]] = 1.
    for y in xrange(r.p1[1], r.p2[1]+1):
        l[r.p1[0], y] = 1.
        l[r.p2[0], y] = 1.

def _draw_rectangle_filled(l, r, multiplier):
    szx = ((r.p2[0] - r.p1[0]) / 2.) * multiplier
    szy = ((r.p2[1] - r.p1[1]) / 2.) * multiplier
    p1 = r.point_relative(l, (-szx, -szy))
    p2 = r.point_relative(l, (+szx, +szy))
    for x in xrange(p1[0], p2[0]+1):
        for y in xrange(p1[1], p2[1]+1):
            l[x, y] = 1.0


def results_to_rectangle_layer(size, results):
    l = layer.Layer(size)
    for r in results:
        _draw_rectangle_contour(l, r)
    return l

def _draw_oval(l, r, multiplier):
    return _draw_thing_generic(l, r, multiplier,
                               lambda d: 1. if d < 1. else 0.)

def _draw_oval_shaded(l, r, multiplier):
    return _draw_thing_generic(l, r, multiplier,
                               lambda d: (1. - d) if d < 1. else 0.)

def _draw_thing_generic(l, r, multiplier, intensity_fun):
    dist = lambda a, b: math.sqrt(((a - r.centre[0]) / r.aspect)**2 +
                                  ((b - r.centre[1]))**2)

    # distance to furthest border of rectangle
    dist_proportion = dist(r.centre[0]+r.size[0]/2., r.centre[1]+r.size[1]/2.) * multiplier

    # 0.75 is chosen to make ovals roughly comparible in size to
    # rectangles. It is fully subjective, and in fact the area of the
    # oval is about 0.75 the area of rectangle.
    dist_proportion = dist_proportion * 0.75

    szx = r.size[0] * multiplier * 0.5 + 1.
    szy = r.size[1] * multiplier * 0.5 + 1.

    p1 = r.point_relative(l, (-szx, -szy))
    p2 = r.point_relative(l, (+szx, +szy))
    for a in xrange(p1[0], p2[0]+1):
        for b in xrange(p1[1], p2[1]+1):
            d = dist(a, b) / dist_proportion
            l[a, b] = max(l[a, b], min(1.0, intensity_fun(d)))
    # Make sure at least one pixel is set to 1.
    l[int(r.centre[0]), int(r.centre[1])] = 1.


def results_to_layer(size, results, multiplier=1.0, type=None):
    l = layer.Layer(size)
    fun = {'ovalshade': _draw_oval_shaded,
           'oval': _draw_oval,
           'rect': _draw_rectangle_filled}[type]
    for r in results:
        fun(l, r, multiplier)

    return l
