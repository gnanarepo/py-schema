
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
| Map Specific | --- | --- | --- | --- |
| known_children | A map of named children that are allowed for a map.  Each named children can have their own schema the value. If it is blank dictionary, or None, value_schema is used. | False | True | Blank Map | 
| allow_unknown_children | Should the UI allow adding children whose names are not known.  If this is set to true, value schema attribute above must be defined. | False | False | False |
| mandatory_children | Names for which values must be provided.  Useful for a map only.	| False | True | No Restrictions | 
| Number Specific | --- | --- | --- | --- |
| minimum_value | Used for int type leaf nodes only. | False | True | No Limit |
| maximum_value	| Used for int type leaf nodes only.| False | True | No Limit | 
| String Specific | --- | --- | --- | --- |
| allowed_pattern | Used for string type values only.  Regular expression to validate given input strings. | False | False | No restrictions |
| valid_values | Used for string type values only.  List of values allowed to be set. | False | True | No restrictions | 
| Boolean Specific | --- | --- | --- | --- |
| true_value. | Used for boolean type leaf nodes only.  String to be displayed if the underlying value is True. For example: Yes, Enabled, True etc. | False | False | True | 
| false_value | Used for boolean type leaf nodes only. | String to be displayed if the underlying value is True. For example: No, Disabled, False etc. | False | False | True |


1. For each complex type of object, schema is required either directly or through inheritance.  Schema defined here is used for all children where an explicit schema is not defined.
2. It is possible that this map might not contains names for which information is already provided.  Such names are logged as warnings and will not be displayed.  Making changes in such cases will remove these values.  (Unless of course allow_unknown_values is set to true)

Lambda Support


