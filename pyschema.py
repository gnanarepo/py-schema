"""
This module allows validation of dictionaries or lists that contain unstructured data.
While using python objects is the right approach to have structured data, many apps
nevertheless use dictionaries or lists of various data and are stuck with it, specifically
for saving configuration etc.
"""
import re


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
        ('value_schema', dict),
        ('minimum_value', int),
        ('maximum_value', float),
        ('allowed_values', (list, set, tuple))
    }
    expected_types = None
    type = None

    def __init__(self, level, schema_dict):
        self.level = level
        try:
            self.display_name = schema_dict.pop('display_name')
        except:
            raise SchemaError('display_name is mandatory at level %s' % self.level)
        self.level += '(%s)' % self.display_name
        self.realized = False
        self.verbatim = schema_dict.pop('verbatim', None)

    def process_children(self):
        raise SchemaError('CODE ERROR: Each child node must implement this method')

    def _execute_if_necessary(self, code_like, expected_type):
        if isinstance(code_like, expected_type):
            ret_value = code_like
        else:
            if callable(code_like):
                ret_value = code_like()
            elif isinstance(code_like, basestring):
                ret_value = eval(code_like)
            else:
                raise SchemaError("Don't known how to execute dynamic schema at %s" % self.level)

            if not isinstance(ret_value, expected_type):
                schema_type_mismatch = "Dynamic schema generated %s doesn't match the expected type %s at %s"
                raise SchemaError( schema_type_mismatch % (type(ret_value), expected_type, self.level))

        return ret_value

    def _realize_node(self):
        for key_name, expected_type in self.allowed_expansions:
            obj = getattr(self, key_name, None)
            if obj:
                try:
                    obj = self._execute_if_necessary(obj, expected_type)
                    setattr(self, key_name, obj)
                except SchemaError:
                    raise
                except Exception:
                    raise SchemaError("Error when realizing dynamic schema for %s at %s" % (key_name, self.level))

        self.realized = True

    def realize_schema(self, attrs):
        if not self.realized:
            self._realize_node()

        attrs['display_name'] = self.display_name
        attrs['type'] = self.type
        if self.verbatim is not None:
            attrs['verbatim'] = self.verbatim

    def validate(self, data):
        """
        Validate the data and return the violations found

        :param data:
        :return: List of violations.  Each violation is basically a string, and it is unstructured.
        """
        # Realize if necessary
        if not self.realized:
            print "Realizing the schema"
            self._realize_node()

        # Perform common validation
        if not isinstance(data, self.expected_types):
            return [
                type_mismatch.format(type=str(self.expected_types),
                                     actual_type = str(type(data)),
                                     level=self.level)
            ]

        # Perform node specific validation
        return self.validate_data(data)

    def validate_data(self, data):
        raise SchemaError('CODE ERROR: Each child node must implement this method')


    @staticmethod
    def create_schema_node(level, schema_dict):
        # Get the type of the node and create the object
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
        else:
            raise SchemaError('Unknown type at level %s' % level)

        # We must have consumed every key in the dictionary
        if len(schema_dict) > 0:
            raise SchemaError('Invalid entries (%s) in schema at level %s for type %s' %
                                                (','.join(schema_dict.keys()), level, node_type))

        # Return the schema node
        return schema_node


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


class ListNode(SchemaNode):
    expected_types = (list, set, tuple)
    type = 'list'

    def __init__(self, level, schema_dict):
        super(ListNode, self).__init__(level, schema_dict)

        try:
            self.sub_schema = SchemaNode.create_schema_node(level+'.n', schema_dict.pop('value_schema'))
        except KeyError:
            raise SchemaError('List type node requires a value_schema at %s' % self.level)

    def realize_schema(self, attrs):
        super(ListNode, self).realize_schema(attrs)
        sub_attrs = {}
        self.sub_schema.realize_schema(sub_attrs)
        attrs['value_schema'] = sub_attrs

    def validate_data(self, data):
        schema_errors = []
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


class MapNode(SchemaNode):
    """ Defines a schema node for the dictionary data.
    """
    expected_types = dict
    type = 'map'

    def __init__(self, level, schema_dict):
        super(MapNode, self).__init__(level, schema_dict)

        # Create the default schema node if necessary
        default_schema = schema_dict.pop('value_schema', None)
        if default_schema:
            self.value_schema = SchemaNode.create_schema_node(level+'.default', default_schema)
        else:
            self.value_schema = None

        # Create schema nodes for all known children and make sure there is default schema if
        # a name defines no specific schema
        self.known_children = {}
        for k,v in schema_dict.pop('known_children', {}).iteritems():
            if v:
                self.known_children[k] = SchemaNode.create_schema_node(level+'.'+k, v)
            else:
                self.known_children[k] = None
                if self.value_schema is None:
                    raise SchemaError('Name %s defines no schema and there is no value schema at %s' % (k, level))

        # Check for allow unknown values
        try:
            self.allow_unknown_children = get_bool(schema_dict.pop('allow_unknown_children', False))
            if self.allow_unknown_children and self.value_schema is None:
                raise SchemaError('Unknown children is true without value schema at %s' % level)
        except ValueError:
            raise SchemaError('Unknown boolean value for allow_unknown_children at %s' % level)

        # Get other attributes
        self.mandatory_names = set(schema_dict.pop('mandatory_children', []))

    def realize_schema(self, attrs):
        super(MapNode, self).realize_schema(attrs)

        if self.value_schema:
            attrs['value_schema'] = {}
            self.value_schema.realize_schema(attrs['value_schema'])

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

            sub_schema = self.known_children[each_key] or self.value_schema
            schema_errors.extend(sub_schema.validate(data[each_key]))

            names_found.add(each_key)

        remaining_names = self.mandatory_names - names_found
        if remaining_names:
            schema_errors.append("Values are required for %s at %s" % (",".join(remaining_names), self.level))

        return schema_errors


class SchemaError(Exception):
    """ This is a marker to know SchemaErrors from other errors. No
    additional methods are defined inside.
    """
    pass
