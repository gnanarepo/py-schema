from pyschema import Schema
from pprint import pprint
from six import print_ as print_out
def name_list():
    return ['a','b','c']
s = Schema({
    'type': 'map',
    'display_name': 'Root Configuration',
    'known_children': {
        'listed_names': {
            'type': 'list',
            'display_name': 'Name List',
            'value_schema': {
                'type':'string',
                'allowed_values':name_list,
                'display_name':'Names'}
            },
        'number_of_names': {
            'display_name': 'Name Count Limit',
            'type': 'number',
            'minimum_value': 2
        },
        'notify_via_mail': {
            'display_name': 'Mail Preference',
            'type': 'boolean'
        }
    },
    'mandatory_children': ['listed_names']
})

print_out("Realized schema\n---------------")
pprint(s.realize())
print_out("\n\n")

print_out("Sample Validation Errors: 1\n---------------")
pprint(s.validate({
    'listed_names': 10
}))
print_out("\n\n")

print_out("Sample Validation Errors: 2\n---------------")
pprint(s.validate({
    'listed_names': [10, 'invalid-name']
}))
print_out("\n\n")

print_out("Sample Validation Errors: 3 (No errors)\n---------------")
pprint(s.validate({
    'listed_names': ['a', 'b']
}))

