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