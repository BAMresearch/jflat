"""
PROJECT JFLAT 

KURZ-GOAL ->  Pydantic model → .model_dump() → nested JSON/dict → JFlat → flattened dict
"""

from typing import Any, Dict


class JFlat:
    """
    A tiny helper class that accepts any JSON‑like dictionary
    and can flatten it.

    Usage:
        flat = JFlat(input_json).flatten()
        print(flat)
    """

    def __init__(self, input_json: Dict[str, Any]):
        if not isinstance(input_json, dict):
            raise ValueError("JFlat only accepts dictionaries.")
        self.input_json = input_json

    # ------------------------------------------------------------
    # Public method
    # ------------------------------------------------------------
    def flatten(self) -> Dict[str, Any]:
        """
        Returns a flattened dictionary.
        Example: {"director": {"name": "X"}} becomes {"director_name": "X"}
        """
        flat_dict: Dict[str, Any] = {}
        self._flatten_recursive(self.input_json, parent_key="", output=flat_dict)
        return flat_dict

    # ------------------------------------------------------------
    # Internal recursive function
    # ------------------------------------------------------------
    def _flatten_recursive(self, obj: Any, parent_key: str, output: Dict[str, Any]):
        """
        Recursively walks through the JSON dictionary and stores
        flattened key/value pairs.
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}_{key}" if parent_key else key
                self._flatten_recursive(value, new_key, output)
        else:
            output[parent_key] = obj


# ----------------------------------------------------------------
# Example usage (your demo for MIT students)
# ----------------------------------------------------------------
if __name__ == "__main__":
    # A nested JSON similar to what Pydantic .model_dump() produces
    # Example with a little humor: Christopher Nolan is still 50 :-)
    input_json = {
        "title": "Inception",
        "director": {
            "name": "Christopher Nolan",
            "age": 50
        }
    }

    print("\nINPUT JSON (nested):")
    print(input_json)

    # flatten it
    jflat = JFlat(input_json)
    output = jflat.flatten()

    print("\nOUTPUT JSON (flattened):")
    print(output)

    # Expected output:
    # {
    #   "title": "Inception",
    #   "director_name": "Christopher Nolan",
    #   "director_age": 50
    # }


"""
INPUT:
{
   "pizza": {
       "toppings": {
           "cheese": "mozzarella",
           "extra": "pineapple (controversial!)"
       }
   }
}

OUPUT:
{
    "pizza_toppings_cheese": "mozzarella",
    "pizza_toppings_extra": "pineapple (controversial!)"
}
"""

