"""Сервисный слой"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.geo import bbox_for_radius, bbox_for_rectangle, haversine_m
from app.models.models import Building, Organization
from app.repo.repositories import BuildingsRepository, OrgsRepository
from app.schemas.schemas import BuildingOut, GeoSearchOut, OrganizationOut


def org_to_out(o: Organization) -> OrganizationOut:
    """
        Преобразует ORM-модель Organization в публичную DTO-схему OrganizationOut

        Args:
            o: ORM-объект Organization

        Returns:
            OrganizationOut: DTO для ответа
    """
    return OrganizationOut.model_validate(
        obj={
            "id": o.id,
            "name": o.name,
            "building": o.building, "phones": [p.phone for p in o.phones],
            "activities": [a.name for a in o.activities],
        },
        from_attributes=True,
    )


class OrgsService:
    """
        Сервис для чтения организаций/зданий/активностей и геопоиска

        Args:
            orgs: Репозиторий организаций
            buildings: Репозиторий зданий
    """
    def __init__(
            self,
            orgs: OrgsRepository,
            buildings: BuildingsRepository,
    ) -> None:
        self.orgs = orgs
        self.buildings = buildings

    async def _get_orgs_by_buildings(
            self,
            db: AsyncSession,
            buildings: list[Building],
    ) -> list[Organization]:
        if not buildings:
            return []

        b_ids = [b.id for b in buildings]
        return await self.orgs.orgs_by_building_ids(
            db=db,
            building_ids=b_ids,
        )

    async def get_organization(
            self,
            db: AsyncSession,
            org_id: int,
    ) -> OrganizationOut:
        """
            Возвращает организацию по id

            Args:
                db: SQLAlchemy-сессия
                org_id: ID организации

            Returns:
                OrganizationOut: DTO для ответа

            Raises:
                HTTPException: 404, если организация не найдена
        """
        org = await self.orgs.get_org_by_id(
            db=db,
            org_id=org_id,
        )
        if org is None:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )
        return org_to_out(org)

    async def search_by_name(
            self,
            db: AsyncSession,
            q: str,
    ) -> list[OrganizationOut]:
        """
            Ищет организации по подстроке в названии

            Args:
                db: SQLAlchemy-сессия
                q: Поисковая строка

            Returns:
                list[OrganizationOut]: Список найденных организаций
        """
        orgs = await self.orgs.search_orgs_by_name(
            db=db,
            q=q,
        )
        return [org_to_out(o) for o in orgs]

    async def organizations_in_building(
            self,
            db: AsyncSession,
            building_id: int,
    ) -> list[OrganizationOut]:
        """
            Возвращает все организации, расположенные в конкретном здании

            Args:
                db: SQLAlchemy-сессия
                building_id: ID здания

            Returns:
                list[OrganizationOut]: Список организаций в здании
        """
        orgs = await self.orgs.orgs_in_building(
            db=db,
            building_id=building_id,
        )
        return [org_to_out(o) for o in orgs]

    async def organizations_by_activity(
            self,
            db: AsyncSession,
            activity_id: int,
    ) -> list[OrganizationOut]:
        """
            Возвращает организации по виду деятельности с учётом дочерних видов до глубины 3

            Args:
                db: SQLAlchemy-сессия
                activity_id: ID вида деятельности

            Returns:
                list[OrganizationOut]: Список организаций, относящихся к activity

            Raises:
                HTTPException: 404, если activity не существует
        """
        exists = await self.orgs.activity_exists(
            db=db,
            activity_id=activity_id,
        )
        if not exists:
            raise HTTPException(
                status_code=404,
                detail="Activity not found",
            )

        ids = await self.orgs.activity_descendants_ids(
            db=db,
            root_activity_id=activity_id,
        )
        orgs = await self.orgs.orgs_by_activity_ids(
            db=db,
            activity_ids=ids,
        )
        return [org_to_out(o) for o in orgs]

    async def geo_radius(
            self,
            db: AsyncSession,
            lat: float,
            lon: float,
            r_m: float,
    ) -> GeoSearchOut:
        """
            Геопоиск организаций в радиусе r_m метров от точки

            Args:
                db: SQLAlchemy-сессия
                lat: Широта точки
                lon: Долгота точки
                r_m: Радиус в метрах

            Returns:
                GeoSearchOut:
                    - buildings: здания, попавшие в радиус
                    - organizations: организации в этих зданиях
        """
        bbox = bbox_for_radius(lat, lon, r_m)
        buildings = await self.buildings.buildings_in_bbox(
            db=db,
            bbox=bbox,
        )
        near = [b for b in buildings if haversine_m(
            lat1=lat,
            lon1=lon,
            lat2=b.lat,
            lon2=b.lon,
        ) <= r_m]

        if not near:
            return GeoSearchOut(
                organizations=[],
                buildings=[],
            )

        orgs = await self._get_orgs_by_buildings(
            db=db,
            buildings=near,
        )

        return GeoSearchOut(
            organizations=[org_to_out(o) for o in orgs],
            buildings=[BuildingOut.model_validate(
                obj=b,
                from_attributes=True,
            ) for b in near],
        )

    async def geo_rectangle(
            self,
            db: AsyncSession,
            lat1: float,
            lon1: float,
            lat2: float,
            lon2: float,
    ) -> GeoSearchOut:
        """
            Геопоиск организаций в прямоугольнике, заданной области

            Args:
                db: SQLAlchemy-сессия
                lat1: Широта первой точки
                lon1: Долгота первой точки
                lat2: Широта второй точки
                lon2: Долгота второй точки

            Returns:
                GeoSearchOut:
                    - buildings: здания внутри прямоугольника
                    - organizations: организации в этих зданиях
        """
        bbox = bbox_for_rectangle(
            lat1=lat1,
            lon1=lon1,
            lat2=lat2,
            lon2=lon2,
        )
        buildings = await self.buildings.buildings_in_bbox(
            db=db,
            bbox=bbox,
        )

        if not buildings:
            return GeoSearchOut(
                organizations=[],
                buildings=[],
            )

        orgs = await self._get_orgs_by_buildings(
            db=db,
            buildings=buildings,
        )

        return GeoSearchOut(
            organizations=[org_to_out(o) for o in orgs],
            buildings=[BuildingOut.model_validate(
                obj=b,
                from_attributes=True,
            ) for b in buildings],
        )
