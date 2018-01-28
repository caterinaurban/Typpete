from .chip import Chip
from .pin import Pin

class LED:
    def __init__(self, vcc, gnd, fade_delay_us=10000):
        self.vcc = vcc
        self.gnd = gnd
        self.fade_delay_us = fade_delay_us
        self.fade_counter_us = fade_delay_us + 1

    def tick(self, us):
        self.fade_counter_us += us
        self.ishigh()

    def ishigh(self):
        if self.vcc.ishigh() and not self.gnd.ishigh():
            self.fade_counter_us = 0
            return True
        else:
            return self.fade_counter_us <= self.fade_delay_us


def combine_repr(segs):
    """Combine and returns __str__ repr of multiple Segment7
    """
    outputs = [str(seg) for seg in segs]
    line1 = ' '.join([s[:3] for s in outputs])
    line2 = ' '.join([s[4:7] for s in outputs])
    line3 = ' '.join([s[8:] for s in outputs])
    return '\n'.join([line1, line2, line3])

class Segment7(Chip):
    INPUT_PINS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'DP']

    def __init__(self, *args, **kwargs):
        for code in self.OUTPUT_PINS:
            pin = Pin(code, code in self.STARTING_HIGH, self, True)
            setattr(self, 'pin_{}'.format(pin.code), pin)
        for code in self.INPUT_PINS:
            pin = Pin(code, code in self.STARTING_HIGH, self)
            setattr(self, 'pin_{}'.format(pin.code), pin)
        self.vcc = Pin('VCC', True, self)
        self.update()
        self.leds = {pin.code: LED(self.vcc, pin) for pin in self.getpins(self.INPUT_PINS)}

    def __str__(self):
        SEGMENTS = ["""
 _.
|_|
|_|""".strip('\n')]
        # Remember, each line is **4** chars long if we count the \n!
        SEGPOS = [
            '', 'A', 'DP', '',
            'F', 'G', 'B', '',
            'E', 'D', 'C'
        ]
        s = []
        for c, seg in zip(SEGMENTS, SEGPOS):
            s.append(c if seg and self.leds[seg].ishigh() else ' ')
        return ''.join(s)

    def tick(self, us):
        for led in self.leds.values():
            led.tick(us)
