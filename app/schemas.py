from pydantic import BaseModel, ConfigDict


class BuildingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address: str
    lat: float
    lon: float


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    building: BuildingOut
    phones: list[str]
    activities: list[str]


class GeoSearchOut(BaseModel):
    organizations: list[OrganizationOut]
    buildings: list[BuildingOut]
