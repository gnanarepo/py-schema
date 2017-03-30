from pyschema import Schema
from six import print_ as print_out

s = Schema({
    'type': 'string',
    'display_name': 'Allow None Test',
    'allow_none': True
})

print_out("NULL ALLOWED")
print_out("------------")
print_out("Should pass: "+"\n".join(s.validate(None)))
print_out("Should pass: "+"\n".join(s.validate('String')))
print_out("Should fail: "+"\n".join(s.validate(10)))


print_out("NULL NOT ALLOWED")
print_out("----------------")
from pyschema import Schema

s = Schema({
    'type': 'string',
    'display_name': 'Allow None Test',
})

print_out("Should fail: "+"\n".join(s.validate(None)))
print_out("Should pass: "+"\n".join(s.validate('String')))
print_out("Should fail: "+"\n".join(s.validate(10)))