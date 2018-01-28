"""Number of solutions of linear equality"""


def count_solutions(a, b):
    dp = [0] * (b + 1)
    dp[0] = 1

    for i in range(len(a)):
        for j in range(a[i]):
            dp[j] += dp[j - a[i]]
    return dp[b]

a = count_solutions([1, 2, 3], 2)

# a := int
# count_solutions := Callable[[List[int], int], int]
