from pydantic import BaseModel, ConfigDict


class BuildingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address: str
    lat: float
    lon: float

    class Config:
        from_attributes = True


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    building: BuildingOut
    phones: list[str]

    class Config:
        from_attributes = True
