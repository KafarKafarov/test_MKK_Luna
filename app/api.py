"""HTTP-слой: маршруты FastAPI, авторизация по статическому API-key и
связывание зависимостей"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.repositories import BuildingsRepository, OrgsRepository
from app.schemas import GeoSearchOut, OrganizationOut
from app.services import OrgsService

router = APIRouter()


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """
        Проверяет API ключ для авторизации

        Args:
            x_api_key: Значение X-API-Key

        Raises:
            HTTPException: 401, если ключ отсутствует или неверен
    """
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


router.dependencies.append(Depends(require_api_key))


def get_service() -> OrgsService:
    """
       Экземпляр сервисного слоя для обработки запросов

       Returns:
           OrgsService: Сервис для операций с организациями/зданиями/геопоиском
    """
    return OrgsService(orgs=OrgsRepository(), buildings=BuildingsRepository())

@router.get(
    "/organizations/search",
    response_model=list[OrganizationOut],
    tags=["Organizations"],
    summary="Search organizations",
)
def search_organizations(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> list[OrganizationOut]:
    """
       Ищет организации по подстроке в названии

       Args:
           q: Поисковая строка
           db: SQLAlchemy-сессия
           svc: Сервисный слой

       Returns:
           list[OrganizationOut]: Список найденных организаций

       Raises:
           HTTPException: 401, если не пройдена проверка API key
    """
    return svc.search_by_name(db, q)


@router.get(
    "/organizations/{org_id}",
    response_model=OrganizationOut,
    tags=["Organizations"],
    summary="Get organization by id",
)
def get_organization(
        org_id: int,
        db: Session = Depends(get_db),
        svc: OrgsService = Depends(get_service),
) -> OrganizationOut:
    """
       Возвращает организацию по её идентификатору.
       Если организация не найдена - сервис выбрасывает 404 ошибку

       Args:
           org_id: Идентификатор организации
           db: SQLAlchemy-сессия
           svc: Сервисный слой

       Returns:
           OrganizationOut: Организация с вложенным зданием и списками телефонов/активностей.

       Raises:
           HTTPException: 401, если не пройдена проверка API key
           HTTPException: 404, если организация не найдена
    """
    return svc.get_organization(db, org_id)


@router.get(
    "/buildings/{building_id}/organizations",
    response_model=list[OrganizationOut],
    tags=["Buildings"],
    summary="List organizations in building",
)
def organizations_in_building(
    building_id: int,
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> list[OrganizationOut]:
    """
        Возвращает список организаций, находящихся в указанном здании

        Args:
            building_id: Идентификатор здания
            db: SQLAlchemy-сессия
            svc: Сервисный слой

        Returns:
            list[OrganizationOut]: Организации, привязанные к зданию

        Raises:
            HTTPException: 401, если не пройдена проверка API key
    """
    return svc.organizations_in_building(db, building_id)


@router.get(
    "/activities/{activity_id}/organizations",
    response_model=list[OrganizationOut],
    tags=["Activities"],
    summary="List organizations by activity (depth ≤ 3)",
)
def organizations_by_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> list[OrganizationOut]:
    """
        Возвращает организации по виду деятельности, включая дочерние активности до глубины 3

        Args:
            activity_id: Идентификатор корневой активности
            db: SQLAlchemy-сессия
            svc: Сервисный слой

        Returns:
            list[OrganizationOut]: Организации, относящиеся к activity_id и её потомкам (до depth=3)

        Raises:
            HTTPException: 401, если не пройдена проверка API key
            HTTPException: 404, если активность не найдена
    """
    return svc.organizations_by_activity(db, activity_id)


@router.get(
    "/geo/radius",
    response_model=GeoSearchOut,
    tags=["Geo"],
    summary="Geo search by radius",
)
def geo_radius(
    lat: float,
    lon: float,
    r_m: float = Query(gt=0),
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> GeoSearchOut:
    """
        Геопоиск по радиусу: здания и организации в пределах заданного расстояния

        Args:
            lat: Широта центра поиска
            lon: Долгота центра поиска
            r_m: Радиус в метрах
            db: SQLAlchemy-сессия
            svc: Сервисный слой

        Returns:
            GeoSearchOut: Списки зданий и организаций в радиусе

        Raises:
            HTTPException: 401, если не пройдена проверка API key
    """
    return svc.geo_radius(db, lat, lon, r_m)


@router.get(
    "/geo/rectangle",
    response_model=GeoSearchOut,
    tags=["Geo"],
    summary="Geo search by rectangle",
)
def geo_rectangle(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    db: Session = Depends(get_db),
    svc: OrgsService = Depends(get_service),
) -> GeoSearchOut:
    """
        Геопоиск по прямоугольнику: здания и организации внутри заданного bbox

        Args:
            lat1: Широта первой точки
            lon1: Долгота первой точки
            lat2: Широта второй точки
            lon2: Долгота второй точки
            db: SQLAlchemy-сессия
            svc: Сервисный слой

        Returns:
            GeoSearchOut: Списки зданий и организаций в прямоугольнике

        Raises:
            HTTPException: 401, если не пройдена проверка API key
    """
    return svc.geo_rectangle(db, lat1, lon1, lat2, lon2)
