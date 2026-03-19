"""Pydantic-схемы(DTO) для публичного API"""
from pydantic import BaseModel, ConfigDict


class BuildingOut(BaseModel):
    """
        Публичное представление здания

        Attributes:
            id: Идентификатор здания
            address: Адрес
            lat: Широта
            lon: Долгота
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    address: str
    lat: float
    lon: float


class OrganizationOut(BaseModel):
    """
        Публичное представление организации

        Attributes:
            id: Идентификатор организации
            name: Название организации
            building: Вложенный объект BuildingOut
            phones: Список телефонных номеров
            activities: Список видов деятельности
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    building: BuildingOut
    phones: list[str]
    activities: list[str]


class GeoSearchOut(BaseModel):
    """
        Ответ геопоиска

        Attributes:
            organizations: Организации, попавшие в область поиска
            buildings: Здания, попавшие в область поиска
    """
    organizations: list[OrganizationOut]
    buildings: list[BuildingOut]
