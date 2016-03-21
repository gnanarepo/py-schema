"""
This module allows validation of dictionaries or lists that contain unstructured data.
While using python objects is the right approach to have structured data, many apps
nevertheless use dictionaries or lists of various data and are stuck with it, specifically
for saving configuration etc.
"""
import re
import traceback

type_mismatch = 'Expecting value to be {type} but got {actual_type} for {level}'
invalid_boolean = 'Invalid Value for boolean field'

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
    def __init__(self, schema_dict):
        self.root = SchemaNode.create_schema_node('root', schema_dict)

    def validate(self, data):
        return self.root.validate(data)

    def realize(self):
        realized_schema = {}
        self.root.realize_schema(realized_schema)
        return realized_schema


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
            self.description = schema_dict.pop('description', '')
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
            elif isinstance(code_like, basestring):
                ret_value = eval(code_like)
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
            schema_errors.extend(self.custom_validation(data))

        return schema_errors

    def validate_data(self, data):
        raise SchemaError('CODE ERROR: Each child node must implement this method')

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
                                                (','.join(schema_dict.keys()), level, node_type))
        # Return the schema node
        return schema_node


class AnyNode(SchemaNode):
    expected_types = (str, unicode, list, dict, set, tuple, int)

    def validate_data(self, data):
        return [ ]


class StringNode(SchemaNode):
    expected_types = (str, unicode)
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

    def validate_data(self, data):
        # Check for valid values
        if self.allowed_values and data not in self.allowed_values:
            invalid_value = '%s is not a allowed value for %s. Expect it to be one of: %s'
            return [ invalid_value % (data, self.level, ",".join(self.allowed_values)) ]

        if self.valid_pattern and not self.valid_pattern.match(data):
            return [ "%s does't match expression %s at %s" % (data, self.valid_pattern.pattern, self.level)]

        return [ ]


class SubSchemaNode(SchemaNode):

    def __init__(self, level, schema_dict):
        super(SubSchemaNode, self).__init__(level, schema_dict)
        self._subschema_realized = False
        self._sub_schema = None
        self.sub_schema = schema_dict.pop('value_schema', None)

    def get_sub_schema(self):
        return self._sub_schema

    def set_sub_schema(self, obj):
        if isinstance(obj, dict):
            if self._subschema_realized:
                raise SchemaError('Subschema already realized')

            try:
                self.sub_schema = SchemaNode.create_schema_node(self._level+'.n', obj)
            except KeyError:
                raise SchemaError('List type node requires a value_schema at %s' % self.level)

            self._subschema_realized = True
        else:
            self._sub_schema = obj

    sub_schema = property(get_sub_schema, set_sub_schema)


class ListNode(SubSchemaNode):
    expected_types = (list, set, tuple)
    type = 'list'

    def __init__(self, level, schema_dict):
        super(ListNode, self).__init__(level, schema_dict)
        self.min_size = schema_dict.pop('minimum_size', None)
        self.max_size = schema_dict.pop('maximum_size', None)

    def realize_schema(self, attrs):
        super(ListNode, self).realize_schema(attrs)
        sub_attrs = {}
        self.sub_schema.realize_schema(sub_attrs)
        attrs['value_schema'] = sub_attrs

    def validate_data(self, data):
        schema_errors = []

        if self.min_size and len(data) < self.min_size:
            schema_errors.extend('Minimum size is set to %s, but actual size is %s at level %s' % (self.min_size, len(data), self.level))

        if self.max_size and len(data) < self.min_size:
            schema_errors.extend('Maximum size is set to %s, but actual size is %s at level %s' % (self.max_size, len(data), self.level))

        for i, each_value in enumerate(data):

            schema_errors.extend(self.sub_schema.validate(each_value))

        return schema_errors


class NumberNode(SchemaNode):
    """ Defines a schema node for numeric data. At present limited to integers only
    """
    expected_types = int
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

    def __init__(self, level, schema_dict):
        super(MapNode, self).__init__(level, schema_dict)

        # Create schema nodes for all known children and make sure there is default schema if
        # a name defines no specific schema
        self._preset = False
        self.known_children = schema_dict.pop('known_children', {})

        # Check for allow unknown values
        try:
            self.allow_unknown_children = get_bool(schema_dict.pop('allow_unknown_children', False))
            if self.allow_unknown_children and self.sub_schema is None:
                raise SchemaError('Unknown children is true without value schema at %s' % level)
        except ValueError:
            raise SchemaError('Unknown boolean value for allow_unknown_children at %s' % level)

        # Get other attributes
        self.mandatory_names = set(schema_dict.pop('mandatory_children', []))

    def realize_schema(self, attrs):
        super(MapNode, self).realize_schema(attrs)

        if self.sub_schema:
            attrs['value_schema'] = {}
            self.sub_schema.realize_schema(attrs['value_schema'])

        attrs['known_children'] = {}
        for k, v in self.known_children.iteritems():
            attrs['known_children'][k] = {}
            if v:
                v.realize_schema(attrs['known_children'][k])

        attrs['mandatory_children'] = list(self.mandatory_names)


    def validate_data(self, data):
        schema_errors = []
        names_found = set()
        # Go to the next level of validation
        for each_key in data:

            if each_key not in self.known_children and self.allow_unknown_children == False:
                schema_errors.append('%s is not allowed at level %s' % (each_key, self.level))

            sub_schema = self.known_children.get(each_key) or self.sub_schema
            schema_errors.extend(sub_schema.validate(data[each_key]))

            names_found.add(each_key)

        remaining_names = self.mandatory_names - names_found
        if remaining_names:
            schema_errors.append("Values are required for %s at %s" % (",".join(remaining_names), self.level))

        return schema_errors

    def set_known_children(self, child_object):
        if isinstance(child_object, dict):
            if (self._preset):
                raise SchemaError('CODE ERROR: Setting children twice')
            self._preset = True
            self._known_children = {}
            for k,v in child_object.iteritems():
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
