from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Organization
from app.schemas import OrganizationOut

router = APIRouter()


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
