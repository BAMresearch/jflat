from pydantic import BaseModel, Field

class Example(BaseModel):
    id: str = Field(..., description="The unique identifier")


class Person(BaseModel):
    name: str = Field(..., description="The person's name")
    age: int = Field(..., ge=0, description="The person's age in years")
    example: Example


class BaseMethod(BaseModel):
    author: str = Field(..., description="The author of the method")


class Method(BaseMethod):
    method_name: str = Field(..., description="The name of the method")
    person: Person


#ToDo Maybe you can define more types in this example? Something like str | none, and create more different Fields (so the printed JSON schema is actually richer and we can cover more cases)


"""
src/jflat/jflat.py def flatten_json(data: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:

The goal of this function is more to map a JSON Schema (as printed by pydantic) to our new flattened version. The end result should look something like:

{
    "$defs": {       
        "Method": {
            "properties": {
                "author": {
                   "description": "The author of the method",
                   "type": "string"
                },
                "method_name": {
                   "description": "The name of the method",
                   "type": "string"
                },
                "person": {
                   "$ref": "#/$defs/Person"
                }
            },
            "description": "...<whatever-here>...",
            "$inherits_from": "#/$defs/BaseMethod",
        },       
        <other classes here>
}}
As you can see, I slightly modified the resulting JSON schema when printed using model_json_schema. The idea is to get rid off unnecessary stuff and adding some other info. I:

Deleted title in each property
Deleted title in each object
Added an $inherits_from key in each of the objects dictionaries
Moved the Method defs inside $defs (before, it is outside because we are printing from it)
We need to add BaseMethod to define inheritances
Deleted all the required and type:object stuff
We could also:

Add a key inside each property defining if they are mandatory or optional (this was before defined by required. Somethind like:
        "author": {
            "description": "The author of the method",
            "type": "string",
            "mandatory": true   # this can also be false, if the property is optional (i.e., str | None)
        },

"""