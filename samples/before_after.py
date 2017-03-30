from pyschema import Schema
from six import print_ as print_out

s = {
    'type': 'string',
    'display_name': 'Drama'
}

print_out(s)

_s = Schema(s)
_s.validate('Drama')

print_out(s)
