# -*- coding: utf-8 -*-
"""
This module allows validation of dictionaries or lists that contain unstructured data.
While using python objects is the right approach to have structured data, many apps
nevertheless use dictionaries or lists of various data and are stuck with it, specifically
for saving configuration etc.
"""
import re
import os
import jinja2

# Import all the types from six to support both PY2 and PY3
from six import integer_types
from six import string_types
from six import text_type
from six import binary_type
from six import iteritems

# TODO: Move all the strings to one place
type_mismatch = 'Expecting value to be {type} but got {actual_type} for {level}'
invalid_boolean = 'Invalid Value for boolean field'

default_template_dir = os.path.join(os.path.dirname(__file__), "doc_templates")

def get_bool(val):
    """
    Convert various True/False values to true boolean values

    :param val: Boolean like value
    :return:
    """
    if val in (0, 'false', 'False', False):
        return False
    elif val in (1, 'true', 'True', True):
        return True
    else:
        raise ValueError(invalid_boolean)


class Schema(object):
    """ Basic class through which data validation can be done.
    Create a schema object by providing schema dictionary as argument.  Once the schema
    is created call realize() to get the normalized schema, and validate to the validate
    a document against the schema.
    >>> s = Schema({'type':'string', 'display_name':'Root'})
    >>> s.validate('xyz')
    []
    >>> s.validate(10)
    ["Expecting value to be (<type 'str'>, <type 'unicode'>) but got <type 'int'> for root(Root)"]
    >>> s.realize()
    {'type': 'string', 'allow_none': False, 'display_name': 'Root', 'description': ''}
    """
    def __init__(self, schema_dict):
        self.root = SchemaNode.create_schema_node('root', schema_dict)

    def validate(self, data):
        return self.root.validate(data)

    def realize(self):
        realized_schema = {}
        self.root.realize_schema(realized_schema)
        return realized_schema
    
    def document(self, template_directory=None):
        self.realize()
        
        if template_directory:
            search_path = [template_directory, default_template_dir]
        else:
            search_path = [default_template_dir]
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(search_path), 
            autoescape=True
        )
        jinja_env.filters['strip_disp_name'] = lambda x: x.split('(')[0]
        
        template =  jinja_env.get_template("overall2.html")
        return template.render(root = self.root)
    
