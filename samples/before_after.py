from pyschema import Schema

s = {
    'type': 'string',
    'display_name': 'Drama'
}

print(s)

_s = Schema(s)
_s.validate('Drama')

print(s)
