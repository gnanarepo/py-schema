from pyschema import Schema
from pprint import pprint
from six import print_ as print_out

s = Schema({
    'type': 'list',
    'value_schema': {'type': 'number', 'display_name': 'Num'},
    'display_name': 'The List',
    'unique': True,
    'minimum_size': 2,
    'maximum_size': 5
})

print_out("VALID: "+"".join(s.validate([5,6])))
print_out("INVALID Few Entries: "+"".join(s.validate([6])))
print_out("INVALID Too Many: "+"".join(s.validate([5,6,7,8,9,1,2,3,4])))
print_out("INVALID Duplicate: "+"".join(s.validate([5,6,5,6])))

s1 = Schema({
    'type': 'list',
    'value_schema': {'type': 'number', 'display_name': 'Num'},
    'display_name': 'The List',
    'unique': False,
    'minimum_size': 2,
    'maximum_size': 5
})
print_out("VALID Duplicate: "+"".join(s1.validate([5,6,5,6])))
pprint(s1.realize())