class SchemaNode(object):
    allowed_expansions = {
        ('known_children', dict),
        ('sub_schema', dict),
        ('minimum_value', int),
        ('maximum_value', float),
        ('allowed_values', (list, set, tuple))
    }
    expected_types = None
    type = None

    def __init__(self, level, schema_dict):
        self.level = level
        self._level = level
        try:
            self.display_name = schema_dict.pop('display_name')
            self.description = schema_dict.pop('description', None)
        except:
            raise SchemaError('display_name is mandatory at level %s' % self.level)
        self.level += '(%s)' % self.display_name
        self.realized = False
        self.verbatim = schema_dict.pop('verbatim', None)
        self.allow_none = schema_dict.pop('allow_none', False)
        self.custom_validation = schema_dict.pop('custom_validation', None)

    def process_children(self):
        raise SchemaError('CODE ERROR: Each child node must implement this method')

    def _execute_if_necessary(self, code_like, expected_type):
        if isinstance(code_like, (expected_type, SchemaNode)):
            ret_value = code_like
            executed = False
        else:
            executed = True
            if callable(code_like):
                ret_value = code_like()
            elif isinstance(code_like, str):
                try:
                    ret_value = eval(code_like)
                except:
                    raise SchemaError("Guessed the value of (%s) at %s to be code, but evaluation failed" % (code_like, self.level))
            else:
                raise SchemaError("Don't known how to execute dynamic schema at %s (expected type = %s, actual type =%s)" % (self.level,expected_type, type(code_like)))

            if not isinstance(ret_value, expected_type):
                schema_type_mismatch = "Dynamic schema generated %s doesn't match the expected type %s at %s"
                raise SchemaError( schema_type_mismatch % (type(ret_value), expected_type, self.level))

        return ret_value, executed

    def _realize_node(self):
        for key_name, expected_type in self.allowed_expansions:
            obj = getattr(self, key_name, None)
            if obj:
                try:
                    obj, executed = self._execute_if_necessary(obj, expected_type)
                    if executed:
                        setattr(self, key_name, obj)
                except SchemaError:
                    raise
                #except Exception as ex:
                    #raise ex
                    # raise SchemaError("Error (%s) when realizing dynamic schema for %s at %s" % (str(ex), key_name, self.level))

        self.realized = True

    def realize_schema(self, attrs):
        if not self.realized:
            self._realize_node()

        attrs['display_name'] = self.display_name
        if self.description is not None:
            attrs['description'] = self.description
        attrs['type'] = self.type
        attrs['allow_none'] = self.allow_none
        if self.verbatim is not None:
            attrs['verbatim'] = self.verbatim
        if self.custom_validation:
            attrs['custom_validation'] = {}
            attrs['custom_validation']['enabled'] = True
            attrs['custom_validation']['info'] = self.custom_validation.__doc__

    def validate(self, data):
        """
        Validate the data and return the violations found

        :param data:
        :return: List of violations.  Each violation is basically a string, and it is unstructured.
        """
        # Realize if necessary
        if not self.realized:
            self._realize_node()

        if data is None:
            if self.allow_none:
                return [ ]
            else:
                return [
                    "Null is not allowed at level %s" % self.level
                ]

        # Perform common validation
        if not isinstance(data, self.expected_types):
            return [
                type_mismatch.format(type=str(self.expected_types),
                                     actual_type = str(type(data)),
                                     level=self.level)
            ]

        # Perform node specific validation
        schema_errors =  self.validate_data(data)
        if self.custom_validation:
            schema_errors.extend("%s: %s at %s" % (self.custom_validation.__name__, x, self.level) for x in self.custom_validation(data))

        return schema_errors
    
    def get_target(self):
        return self.level.split('(')[0].replace('.','_')
    
    def validate_data(self, data):
        raise SchemaError('CODE ERROR: Each child node must implement this method')
    
    # methods related to documentation
    def get_short_decoration(self):
        return ""
    
    def should_doc_children(self):
        return False
    
    def doc_child_list(self):
        return [ ] 
    
    def get_doc_tags(self):
        return {}
    
    @staticmethod
    def create_schema_node(level, schema_dict):
        # Get the type of the node and create the object
        schema_dict = schema_dict.copy()
        node_type = schema_dict.pop('type', 'map')
        if node_type == 'map':
            schema_node = MapNode(level, schema_dict)
        elif node_type == 'string':
            schema_node = StringNode(level, schema_dict)
        elif node_type == 'number':
            schema_node = NumberNode(level, schema_dict)
        elif node_type == 'list':
            schema_node = ListNode(level, schema_dict)
        elif node_type == 'boolean':
            schema_node = BooleanNode(level, schema_dict)
        elif node_type == 'any':
            schema_node = AnyNode(level, schema_dict)
        else:
            raise SchemaError('Unknown type at level %s' % level)

        # We must have consumed every key in the dictionary
        if len(schema_dict) > 0:
            raise SchemaError('Invalid entries (%s) in schema at level %s for type %s' %
                                                (','.join(list(schema_dict.keys())), level, node_type))
        # Return the schema node
        return schema_node


class AnyNode(SchemaNode):
    expected_types = (string_types, text_type, list, dict, set, tuple, integer_types, float)

    def validate_data(self, data):
        return [ ]
    
    def get_short_decoration(self):
        return "*"
    
    def get_doc_tags(self):
        return {
            "WARNING": "Values set at this level are not validated. Exercise caution."
        }


class StringNode(SchemaNode):
    expected_types = (string_types, text_type)
    type = 'string'

    def __init__(self, level, schema_dict):
        super(StringNode, self).__init__(level, schema_dict)
        self.allowed_values = schema_dict.pop('allowed_values', [])
        pattern = schema_dict.pop('allowed_pattern', None)
        self.valid_pattern = re.compile(pattern) if pattern else None

    def realize_schema(self, attrs):
        super(StringNode, self).realize_schema(attrs)
        if self.allowed_values:
            attrs['allowed_values'] = self.allowed_values
        if self.valid_pattern:
            attrs['allowed_pattern'] = self.valid_pattern
            
    def get_short_decoration(self):
        return "a"
    
    def get_doc_tags(self):
        tags = {}
        if self.allowed_values: 
            tags['Allowed Values'] = ", ".join(self.allowed_values)
        if self.valid_pattern:
            tags['Allowed Pattern'] = self.valid_pattern
        return tags

    def validate_data(self, data):
        # Check for valid values
        if self.allowed_values and data not in self.allowed_values:
            invalid_value = '%s is not a allowed value for %s. Expect it to be one of: %s'
            return [ invalid_value % (data, self.level, ",".join(self.allowed_values)) ]

        if self.valid_pattern and not self.valid_pattern.match(data):
            return [ "%s does't match expression %s at %s" % (data, self.valid_pattern.pattern, self.level)]

        return [ ]


