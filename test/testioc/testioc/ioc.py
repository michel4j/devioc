from devioc import models


# Create your models here. Modify the example below as appropriate

class Testioc(models.Model):
    number = models.Enum('number', choices=['ZERO', 'ONE', 'TWO'], default=0, desc='Enum Test')
    toggle = models.Toggle('toggle', zname='ON', oname='OFF', high=0, desc='Toggle Test')
    sstring = models.String('sstring', max_length=20, desc='Short String Test')
    lstring = models.String('lstring', max_length=512, desc='Long String Test')
    intval = models.Integer('intval', max_val=1000, min_val=-1000, default=0, desc='Int Test')
    floatval = models.Float('floatval', max_val=1e6, min_val=1e-6, default=0.0, desc='Float Test')
    floatout = models.Float('floatout', desc='Test Float Output')
    intarray = models.Array('intarray', type=int, length=16, desc='Int Array Test')
    floatarray = models.Array('floatarray', type=float, length=16, desc='Float Array Test')
    calc = models.Calc(
        'calc', calc='A+B', inpa='$(device):intval CP NMS', inpb='$(device):floatval CP NMS', desc='Calc Test'
    )


# create your app here. Modify the following example as appropriate

class TestiocApp(object):
    def __init__(self, device_name):
        self.ioc = Testioc(device_name, callbacks=self)

    def do_toggle(self, pv, value, ioc):
        if value == 1:
            # Command activated, value will return to 0 after some time 
            print('Toggle Changed Value', pv, value, ioc)
            ioc.number.put((ioc.number.get() + 1) % 3, wait=True)  # cycle through values

    def do_number(self, pv, value, ioc):
        name = {0: 'Noll', 1: 'Ett', 2: 'Två'}.get(value, 'va?')
        print(f'New Enum Value: {value} {name}')

    def do_calc(self, pv, value, ioc):
        A = ioc.intval.get()
        B = ioc.floatval.get()
        print(f'New Calc Result: {A} + {B} = {value}')

    def shutdown(self):
        # needed for proper IOC shutdown
        self.ioc.shutdown()
