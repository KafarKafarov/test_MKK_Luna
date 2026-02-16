from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.geo import BBox
from app.models import Activity, Building, Organization


class OrgsRepository:
    @staticmethod
    def get_org_by_id(db: Session, org_id: int) -> Organization | None:
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
        stmt = select(Activity.id).where(Activity.id == activity_id)
        return db.execute(stmt).scalar_one_or_none() is not None

    @staticmethod
    def activity_descendants_ids(db: Session, root_activity_id: int) -> list[int]:
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
    @staticmethod
    def buildings_in_bbox(db: Session, bbox: BBox) -> list[Building]:
        stmt = select(Building).where(
            Building.lat.between(bbox.lat_min, bbox.lat_max),
            Building.lon.between(bbox.lon_min, bbox.lon_max),
        )
        return list(db.execute(stmt).scalars().all())