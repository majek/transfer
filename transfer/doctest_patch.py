
# Internal doctests
#
# To maintain compatibility with both python 2.x and 3.x in tests
# we need to do a trick. Python 2.x doesn't like b'' notation,
# Python 3.x doesn't have 2222L long integers notation. To
# overcome that we'll pipe both results as well as the intended
# doctest output through an `eval` function before comparison. To
# do it we need to monkeypatch the OutputChecker:
import doctest
EVAL_FLAG = doctest.register_optionflag("EVAL")
OrigOutputChecker = doctest.OutputChecker

def relaxed_eval(s):
    if s.strip():
        return eval(s)
    else:
        return None

class MyOutputChecker:
    def __init__(self):
        self.orig = OrigOutputChecker()

    def check_output(self, want, got, optionflags):
        if optionflags & EVAL_FLAG:
            return relaxed_eval(got) == relaxed_eval(want)
        else:
            return self.orig.check_output(want, got, optionflags)

    def output_difference(self, example, got, optionflags):
        return self.orig.output_difference(example, got, optionflags)

doctest.OutputChecker = MyOutputChecker
# Monkey patching done. Go for doctests:

#if doctest.testmod(optionflags=EVAL_FLAG)[0] == 0: print("all tests ok")
