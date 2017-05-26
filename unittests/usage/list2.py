b = bool(input())
x = int(input())
y = int(input())
# RESULT: b -> U, list1 -> (O@0:4), list2 -> (O@0:2), sum -> O, x -> U, y -> N
list1 = [1, x, 2, 3, 5, 8, y]
sum = 0
if b:
    # some random accesses to list
    list2 = list1
    sum += list2[2]
    sum += list2[1]
else:
    # some different random accesses to list
    sum += list1[4]
    sum += list1[3]
    sum += list1[0]
print(sum)
