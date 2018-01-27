# type_params {'generic_tolist': ['GTL'], 'flatten': ['FL'], 'flatten_dict': ['DK','DV']}


def generic_tolist(a):
    return [a]

u = generic_tolist(1.2)
u[0] = 2.4
v = generic_tolist(True)
v2 = v[v[0]]


def flatten(lists):
    """
    Flattens a list of lists into a flat list
    """
    return [item for sublist in lists for item in sublist]


def flatten_dict(dicts,
                 defaults):
    """
    Flattens a dict of lists, i.e., concatenates all lists for the same keys.
    """
    result = {}
    for key in defaults:
        result[key] = []
    for d in dicts:
        for key, value in d.items():
            if key in result:
                result[key].extend(value)
            else:
                result[key] = value
    return result

a = flatten([[1,2], [1,2], [True, False]])
a2 = flatten([["hi"], ['yo', 'sup']])
a4 = a[a[0]]

b = [{1:[2]}, {True: [True]}, {5: [1.2, 2]}]
c = b[0][1]

d = flatten_dict(b, [True, 1])
e = flatten_dict([{1.2: ['hi']}], [3, 5])

class A:
    def bar(self):
        return 1

class B(A):
    pass

ff = flatten_dict([{'hi': [A()]}, {'sup': [A()], 'hey': [B(), A()]}], ['asd', 'erer'])
ff['hi'][0].bar()


# flatten := Callable[[List[List[FL]]], List[FL]]
# flatten_dict := Callable[[List[Dict[DV, List[DK]]], List[DV]], Dict[DV, List[DK]]]
# generic_tolist := Callable[[GTL], List[GTL]]