import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BBox:
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def bbox_for_radius(lat: float, lon: float, radius_m: float) -> BBox:
    lat_delta = radius_m / 111_000.0
    lon_delta = radius_m / (111_000.0 * max(0.1, math.cos(math.radians(lat))))
    return BBox(
        lat_min=lat - lat_delta,
        lat_max=lat + lat_delta,
        lon_min=lon - lon_delta,
        lon_max=lon + lon_delta,
    )


def bbox_for_rectangle(lat1: float, lon1: float, lat2: float, lon2: float) -> BBox:
    lat_min, lat_max = sorted([lat1, lat2])
    lon_min, lon_max = sorted([lon1, lon2])
    return BBox(lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max)