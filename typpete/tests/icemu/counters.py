from .chip import ActivableChip
from .util import set_binary_value
from .pin import Pin

class BinaryCounter(ActivableChip):
    CLOCK_PIN = ''

    def __init__(self, *args, **kwargs):
        self.value = 0
        self.prev_clock_high = False
        for code in self.OUTPUT_PINS:
            pin = Pin(code, code in self.STARTING_HIGH, self, True)
            setattr(self, 'pin_{}'.format(pin.code), pin)
        for code in self.INPUT_PINS:
            pin = Pin(code, code in self.STARTING_HIGH, self)
            setattr(self, 'pin_{}'.format(pin.code), pin)
        self.vcc = Pin('VCC', True, self)
        self.update()

    def maxvalue(self):
        return (1 << len(self.OUTPUT_PINS)) - 1

    def update(self):
        if not self.is_enabled():
            return

        clock = self.getpin(self.CLOCK_PIN)
        if clock.ishigh() and not self.prev_clock_high:
            self.value += 1
            if self.value > self.maxvalue():
                self.value = 0

            set_binary_value(self.value, self.getpins(self.OUTPUT_PINS))

        self.prev_clock_high = clock.ishigh()


class SN74F161AN(BinaryCounter):
    CLOCK_PIN = 'CLK'
    ENABLE_PINS = ['ENT', 'ENP']
    STARTING_HIGH = ENABLE_PINS
    INPUT_PINS = [CLOCK_PIN] + ENABLE_PINS
    OUTPUT_PINS = ['QA', 'QB', 'QC', 'QD']