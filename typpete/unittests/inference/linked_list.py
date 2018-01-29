class Node:
    def __init__(self, data):
        self.data = data
        self.next_node = self

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data

    def get_next_node(self):
        return self.next_node

    def set_next_node(self, node):
        self.next_node = node


class LList:
    def __init__(self):
        self.first_node = Node(-1)
        self.last_node = Node(-1)

    def is_empty(self):
        return self.first_node.data == -1

    def insert_at_begin(self, value):
        new_node = Node(value)
        if self.is_empty():
            self.first_node = self.last_node = new_node
        else:
            new_node.set_next_node(self.first_node)
            self.first_node = new_node

n = Node(1)
l = LList()

for i in range(5):
    if l.is_empty():
        l.insert_at_begin(i)
    else:
        l.insert_at_begin(l.first_node.get_data() + i)

# Node := Type[Node]
# get_data := Callable[[Node], int]
# set_data := Callable[[Node, int], None]
# get_next_node := Callable[[Node], Node]
# set_next_node := Callable[[Node, Node], None]

# LList := Type[LList]
# is_empty := Callable[[LList], bool]
# insert_at_begin := Callable[[LList, int], None]
# n := Node
# l := LList
