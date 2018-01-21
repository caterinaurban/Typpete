# first pin is the least significant bit
def set_binary_value(value, pins):
    for i, pin in enumerate(pins):
        pin.set(bool((value >> i) & 0x1))

def get_binary_value(pins):
    value = 0
    for index, pin in enumerate(pins):
        if pin.ishigh():
            value |= 1 << index
    return value