from pyschema import Schema

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

print "Invalid B " + "\n".join(s.validate({'a': 10, 'b': 10}))
print "Valid" + "\n".join(s.validate({'a': 10, 'b': 'string'}))
print "Valid Any " + "\n".join(s.validate({'a': 10, 'z': 10}))
print "Valid Any " + "\n".join(s.validate({'x': 10, 'z': 10}))