from schema import Method
import json

"""File to create a json for "Ticket - schema_json.json" with model_json_schema()
this can also be run in a terminal 
"""

schema = Method.model_json_schema()

with open("schema_json.json", "w") as f:
    json.dump(schema, f, indent=4)
 