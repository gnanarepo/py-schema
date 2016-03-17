from pyschema import Schema

def even_only(a):
        return ["size must be even"] if len(a) % 2 else [ ]

s = Schema({
    'type': 'string',
    'display_name': 'EvenStevens',
    'custom_validation': even_only
})

print "EVEN STEVENS"
print "------------"
print "Should pass: "+"\n".join(s.validate('String'))
print "Should fail: "+"\n".join(s.validate('basestr'))

s = Schema({
    'type': 'list',
    'display_name': 'EvenStevens List',
    'custom_validation': even_only,
    'value_schema': {
        'type': 'string',
        'display_name': 'One of the stevens'
    }
})

print "EVEN STEVENS ENLISTED"
print "---------------------"
print "Should pass: "+"\n".join(s.validate(['String', 'basestr']))
print "Should fail: "+"\n".join(s.validate(('basestr',)))
print "Should fail: "+"\n".join(s.validate('basestr'))