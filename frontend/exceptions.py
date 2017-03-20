class HomogeneousTypesConflict(Exception):

    def __init__(self, type1, type2):
        self.message = "Conflict in list types: {} and {}".format(type1, type2)
        super(HomogeneousTypesConflict, self).__init__(self.message)
