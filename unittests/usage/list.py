x = int(input())
y = int(input())
# RESULT: list1 -> (O@0:4), sum -> O, x -> U, y -> N
list1 = [1, x, 2, 3, 5, 8, y]
sum = 0
# some random accesses to list
sum += list1[2]
sum += list1[1]
sum += list1[4]
sum += list1[3]
sum += list1[0]
print(sum)
