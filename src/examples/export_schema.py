from schema import Method
import json

"""
File to create a JSON Schema (stored in `./examples/schema_json.json`) based on the example data model defined
in `./examples/schema.py`. 

This JSON Schema is produced by calling `Method.model_json_schema()`, where `Method` is defined in `schema.py`. 
"""

schema = Method.model_json_schema()

with open("schema_json.json", "w") as f:
    json.dump(schema, f, indent=2)
 