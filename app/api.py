from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.repositories import BuildingsRepository, OrgsRepository
from app.schemas import GeoSearchOut, OrganizationOut
from app.services import OrgsService

router = APIRouter()


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


router.dependencies.append(Depends(require_api_key))


def get_service() -> OrgsService:
    return OrgsService(orgs=OrgsRepository(), buildings=BuildingsRepository())

@router.get("/organizations/search", response_model=list[OrganizationOut])
def search_organizations(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> list[OrganizationOut]:
    return svc.search_by_name(db, q)


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
def get_organization(
        org_id: int,
        db: Session = Depends(get_db),
        svc: OrgsService = Depends(get_service),
) -> OrganizationOut:
    return svc.get_organization(db, org_id)


@router.get("/buildings/{building_id}/organizations", response_model=list[OrganizationOut])
def organizations_in_building(
    building_id: int,
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> list[OrganizationOut]:
    return svc.organizations_in_building(db, building_id)


@router.get("/activities/{activity_id}/organizations", response_model=list[OrganizationOut])
def organizations_by_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> list[OrganizationOut]:
    return svc.organizations_by_activity(db, activity_id)


@router.get("/geo/radius", response_model=GeoSearchOut)
def geo_radius(
    lat: float,
    lon: float,
    r_m: float = Query(gt=0),
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> GeoSearchOut:
    return svc.geo_radius(db, lat, lon, r_m)


@router.get("/geo/rectangle", response_model=GeoSearchOut)
def geo_rectangle(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> GeoSearchOut:
    return svc.geo_rectangle(db, lat1, lon1, lat2, lon2)
