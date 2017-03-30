from pyschema import Schema
from six import print_ as print_out

def even_only(a):
        return ["size must be even"] if len(a) % 2 else [ ]

s = Schema({
    'type': 'string',
    'display_name': 'EvenStevens',
    'custom_validation': even_only
})

print_out("EVEN STEVENS")
print_out("------------")
print_out("Should pass: "+"\n".join(s.validate('String')))
print_out("Should fail: "+"\n".join(s.validate('basestr')))

s = Schema({
    'type': 'list',
    'display_name': 'EvenStevens List',
    'custom_validation': even_only,
    'value_schema': {
        'type': 'string',
        'display_name': 'One of the stevens'
    }
})

print_out("EVEN STEVENS ENLISTED")
print_out("---------------------")
print_out("Should pass: "+"\n".join(s.validate(['String', 'basestr'])))
print_out("Should fail: "+"\n".join(s.validate(('basestr',))))
print_out("Should fail: "+"\n".join(s.validate('basestr')))