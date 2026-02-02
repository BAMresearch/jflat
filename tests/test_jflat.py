
from jflat.jflat import flatten_json


def test_flatten_json_simple():
    data = {"a": 1, "b": 2}
    assert flatten_json(data) == {"a": 1, "b": 2}


def test_flatten_json_nested():
    data = {
        "person": {
            "name": "Alice",
            "info": {
                "age": 30
            }
        }
    }

    flattened = flatten_json(data)

    assert flattened == {
        "person_name": "Alice",
        "person_info_age": 30
    }


from yourpackage.jflat import JFlat

def test_flatten_simple():
    j = JFlat({"a": {"b": 1}})
    result = j.flatten()
    assert result == {"a.b": 1}