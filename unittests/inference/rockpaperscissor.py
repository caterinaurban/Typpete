from abc import ABCMeta, abstractmethod

class Outcome:
    def __init__(self, value, name):
        self.value = value
        self.name = name


class Item(metaclass=ABCMeta):
    @abstractmethod
    def compete(self, item):
        pass

    @abstractmethod
    def evalPaper(self, item):
        pass

    @abstractmethod
    def evalScissors(self, item):
        pass

    @abstractmethod
    def evalRock(self, item):
        pass


class Paper(Item):
    def compete(self, item):
        return item.evalPaper(self)

    def evalPaper(self, item):
        return Outcome(2, "draw")

    def evalScissors(self, item):
        return Outcome(0, "win")

    def evalRock(self, item):
        return Outcome(1, "lose")


class Scissors(Item):
    def compete(self, item):
        return item.evalScissors(self)

    def evalPaper(self, item):
        return Outcome(1, "lose")

    def evalScissors(self, item):
        return Outcome(2, "draw")

    def evalRock(self, item):
        return Outcome(0, "win")


class Rock(Item):
    def compete(self, item):
        return item.evalRock(self)

    def evalPaper(self, item):
        return Outcome(0, "win")

    def evalScissors(self, item):
        return Outcome(1, "lose")

    def evalRock(self, item):
        return Outcome(2, "draw")


def match(item1, item2):
    return item1.compete(item2)


match(Rock(), Scissors())
match(Paper(), Rock())
match(Scissors(), Paper())

# Outcome := Type[Outcome]
# Item := Type[Item]
# match := Callable[[Item, Item], Outcome]
