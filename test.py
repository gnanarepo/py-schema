from pyschema import Schema
from pprint import pprint
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

print "Realized schema\n---------------"
pprint(s.realize())
print "\n\n"

print "Sample Validation Errors: 1\n---------------"
pprint(s.validate({
    'listed_names': 10
}))
print "\n\n"

print "Sample Validation Errors: 2\n---------------"
pprint(s.validate({
    'listed_names': [10, 'invalid-name']
}))
print "\n\n"

print "Sample Validation Errors: 3 (No errors)\n---------------"
pprint(s.validate({
    'listed_names': ['a', 'b']
}))

