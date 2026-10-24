"""A small strict validator for our public tool subset; no dependency downloads."""
from .tools import schemas

def validate_value(value,schema):
    kind=schema.get('type')
    correct={'object':lambda:isinstance(value,dict),'array':lambda:isinstance(value,list),'string':lambda:isinstance(value,str),'boolean':lambda:type(value) is bool,'integer':lambda:type(value) is int}
    if kind in correct and not correct[kind]():raise ValueError('Invalid argument type')
    if isinstance(value,str) and len(value)>6000:raise ValueError('Argument too long')
    if 'enum' in schema and value not in schema['enum']:raise ValueError('Invalid argument value')
    if kind=='object':
        props=schema.get('properties',{})
        if not set(schema.get('required',[]))<=set(value):raise ValueError('Missing required argument')
        if schema.get('additionalProperties') is False and set(value)-set(props):raise ValueError('Unexpected argument')
        for k,v in value.items():
            if k in props:validate_value(v,props[k])
    if kind=='array':
        if len(value)>schema.get('maxItems',100):raise ValueError('Too many values')
        for x in value:validate_value(x,schema.get('items',{}))

def validate_action(name,args):
    if not isinstance(name,str):raise ValueError('Unknown action')
    for tool in schemas():
        if tool['function']['name']==name:
            validate_value(args,tool['function']['parameters']);return
    raise ValueError('Unknown action')
