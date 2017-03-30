from pyschema import Schema
import functools
from pprint import pprint
from six import print_ as print_out
from six import iteritems

name_map = {
    'names': 'names.txt',
    'places': 'places.txt'
}

def list_from_file(filename):
    with file(filename) as fp:
        return [x.strip() for x in fp]

def name_list():
    ret_value = {}
    for k, v in iteritems(name_map):
        ret_value[k] = {
            'display_name': k,
            'type': 'list',
            'value_schema': {
                'display_name': 'Pick a '+k,
                'type': 'string',
                'allowed_values': functools.partial(list_from_file, v)
            }
        }
    return ret_value

schema = Schema({
    'type': 'map',
    'display_name': 'Complex Test',
    'known_children': name_list
})

pprint(schema.realize())
print_out("\n\n")

print_out("Expecting a type error\n---------------")
pprint(schema.validate({'names':[], 'places':'Lakkavaram'}))
print_out("\n\n")

print_out("No Errors\n----------------")
pprint(schema.validate({'names':['john'], 'places':['Lakkavaram']}))
print_out("\n\n")
