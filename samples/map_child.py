from pyschema import Schema

s = Schema({
    'display_name': 'Names',
    'known_children': {
        'a': None,
        'b': None,
    },
    'value_schema': {
        'type': 'string',
        'display_name':'A or B'
    },
    'allow_unknown_children': False
})

print 'Must Pass: '+'\n'.join(s.validate({'a': 'Something'}))
print 'Must FAIL: '+'\n'.join(s.validate({'z':'ERROR'}))
