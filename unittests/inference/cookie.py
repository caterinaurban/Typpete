T = 4

for x in [1, 2, 3, 4, T + 1]:

    C, F, X = 30.0, 1.0, 2.0

    c = 0.0
    cs = 2.0
    y = 0.0
    while c < X:
        b = C / cs  # buy
        w = X / cs  # wait
        if w < (b + X / (cs + F)):
            y = y + w
            c = X
        else:
            y = y + b
            cs = cs + F

# T := int
# C := float
# F := float
# X := float
# b := float
# c := float
# cs := float
# w := float
# x := int
# y := float