class SubSchemaNode(SchemaNode):
    subschema_denote = '.n'
    def __init__(self, level, schema_dict):
        super(SubSchemaNode, self).__init__(level, schema_dict)
        self._subschema_realized = False
        self._sub_schema = None
        self.sub_schema = schema_dict.pop('value_schema', None)

    def realize_schema(self, attrs):
        super(SubSchemaNode, self).realize_schema(attrs)
        if self.sub_schema:
            attrs['value_schema'] = { }
            self.sub_schema.realize_schema(attrs['value_schema'])

    def get_sub_schema(self):
        return self._sub_schema

    def set_sub_schema(self, obj):
        if isinstance(obj, dict):
            if self._subschema_realized:
                raise SchemaError('Subschema already realized')

            try:
                self.sub_schema = SchemaNode.create_schema_node(self._level+self.subschema_denote, obj)
            except KeyError:
                raise SchemaError('List type node requires a value_schema at %s' % self.level)

            self._subschema_realized = True
        else:
            self._sub_schema = obj

    sub_schema = property(get_sub_schema, set_sub_schema)


class ListNode(SubSchemaNode):
    expected_types = (list, set, tuple)
    type = 'list'
    subschema_denote = "[i]"

    def __init__(self, level, schema_dict):
        super(ListNode, self).__init__(level, schema_dict)
        self.min_size = schema_dict.pop('minimum_size', None)
        self.max_size = schema_dict.pop('maximum_size', None)

        unique = schema_dict.pop('unique', None)
        if unique is not None:
            self.unique = get_bool(unique)
        else:
            self.unique = None

        if self.min_size and self.max_size and self.min_size > self.max_size:
            raise SchemaError('minimum_size can not be greater than maximum_size at %s' % self.level)

        if not self.sub_schema:
            raise SchemaError('value_schema is mandatory for list type')
        
    def get_doc_tags(self):
        return {
            'values': 'Must be unique' if self.unique else 'May have duplicates',
            'minimum size': self.min_size,
            'maximum size': self.max_size
        }

    def realize_schema(self, attrs):
        super(ListNode, self).realize_schema(attrs)
        if self.min_size is not None:
            attrs['minimum_size'] = self.min_size
        if self.max_size is not None:
            attrs['maximum_size'] = self.max_size
        if self.unique is not None:
            attrs['unique'] = self.unique
            
    def should_doc_children(self):
        return True
            
    def get_short_decoration(self):
        #return r'&#x2630;'
        return '[ ]'
    
    def doc_child_list(self):
        return [ ('N/A', self.sub_schema) ] 

    def validate_data(self, data):
        schema_errors = []

        if self.min_size and len(data) < self.min_size:
            schema_errors.append('Minimum size is set to %s, but actual size is %s at level %s' % (self.min_size, len(data), self.level))

        if self.max_size and len(data) < self.min_size:
            schema_errors.append('Maximum size is set to %s, but actual size is %s at level %s' % (self.max_size, len(data), self.level))

        for i, each_value in enumerate(data):
            schema_errors.extend(self.sub_schema.validate(each_value))

        if self.unique:
            dups = set()
            found = set()
            for x in data:
                if x in found:
                    dups.add(x)
                else:
                    found.add(x)
            if dups:
                schema_errors.append('Duplicate(s) %s found for a unique list at %s' % ( ",".join(str(a) for a in dups), self.level))

        return schema_errors


class NumberNode(SchemaNode):
    """ Defines a schema node for numeric data. At present limited to integers only
    """
    expected_types = integer_types
    type = 'number'

    def __init__(self, level, schema_dict):
        super(NumberNode, self).__init__(level, schema_dict)
        self.min_value = schema_dict.pop('minimum_value', None)
        self.max_value = schema_dict.pop('maximum_value', None)

        if self.min_value and self.max_value and self.min_value > self.max_value:
            raise SchemaError("Min and Max values in the schema are incorrect at %s" % self.level)

    def realize_schema(self, attrs):
        super(NumberNode, self).realize_schema(attrs)
        if self.min_value:
            attrs['minimum_value'] = self.min_value
        if self.max_value:
            attrs['maximum_value'] = self.max_value
            
    def get_doc_tags(self):
        tags = {}
        if self.min_value:
            tags['Minimum Value'] = self.min_value
        if self.max_value:
            tags['Maximum Value'] = self.max_value
        return tags
    
    def get_short_decoration(self):
        return "1"

    def validate_data(self, data):
        if self.min_value and data < self.min_value:
            return [ "Value %s is smaller than %s at %s" % (data, self.min_value, self.level)]

        if self.max_value and data > self.max_value:
            return [ "Value %s is greater than %s at %s" % (data, self.max_value, self.level)]

        return [ ]


