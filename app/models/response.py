from pydantic import BaseModel
from typing import List

class Restaurant(BaseModel):
    name: str
    reason: str
    location: str

class ResponseModel(BaseModel):
    restaurants: List[Restaurant]