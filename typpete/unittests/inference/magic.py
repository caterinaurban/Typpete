T = 3

for x in [1, 2, 3, T + 1]:

    l1 = 2
    for i in [1, l1]:
        pass
    L1 = [9, 10, 11, 12]
    for i in [l1 + 1, 4]:
        pass

    l2 = 3
    for i in [1, 2, l2]:
        pass
    L2 = [9, 10, 7, 12]
    for i in [l2 + 1]:
        pass

    z = 0
    n = 0
    for i in [0, 1, 2, 3]:
        for j in [0, 1, 2, 3]:
            if L1[i] == L2[j]:
                z = z + 1
                n = L1[i]

    if z == 1:
        res = ""
    else:
        if z == 0:
            res = ""
        else:
            res = ""

# T := int
# x := int
# l1 := int
# L1 := List[int]
# l2 := int
# L2 := List[int]
# i := int
# j := int
# z := int
# n := int
# res := str
