"""Сервисный слой"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.geo import bbox_for_radius, bbox_for_rectangle, haversine_m
from app.models import Organization
from app.repositories import BuildingsRepository, OrgsRepository
from app.schemas import BuildingOut, GeoSearchOut, OrganizationOut


def org_to_out(o: Organization) -> OrganizationOut:
    """
        Преобразует ORM-модель Organization в публичную DTO-схему OrganizationOut

        Args:
            o: ORM-объект Organization

        Returns:
            OrganizationOut: DTO для ответа
    """
    return OrganizationOut.model_validate(
        {
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

    def get_organization(self, db: Session, org_id: int) -> OrganizationOut:
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
        org = self.orgs.get_org_by_id(db, org_id)
        if org is None:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )
        return org_to_out(org)

    def search_by_name(self, db: Session, q: str) -> list[OrganizationOut]:
        """
            Ищет организации по подстроке в названии

            Args:
                db: SQLAlchemy-сессия
                q: Поисковая строка

            Returns:
                list[OrganizationOut]: Список найденных организаций
        """
        return [org_to_out(o) for o in self.orgs.search_orgs_by_name(db, q)]

    def organizations_in_building(
            self,
            db: Session,
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
        return [org_to_out(o) for o in self.orgs.orgs_in_building(
            db,
            building_id,
            )
        ]

    def organizations_by_activity(
            self,
            db: Session,
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
        if not self.orgs.activity_exists(db, activity_id):
            raise HTTPException(status_code=404, detail="Activity not found")

        ids = self.orgs.activity_descendants_ids(db, activity_id)
        orgs = self.orgs.orgs_by_activity_ids(db, ids)
        return [org_to_out(o) for o in orgs]

    def geo_radius(
            self,
            db: Session,
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
        buildings = self.buildings.buildings_in_bbox(db, bbox)
        near = [b for b in buildings if haversine_m(
            lat,
            lon,
            b.lat,
            b.lon,
        ) <= r_m]

        if not near:
            return GeoSearchOut(organizations=[], buildings=[])

        b_ids = {b.id for b in near}
        orgs = []
        for b_id in b_ids:
            orgs.extend(self.orgs.orgs_in_building(db, b_id))

        return GeoSearchOut(
            organizations=[org_to_out(o) for o in orgs],
            buildings=[BuildingOut.model_validate(
                b,
                from_attributes=True,
            ) for b in near],
        )

    def geo_rectangle(
            self,
            db: Session,
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
        bbox = bbox_for_rectangle(lat1, lon1, lat2, lon2)
        buildings = self.buildings.buildings_in_bbox(db, bbox)

        if not buildings:
            return GeoSearchOut(organizations=[], buildings=[])

        b_ids = {b.id for b in buildings}
        orgs = []
        for b_id in b_ids:
            orgs.extend(self.orgs.orgs_in_building(db, b_id))

        return GeoSearchOut(
            organizations=[org_to_out(o) for o in orgs],
            buildings=[BuildingOut.model_validate(
                b,
                from_attributes=True,
            ) for b in buildings],
        )
