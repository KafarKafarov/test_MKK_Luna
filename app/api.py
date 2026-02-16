import math

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import get_db
from app.models import Activity, Building, Organization
from app.schemas import BuildingOut, GeoSearchOut, OrganizationOut

router = APIRouter()


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


router.dependencies.append(Depends(require_api_key))


@router.get("/organizations/search", response_model=list[OrganizationOut])
def search_organizations(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> list[OrganizationOut]:
    orgs = db.query(Organization).filter(Organization.name.ilike(f"%{q}%")).all()

    return [
        OrganizationOut.model_validate(
            {
                "id": o.id,
                "name": o.name,
                "building": o.building,
                "phones": [p.phone for p in o.phones],
            },
            from_attributes=True,
        )
        for o in orgs
    ]


def org_to_out(o: Organization) -> OrganizationOut:
    return OrganizationOut.model_validate(
        {
            "id": o.id,
            "name": o.name,
            "building": o.building,
            "phones": [p.phone for p in o.phones],
            "activities": [a.name for a in o.activities],
        },
        from_attributes=True,
    )


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: int, db: Session = Depends(get_db)) -> OrganizationOut:
    stmt = (
        select(Organization)
        .where(Organization.id == org_id)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.phones),
            selectinload(Organization.activities),
        )
    )
    org = db.execute(stmt).scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org_to_out(org)


@router.get("/buildings/{building_id}/organizations", response_model=list[OrganizationOut])
def organizations_in_building(
    building_id: int,
    db: Session = Depends(get_db),
) -> list[OrganizationOut]:
    stmt = (
        select(Organization)
        .where(Organization.building_id == building_id)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.phones),
            selectinload(Organization.activities),
        )
    )
    orgs = db.execute(stmt).scalars().all()
    return [org_to_out(o) for o in orgs]


def activity_descendants_ids(db: Session, activity_id: int) -> list[int]:
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
    rows = db.execute(sql, {"root_id": activity_id}).all()
    return [int(r[0]) for r in rows]


@router.get("/activities/{activity_id}/organizations", response_model=list[OrganizationOut])
def organizations_by_activity(
    activity_id: int,
    db: Session = Depends(get_db),
) -> list[OrganizationOut]:
    exists = db.execute(select(Activity.id).where(Activity.id == activity_id)).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    ids = activity_descendants_ids(db, activity_id)

    stmt = (
        select(Organization)
        .join(Organization.activities)
        .where(Activity.id.in_(ids))
        .options(
            selectinload(Organization.building),
            selectinload(Organization.phones),
            selectinload(Organization.activities),
        )
        .distinct()
    )
    orgs = db.execute(stmt).scalars().all()
    return [org_to_out(o) for o in orgs]


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@router.get("/geo/radius", response_model=GeoSearchOut)
def geo_radius(
    lat: float,
    lon: float,
    r_m: float = Query(gt=0),
    db: Session = Depends(get_db),
) -> GeoSearchOut:
    lat_delta = r_m / 111_000.0
    lon_delta = r_m / (111_000.0 * max(0.1, math.cos(math.radians(lat))))

    lat_min, lat_max = lat - lat_delta, lat + lat_delta
    lon_min, lon_max = lon - lon_delta, lon + lon_delta

    buildings = (
        db.execute(
            select(Building).where(
                Building.lat.between(lat_min, lat_max),
                Building.lon.between(lon_min, lon_max),
            )
        )
        .scalars()
        .all()
    )

    near_buildings = [b for b in buildings if haversine_m(lat, lon, b.lat, b.lon) <= r_m]
    if not near_buildings:
        return GeoSearchOut(organizations=[], buildings=[])

    b_ids = [b.id for b in near_buildings]
    orgs = (
        db.execute(
            select(Organization)
            .where(Organization.building_id.in_(b_ids))
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
        )
        .scalars()
        .all()
    )

    return GeoSearchOut(
        organizations=[org_to_out(o) for o in orgs],
        buildings=[BuildingOut.model_validate(b, from_attributes=True) for b in near_buildings],
    )


@router.get("/geo/rectangle", response_model=GeoSearchOut)
def geo_rectangle(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    db: Session = Depends(get_db),
) -> GeoSearchOut:
    lat_min, lat_max = sorted([lat1, lat2])
    lon_min, lon_max = sorted([lon1, lon2])

    buildings = (
        db.execute(
            select(Building).where(
                Building.lat.between(lat_min, lat_max),
                Building.lon.between(lon_min, lon_max),
            )
        )
        .scalars()
        .all()
    )

    if not buildings:
        return GeoSearchOut(organizations=[], buildings=[])

    b_ids = [b.id for b in buildings]
    orgs = (
        db.execute(
            select(Organization)
            .where(Organization.building_id.in_(b_ids))
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
        )
        .scalars()
        .all()
    )

    return GeoSearchOut(
        organizations=[org_to_out(o) for o in orgs],
        buildings=[BuildingOut.model_validate(b, from_attributes=True) for b in buildings],
    )
