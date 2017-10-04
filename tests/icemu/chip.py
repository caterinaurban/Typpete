from .pin import Pin

class Chip:
    OUTPUT_PINS = []
    INPUT_PINS = []
    STARTING_HIGH = [] # pins that start high
    PIN_ORDER = None

    def __init__(self):
        for code in self.OUTPUT_PINS:
            pin = Pin(code, chip=self, output=True, high=(code in self.STARTING_HIGH))
            setattr(self, 'pin_{}'.format(pin.code), pin)
        for code in self.INPUT_PINS:
            pin = Pin(code, chip=self, high=(code in self.STARTING_HIGH))
            setattr(self, 'pin_{}'.format(pin.code), pin)
        self.vcc = Pin('VCC', chip=self, high=True)
        self.update()

    def __str__(self):
        inputs = ' '.join([str(self.getpin(code)) for code in self.INPUT_PINS])
        outputs = ' '.join([str(self.getpin(code)) for code in self.OUTPUT_PINS])
        return '{} I: {} O: {}'.format("Chip", inputs, outputs)

    def ispowered(self):
        return self.vcc.ishigh()

    def getpin(self, code) -> Pin:
        return getattr(self, 'pin_{}'.format(code.replace('~', '')))

    def getpins(self, codes):
        return [self.getpin(code) for code in codes]

    # Set multiple pins on the same chip and only update chips one all pins are updated.
    def setpins(self, low, high):
        updateself = False
        updatelist = set()
        for codes, val in [(low, False), (high, True)]:
            for pin in self.getpins(codes):
                if pin.high != val:
                    pin.high = val
                    if pin.output:
                        updatelist |= pin.propagate_to()
                    else:
                        updateself = True
        if updateself:
            self.update()
        for chip in updatelist:
            chip.update()

    def tick(self, us):
        pass

    def update(self):
        pass
