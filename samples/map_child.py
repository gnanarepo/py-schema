from pyschema import Schema
from six import print_ as print_out

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

print_out('Must Pass: '+'\n'.join(s.validate({'a': 'Something'})))
print_out('Must FAIL: '+'\n'.join(s.validate({'z':'ERROR'})))

print_out(s.document())

