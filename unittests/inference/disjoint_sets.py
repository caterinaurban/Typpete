class DisjointSets:
    def __init__(self, size):
        self.size = size
        self.p = [i for i in range(size)]
        self.rank = [0] * size
        self.set_size = [1] * size

        for i in range(size):
            self.p[i] = i

    def find_set(self, i):
        if self.p[i] == i:
            return i

        self.p[i] = self.find_set(self.p[i])
        return self.p[i]

    def is_same_set(self, i, j):
        return self.find_set(i) == self.find_set(j)

    def union_sets(self, i, j):
        if self.is_same_set(i, j):
            return
        self.size -= 1
        x = self.find_set(i)
        y = self.find_set(j)
        if self.rank[x] > self.rank[y]:
            self.p[y] = x
            self.set_size[x] += self.set_size[y]
        else:
            self.p[x] = y
            self.set_size[y] += self.set_size[x]
            if self.rank[x] == self.rank[y]:
                self.rank[y] += 1


d = DisjointSets(3)

print(d.is_same_set(0, 1))
d.union_sets(0, 1)
print(d.is_same_set(0, 1))


# DisjointSets := Type[DisjointSets]
# d := DisjointSets
