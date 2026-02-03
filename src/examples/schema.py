from __future__ import annotations

from pydantic import BaseModel, Field


# class Example(BaseModel):
#     id: str = Field(..., description="The unique identifier")


# class Person(BaseModel):
#     name: str = Field(..., description="The person's name")
#     age: int = Field(..., ge=0, description="The person's age in years")
#     example: Example


# class BaseMethod(BaseModel):
#     author: str = Field(..., description="The author of the method")


# class Method(BaseMethod):
#     method_name: str = Field(..., description="The name of the method")
#     person: Person




class Example(BaseModel):
    id: str = Field(..., description="The unique identifier")
    note: str | None = Field(None, description="Optional note (can be null)")


class Person(BaseModel):
    name: str = Field(..., description="The person's name")
    age: int = Field(..., ge=0, description="The person's age in years")
    nickname: str | None = Field(None, description="Optional nickname")
    tags: list[str] = Field(default_factory=list, description="List of tags")
    example: Example


class BaseMethod(BaseModel):
    author: str = Field(..., description="The author of the method")


class Method(BaseMethod):
    method_name: str = Field(..., description="The name of the method")
    person: Person
    comment: str | None = Field(None, description="Optional comment")

