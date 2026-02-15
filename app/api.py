import math

from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Organization, Activity, Building
from app.schemas import OrganizationOut, GeoSearchOut, BuildingOut
from app.config import settings

router = APIRouter()

def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

router.dependencies.append(Depends(require_api_key))

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
def organizations_in_building(building_id: int, db: Session = Depends(get_db)) -> list[OrganizationOut]:
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

@router.get("/organizations/search", response_model=list[OrganizationOut])
def search_organizations(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> list[OrganizationOut]:
    orgs = (
        db.query(Organization)
        .filter(Organization.name.ilike(f"%{q}%"))
        .all()
    )

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
