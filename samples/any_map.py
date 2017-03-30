from pyschema import Schema
from six import print_ as print_out
s = Schema({
    'known_children': {
        'a': {
            'type': 'number',
            'display_name': 'A NUM'
        },
        'b': {
            'type': 'string',
            'display_name': 'B STRING'
        }
    },
    'display_name': 'ANY MAP',
    'value_schema': {
        'type': 'any',
        'display_name': 'ANY VALUE'
    },
    'allow_unknown_children': True
})

print_out("Invalid B " + "\n".join(s.validate({'a': 10, 'b': 10})))
print_out("Valid" + "\n".join(s.validate({'a': 10, 'b': 'string'})))
print_out("Valid Any " + "\n".join(s.validate({'a': 10, 'z': 10})))
print_out("Valid Any " + "\n".join(s.validate({'x': 10, 'z': 10})))