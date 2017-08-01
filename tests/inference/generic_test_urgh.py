


def generic_tolist(aaa):
    bbb = aaa + 1
    return [aaa]

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
            # a = [1]
            # b = a[key]
            if key in result:
                result[key].extend(value)
            else:
                result[key] = value
    return result

a = flatten([[1,2], [1,2], [True, False]])
a2 = flatten([[1,2], [1,2], [True, False]])
a3 = flatten([[1,2], [1,2], [True, False]])
a4 = flatten([[1,2], [1,2], [True, False]])
a5 = flatten([["hi"], ['yo', 'sup']])
a6 = a[a[0]]

b = [{1:[2]}, {True: [True]}, {5: [1.2, 2]}]
c = b[0][1]
arggg = [True, 1]
gg = flatten_dict(b, arggg)