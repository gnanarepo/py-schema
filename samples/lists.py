from pyschema import Schema
from pprint import pprint

s = Schema({
    'type': 'list',
    'value_schema': {'type': 'number', 'display_name': 'Num'},
    'display_name': 'The List',
    'unique': True,
    'minimum_size': 2,
    'maximum_size': 5
})

print "VALID: "+"".join(s.validate([5,6]))
print "INVALID Few Entries: "+"".join(s.validate([6]))
print "INVALID Too Many: "+"".join(s.validate([5,6,7,8,9,1,2,3,4]))
print "INVALID Duplicate: "+"".join(s.validate([5,6,5,6]))

s1 = Schema({
    'type': 'list',
    'value_schema': {'type': 'number', 'display_name': 'Num'},
    'display_name': 'The List',
    'unique': True,
    'minimum_size': 2,
    'maximum_size': 5
})
print "VALID Duplicate: "+"".join(s1.validate([5,6,5,6]))
pprint(s1.realize())
