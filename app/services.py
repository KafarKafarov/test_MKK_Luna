from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.geo import bbox_for_radius, bbox_for_rectangle, haversine_m
from app.models import Organization
from app.repositories import BuildingsRepository, OrgsRepository
from app.schemas import BuildingOut, GeoSearchOut, OrganizationOut


def org_to_out(o: Organization) -> OrganizationOut:  return OrganizationOut.model_validate(
        {
            "id": o.id,
            "name": o.name,
            "building": o.building, "phones": [p.phone for p in o.phones],
            "activities": [a.name for a in o.activities],
        },
        from_attributes=True,
    )


class OrgsService:
    def __init__(
            self,
            orgs: OrgsRepository,
            buildings: BuildingsRepository,
    ) -> None:
        self.orgs = orgs
        self.buildings = buildings

    def get_organization(self, db: Session, org_id: int) -> OrganizationOut:
        org = self.orgs.get_org_by_id(db, org_id)
        if org is None:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org_to_out(org)

    def search_by_name(self, db: Session, q: str) -> list[OrganizationOut]:
        return [org_to_out(o) for o in self.orgs.search_orgs_by_name(db, q)]

    def organizations_in_building(self, db: Session, building_id: int) -> list[OrganizationOut]:
        return [org_to_out(o) for o in self.orgs.orgs_in_building(db, building_id)]

    def organizations_by_activity(self, db: Session, activity_id: int) -> list[OrganizationOut]:
        if not self.orgs.activity_exists(db, activity_id):
            raise HTTPException(status_code=404, detail="Activity not found")

        ids = self.orgs.activity_descendants_ids(db, activity_id)
        orgs = self.orgs.orgs_by_activity_ids(db, ids)
        return [org_to_out(o) for o in orgs]

    def geo_radius(self, db: Session, lat: float, lon: float, r_m: float) -> GeoSearchOut:
        bbox = bbox_for_radius(lat, lon, r_m)
        buildings = self.buildings.buildings_in_bbox(db, bbox)
        near = [b for b in buildings if haversine_m(lat, lon, b.lat, b.lon) <= r_m]

        if not near:
            return GeoSearchOut(organizations=[], buildings=[])

        b_ids = {b.id for b in near}
        orgs = []
        for b_id in b_ids:
            orgs.extend(self.orgs.orgs_in_building(db, b_id))

        return GeoSearchOut(
            organizations=[org_to_out(o) for o in orgs],
            buildings=[BuildingOut.model_validate(b, from_attributes=True) for b in near],
        )

    def geo_rectangle(
            self,
            db: Session,
            lat1: float,
            lon1: float,
            lat2: float,
            lon2: float,
    ) -> GeoSearchOut:
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
            buildings=[BuildingOut.model_validate(b, from_attributes=True) for b in buildings],
        )