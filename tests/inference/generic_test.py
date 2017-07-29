



def generic_tolist(a):
    b = a + 1
    return [a]

u = generic_tolist(1.2)
u[0] = 2.4
v = generic_tolist(True)
v2 = v[v[0]]
# v3 = v[0] + 2


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
            a = [1]
            b = a[key]
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
# e = flatten_dict([{1.2: ['hi']}], [3, 5])


# a := List[int]
# b := List[Dict[int, List[float]]]
# c := List[float]
# d := Dict[int, List[float]]
# flatten := Callable[[List[List[int]]], List[int]]
# flatten_dict := Callable[[List[Dict[int, List[float]]], List[int]], Dict[int, List[float]]]