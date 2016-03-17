from pyschema import Schema

s = Schema({
    'type': 'string',
    'display_name': 'Allow None Test',
    'allow_none': True
})

print "NULL ALLOWED"
print "------------"
print "Should pass: "+"\n".join(s.validate(None))
print "Should pass: "+"\n".join(s.validate('String'))
print "Should fail: "+"\n".join(s.validate(10))


print "NULL NOT ALLOWED"
print "----------------"
from pyschema import Schema

s = Schema({
    'type': 'string',
    'display_name': 'Allow None Test',
})

print "Should fail: "+"\n".join(s.validate(None))
print "Should pass: "+"\n".join(s.validate('String'))
print "Should fail: "+"\n".join(s.validate(10))