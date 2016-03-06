
This project provides a way to validate recursive data structures created using
dictionaries, tuples, lists etc.  Proper way of adding validations should be
to add python classes in the mix, but lot of times we end up with simple data
structures as they are easy to start.  This project provides a way to create
schema definition for such objects. 

Schema definition is done recursively using attributes given here and allow any depth to of the metadata to be specified.  

Each level is described by the following properties in a python dictionary:

| Name | Description | Required | Lambda Support | Default |
| ---- | ---- | ---- | ---- | ---- |
| display_name | Name to be used in the display | True | False | n/a |
| description | Helpful information about this element | False | False | Blank string |
| type | Data type of the value. Should be one of map, list, string, number or boolean | False | True | n/a |
| value_schema | Schema to be used for any of the child values by default. | Depends(1) | True | n/a |
| known_children | A map of named children that are allowed for a map.  Each named children can have their own schema the value. If it is blank dictionary, or None, value_schema is used. | False | True | Blank Map | 
| ---- | ---- | ---- | ---- | ---- |


1. For each complex type of object, schema is required either directly or through inheritance.  Schema defined here is used for all children where an explicit schema is not defined.



NOTE for backend: Known names can be a string instead of map, in which case this string is interpolated as python code using eval.  We expect the return value of this eval to be a map as if it is specified inside the code.

It is possible that this map might not contains names for which information is already provided.  Such names are logged as warnings and will not be displayed.  Making changes in such cases will remove these values.  (Unless of course allow_unknown_values is set to true)
	False	True	Empty map
allow_unknown_children	Should the UI allow adding children whose names are not known.  If this is set to true, schema attribute above must be defined. 	False	False	False
minimum_value	Used for int type leaf nodes only. 	False	True	No Limit
maximum_value	Used for int type leaf nodes only.	False	True	No Limit
valid_pattern	Used for string type values only.  Regular expression to validate given input strings.	False	False	No restrictions
valid_values	Used for string type values only.  List of values allowed to be set.	False	True	No restrictions
true_value.	Used for boolean type leaf nodes only.  String to be displayed if the underlying value is True.   For example: Yes, Enabled, True etc.	False	False	True
false_value	Used for boolean type leaf nodes only.  String to be displayed if the underlying value is True.   For example: No, Disabled, False etc.	False	False	True
default_value	

Value to be used as default if not provided in the json document.

When get_config, or any such parser is called and there is no default, it should result in an exception.  However default can be merely informative in many cases.
	False	True	See Note
mandatory_children	Names for which values must be provided.  Useful for a map only.	False	True	No Restrictions

 

Schema document always follows a strict tree, and the root most node is not used in this case.  The root node will basically have all the top level categories as known_names, and sets allow_unknown_names to be false.

We expect the first 2 levels to be displayed as the tree depicted above, and all the levels below to be displayed as Forms and Panels that allow insertion, deletion, re-ordering (for lists) etc.


