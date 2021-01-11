import unittest
import numpy

from .. import models, log

MAX_INTEGER = 12345
MIN_INTEGER = -54321
DEFAULT_INTEGER = 1111
DEFAULT_FLOAT = 0.1234
ARRAY_SIZE = 16
DEVICE_NAME = 'TEST001'


class TestIOC(models.Model):
    enum = models.Enum('enum', choices=['ZERO', 'ONE', 'TWO'], default=0, desc='Enum Test')
    toggle = models.Toggle('toggle', zname='ON', oname='OFF', desc='Toggle Test')
    sstring = models.String('sstring', max_length=20, desc='Short String Test')
    lstring = models.String('lstring', max_length=512, desc='Long String Test')
    intval = models.Integer(
        'intval', max_val=MAX_INTEGER, min_val=MIN_INTEGER, default=0, desc='Int Test'
    )
    floatval = models.Float(
        'floatval', max_val=MAX_INTEGER, min_val=MIN_INTEGER, default=0.0, desc='Float Test'
    )
    floatout = models.Float('floatout', desc='Test Float Output')
    intarray = models.Array('intarray', type=int, length=ARRAY_SIZE, desc='Int Array Test')
    floatarray = models.Array('floatarray', type=float, length=ARRAY_SIZE, desc='Float Array Test')
    strarray = models.Array('strarray', type=str, length=ARRAY_SIZE, desc='String Array Test')
    calc = models.Calc('calc', calc='A+B', inpa='$(device):intval CP NMS', inpb='$(device):floatval CP NMS', desc='Calc Test')
    calcout = models.CalcOut(
        'calcout', calc='A+B', inpa='$(device):intval CP NMS', inpb='$(device):floatval CP NMS', out='$(device):floatout NP',
        desc='CalcOut Test'
    )


class IOCManager(object):

    def __init__(self):
        log.log_to_console()
        self.ioc = TestIOC(DEVICE_NAME, callbacks=self)


class IOCTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manager = IOCManager()
        cls.ioc = cls.manager.ioc

    @classmethod
    def tearDownClass(cls):
        cls.ioc.shutdown()

    def test_enum(self):
        val = 1
        pv = self.ioc.enum
        pv.put(val, wait=True)
        self.assertEqual(val, pv.get(), 'Put Failed: Values do not match: {} vs {}'.format(val, pv.get()))

    def test_sstring(self):
        val = 'devioc is cool'
        pv = self.ioc.sstring
        pv.put(val, wait=True)
        self.assertEqual(val, pv.get(), 'Put Failed: Values do not match: {} vs {}'.format(val, pv.get()))

    def test_lstring(self):
        val = 'devioc is cool, this is a very long string which should not fit in the small space of a regular string'
        pv = self.ioc.lstring
        pv.put(val, wait=True)
        print(val, pv.get())
        self.assertEqual(val, pv.get(), 'Put Failed: Values do not match: {} vs {}'.format(val, pv.get()))

    def test_integer(self):
        pv = self.ioc.intval
        pv.put(DEFAULT_INTEGER, wait=True)
        self.assertEqual(DEFAULT_INTEGER, pv.get(), 'Put Failed: Values do not match: {} vs {}'.format(DEFAULT_INTEGER, pv.get()))

    def test_float(self):
        pv = self.ioc.floatval
        pv.put(DEFAULT_FLOAT, wait=True)
        self.assertEqual(DEFAULT_FLOAT, pv.get(), 'Put Failed: Values do not match: {} vs {}'.format(DEFAULT_FLOAT, pv.get()))

    def test_int_array(self):
        pv = self.ioc.intarray
        val = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        pv.put(val, wait=True)
        out = pv.get()
        self.assertEqual(val, list(out), 'Put Failed: Values do not match')

    def test_float_array(self):
        pv = self.ioc.floatarray
        val = numpy.array([.0, .1, .2, .3, .4, .5, .6, .7, .8, .9, .10, .11, .12, .13, .14, .15])
        pv.put(val, wait=True)
        out = pv.get()
        self.assertAlmostEqual(val.mean(), out.mean(), 6, 'Put Failed: Values do not match')

    def test_calc(self):
        A = self.ioc.intval
        B = self.ioc.floatval
        calc = self.ioc.calc

        A.put(DEFAULT_INTEGER, wait=True)
        B.put(DEFAULT_FLOAT, wait=True)
        out2 = calc.get()
        expected = DEFAULT_FLOAT + DEFAULT_INTEGER
        self.assertAlmostEqual(out2, expected, 6, 'Calculated Vaues do not match: {} vs {}'.format(out2, expected))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(IOCTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)