import itertools
import array
import sys
import PIL.Image


class Layer(object):
    def __init__(self, size, data=None):
        self.size = size
        if data is not None:
            self.a = array.array('f', data)
            assert len(self.a) == size[0] * size[1]
        else:
            self.a = array.array('f', itertools.repeat(0., size[0] * size[1]))

    def __getitem__(self, k):
        # assert 0 <= k[0] < self.size[0]
        # assert 0 <= k[1] < self.size[1]
        return self.a[k[0] + self.size[0] * k[1]]

    def __setitem__(self, k, v):
        # assert 0 <= k[0] < self.size[0]
        # assert 0 <= k[1] < self.size[1]
        self.a[k[0] + self.size[0] * k[1]] = v

    def normalize(self):
        mi = min(self.a); ma = max(self.a)
        delta = float(ma - mi)
        self.a = array.array('f', ((v - mi) / delta for v in self.a))


    def bigger(self, extend):
        '''
        >>> l = Layer((1,1), [1.0])
        >>> list(l.bigger((1,1)).a)
        [0.0, 0.0, 0.0,
         0.0, 1.0, 0.0,
         0.0, 0.0, 0.0]
        >>> l = Layer((2,1), [1.0, 2.0])
        >>> list(l.a)
        [1.0, 2.0]
        >>> list(l.bigger((2,2)).a)
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 1.0, 2.0, 0.0, 0.0,
         0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        >>> list(l.bigger((2,1)).a)
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 1.0, 2.0, 0.0, 0.0,
         0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        >>> l = Layer((2,2), [1.0, 2.0, 3.0, 4.0])
        >>> list(l.bigger((1,1)).a)
        [0.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 2.0, 0.0,
         0.0, 3.0, 4.0, 0.0,
         0.0, 0.0, 0.0, 0.0]
        '''
        (r, c) = extend
        a = array.array('f')
        for _ in xrange(c):
            a.extend(itertools.repeat(0., r+r+self.size[0]))
        for y in xrange(self.size[1]):
            a.extend(itertools.chain(
                    itertools.repeat(0., r),
                    self.a[self.size[0] * y: self.size[0] * (y+1)],
                    itertools.repeat(0., r),
                    ) )
        for _ in xrange(c):
            a.extend(itertools.repeat(0., r+r+self.size[0]))
        # print(len(a),self.size, extend, self.size[0]+2*r, self.size[1]+2*c,
        #       (self.size[0]+2*r)* (self.size[1]+2*c))
        return Layer((self.size[0]+2*r, self.size[1]+2*c), a)

    def to_image(self):
        img = PIL.Image.new('L', self.size)
        img.putdata(array.array('B', (int(v*255.) for v in self.a)))
        return img

    def windows_fun(self, size):
        '''
        >>> l = Layer((1,1), [1.0])
        >>> l[0,0]
        1.0
        >>> l.a[0]
        1.0
        >>> list(l.windows_fun(2)(0).a)
        [0.0, 0.0,
         0.0, 1.0]
        >>> list(l.windows_fun(4)(0).a)
        [0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 1.0, 0.0,
         0.0, 0.0, 0.0, 0.0]
        >>> l = Layer((2,1), [1.0, 2.0])
        >>> list(l.windows_fun(2)(0).a)
        [0.0, 0.0,
         0.0, 1.0]
        >>> list(l.windows_fun(2)(1).a)
        [0.0, 0.0,
         1.0, 2.0]
        >>> l = Layer((1,2), [1.0, 2.0])
        >>> list(l.windows_fun(2)(0).a)
        [0.0, 0.0,
         0.0, 1.0]
        >>> list(l.windows_fun(2)(1).a)
        [0.0, 1.0,
         0.0, 2.0]
        >>> l = Layer((2,2), [1.0, 2.0, 3.0, 4.0])
        >>> list(l.windows_fun(4)(0).a)
        [0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 1.0, 2.0,
         0.0, 0.0, 3.0, 4.0]
        >>> list(l.windows_fun(4)(1).a)
        [0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 2.0, 0.0,
         0.0, 3.0, 4.0, 0.0]
        >>> list(l.windows_fun(4)(2).a)
        [0.0, 0.0, 0.0, 0.0,
         0.0, 0.0, 1.0, 2.0,
         0.0, 0.0, 3.0, 4.0,
         0.0, 0.0, 0.0, 0.0]
        >>> list(l.windows_fun(4)(3).a)
        [0.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 2.0, 0.0,
         0.0, 3.0, 4.0, 0.0,
         0.0, 0.0, 0.0, 0.0]
        '''
        size = (size/2)*2
        big = self.bigger((size/2, size/2))
        old_y = self.size[0]
        new_y = big.size[0]
        def gen(c):
            y = c / old_y
            x = c % old_y
            rows = [big.a[x + new_y*yy : x + size + new_y*yy]
                    for yy in xrange(y, y+size)]
            return Layer((size, size), itertools.chain(*rows))
        return gen


    def delta(self, l):
        n = Layer(self.size)
        for c in xrange(self.size[0] * self.size[1]):
            n.a[c] = abs(l.a[c] - self.a[c])
        return n

def save(layers, filename):
    out = PIL.Image.merge("RGB", (layers[0].to_image(),
                                  layers[1].to_image(),
                                  layers[2].to_image()))
    out.save(filename)



if __name__ == '__main__':
    import doctest_patch
    import doctest
    if doctest.testmod(optionflags=doctest_patch.EVAL_FLAG)[0] == 0:
        print("all tests ok")
