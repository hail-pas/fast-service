import strawberry
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


class Vehicle(BaseModel):
    vin: str
    license_no: str


@strawberry.experimental.pydantic.type(model=User)
class UserType:
    id: strawberry.auto
    name: strawberry.auto
    friend: strawberry.auto


@strawberry.experimental.pydantic.type(model=Vehicle, all_fields=True)
class VehicleType:
    pass