class BooleanNode(SchemaNode):
    """ Defines a schema node for boolean data
    """
    expected_types = bool
    type = 'boolean'

    def __init__(self, level, schema_dict):
        super(BooleanNode, self).__init__(level, schema_dict)
        self.true_value = schema_dict.pop('true_value', 'True')
        self.false_value = schema_dict.pop('false_value', 'False')

    def realize_schema(self, attrs):
        super(BooleanNode, self).realize_schema(attrs)
        attrs['true_value'] = self.true_value
        attrs['false_value'] = self.false_value
        
    def get_short_decoration(self):
        return r'&#x2713;'
    
    def get_doc_tags(self):
        return {
            'True Value': self.true_value,
            'False Value': self.false_value
        }

    def validate_data(self, data):
        """
        No additional validations necessary for boolean data

        :param data: data
        :return:
        """
        return [ ]


class MapNode(SubSchemaNode):
    """ Defines a schema node for the dictionary data.
    """
    expected_types = dict
    type = 'map'
    subschema_denote = ".<name>"

    def __init__(self, level, schema_dict):
        super(MapNode, self).__init__(level, schema_dict)

        # Create schema nodes for all known children and make sure there is default schema if
        # a name defines no specific schema
        self._preset = False
        self.known_children = schema_dict.pop('known_children', {})
        self.allow_list = schema_dict.pop('allow_list', False)
        
        if self.allow_list:
            self.expected_types = (dict, list)

        # Check for allow unknown values
        try:
            self.allow_unknown_children = get_bool(schema_dict.pop('allow_unknown_children', False))
            if self.allow_unknown_children and self.sub_schema is None:
                raise SchemaError('Unknown children is true without value schema at %s' % level)
        except ValueError:
            raise SchemaError('Unknown boolean value for allow_unknown_children at %s' % level)

        # Get other attributes
        self.mandatory_names = set(schema_dict.pop('mandatory_children', []))
        
    def get_doc_tags(self):
        additional_children = [x[0] for x in iteritems(self.known_children) if x[1] == None]
        tags = {
            'Unknown children': 'Allowed' if self.allow_unknown_children else 'Not Allowed',
            'Can be a list': 'Yes' if self.allow_list else 'No' 
        }
        if additional_children:
            tags['Additinal Children'] = ", ".join(additional_children)
        if self.mandatory_names:
            tags['Must Provide'] = ",".join(self.mandatory_names)
        return tags

    def realize_schema(self, attrs):
        super(MapNode, self).realize_schema(attrs)

        attrs['known_children'] = {}
        for k, v in iteritems(self.known_children):
            attrs['known_children'][k] = {}
            if v:
                v.realize_schema(attrs['known_children'][k])

        attrs['mandatory_children'] = list(self.mandatory_names)

    def get_short_decoration(self):
        return "{ }"
    
    def should_doc_children(self):
        return True
    
    def doc_child_list(self):
        if self.sub_schema:
            yield ('<Name>', self.sub_schema)
        for k,v in iteritems(self.known_children):
            if v:
                yield k, v

    def validate_data(self, data):
        schema_errors = []
        
        def do_validate(data):
            names_found = set()
            # Go to the next level of validation
            for each_key in data:
    
                if each_key not in self.known_children and self.allow_unknown_children == False:
                    schema_errors.append('%s is not allowed at level %s' % (each_key, self.level))
    
                sub_schema = self.known_children.get(each_key) or self.sub_schema
                if not sub_schema:
                    schema_errors.append("No sub-schema found for %s at %s" % (each_key, self.level))
                else:
                    schema_errors.extend(sub_schema.validate(data[each_key]))
    
                names_found.add(each_key)
    
            remaining_names = self.mandatory_names - names_found
            if remaining_names:
                schema_errors.append("Values are required for %s at %s" % (",".join(remaining_names), self.level))
        
        if self.allow_list:
            if isinstance(data, list):
                level_save = self.level
                for i,x in enumerate(data):
                    self.level = level_save + str(i)
                    do_validate(x)
            else:
                do_validate(data)
        else:
            do_validate(data)

        return schema_errors

    def set_known_children(self, child_object):
        if isinstance(child_object, dict):
            if (self._preset):
                raise SchemaError('CODE ERROR: Setting children twice')
            self._preset = True
            self._known_children = {}
            for k,v in iteritems(child_object):
                if v:
                    self._known_children[k] = SchemaNode.create_schema_node(self._level+'.'+k, v)
                else:
                    self._known_children[k] = None
                    if self.sub_schema is None:
                        raise SchemaError('Name %s defines no schema and there is no value schema at %s' % (k, self._level))
        else:
            self._preset = False
            self._known_children = child_object

    def get_known_children(self):
        return self._known_children

    known_children = property(get_known_children, set_known_children)


class SchemaError(Exception):
    """ This is a marker to know SchemaErrors from other errors. No
    additional methods are defined inside.
    """
    pass
