class HomogeneousTypesConflict(Exception):

    def __init__(self, type1, type2):
        self.message = "Conflict in list types: {} and {}".format(type(type1).__name__, type(type2).__name__)
        super(HomogeneousTypesConflict, self).__init__(self.message)
