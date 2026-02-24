"""Слой доступа к данным"""
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.geo import BBox
from app.models import Activity, Building, Organization


class OrgsRepository:
    """Репозиторий для работы с организациями и деятельностями"""
    @staticmethod
    def get_org_by_id(db: Session, org_id: int) -> Organization | None:
        """
            Возвращает организацию по id

            Args:
                db: Активная SQLAlchemy-сессия
                org_id: Идентификатор организации

            Returns:
                Organization | None: ORM-объект или None
        """
        stmt = (
            select(Organization)
            .where(Organization.id == org_id)
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def search_orgs_by_name(db: Session, q: str) -> list[Organization]:
        """
            Поиск организаций по части названия

            Args:
                db: SQLAlchemy-сессия
                q: Поисковая строка

            Returns:
                list[Organization]: Список ORM-сущностей
        """
        stmt = (
            select(Organization)
            .where(Organization.name.ilike(f"%{q}%"))
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def orgs_in_building(db: Session, building_id: int) -> list[Organization]:
        """
            Возвращает все организации в указанном здании

            Args:
                db: SQLAlchemy-сессия
                building_id: ID здания

            Returns:
                list[Organization]: Организации в здании
        """
        stmt = (
            select(Organization)
            .where(Organization.building_id == building_id)
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def activity_exists(db: Session, activity_id: int) -> bool:
        """
            Проверяет существование вида деятельности

            Args:
                db: SQLAlchemy-сессия
                activity_id: ID активности

            Returns:
                bool: True если существует
           """
        stmt = select(Activity.id).where(Activity.id == activity_id)
        return db.execute(stmt).scalar_one_or_none() is not None

    @staticmethod
    def activity_descendants_ids(db: Session, root_activity_id: int) -> list[int]:
        """
            Возвращает список ID активности и её дочерних до глубины 3

            Args:
                db: SQLAlchemy-сессия
                root_activity_id: ID корневой активности

            Returns:
                list[int]: ID всех найденных активностей
        """
        sql = text(
            """
            WITH RECURSIVE tree AS (
                SELECT id, parent_id, 1 AS depth
                FROM activities
                WHERE id = :root_id
                UNION ALL
                SELECT a.id, a.parent_id, t.depth + 1
                FROM activities a
                JOIN tree t ON a.parent_id = t.id
                WHERE t.depth < 3
            )
            SELECT id FROM tree;
            """
        )
        rows = db.execute(sql, {"root_id": root_activity_id}).all()
        return [int(r[0]) for r in rows]

    @staticmethod
    def orgs_by_activity_ids(db: Session, activity_ids: list[int]) -> list[Organization]:
        """
            Возвращает организации, связанные с заданными ID активностей

            Args:
                db: SQLAlchemy-сессия
                activity_ids: Список ID активностей

            Returns:
                list[Organization]: Список организаций
        """
        if not activity_ids:
            return []
        stmt = (
            select(Organization)
            .join(Organization.activities)
            .where(Activity.id.in_(activity_ids))
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
            .distinct()
        )
        return list(db.execute(stmt).scalars().all())


class BuildingsRepository:
    """Репозиторий для работы со зданиями"""
    @staticmethod
    def buildings_in_bbox(db: Session, bbox: BBox) -> list[Building]:
        """
            Возвращает здания внутри заданного прямоугольника

            Args:
                db: SQLAlchemy-сессия
                bbox: Объект с координатными границами

            Returns:
                list[Building]: Здания внутри прямоугольника
        """
        stmt = select(Building).where(
            Building.lat.between(bbox.lat_min, bbox.lat_max),
            Building.lon.between(bbox.lon_min, bbox.lon_max),
        )
        return list(db.execute(stmt).scalars().all())