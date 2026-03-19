"""HTTP-слой: маршруты FastAPI, авторизация по статическому API-key и
связывание зависимостей"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.repo.repositories import BuildingsRepository, OrgsRepository
from app.schemas.schemas import GeoSearchOut, OrganizationOut
from app.services.services import OrgsService

router = APIRouter()


def require_api_key(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """
        Проверяет API ключ для авторизации

        Args:
            x_api_key: Значение X-API-Key

        Raises:
            HTTPException: 401, если ключ отсутствует или неверен
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


router.dependencies.append(Depends(require_api_key))


async def get_service() -> OrgsService:
    """
       Экземпляр сервисного слоя для обработки запросов

       Returns:
           OrgsService: Сервис для операций с организациями/зданиями/геопоиском
    """
    return OrgsService(
        orgs=OrgsRepository(),
        buildings=BuildingsRepository(),
    )

@router.get(
    path="/organizations/search",
    response_model=list[OrganizationOut],
    tags=["Organizations"],
    summary="Search organizations",
)
async def search_organizations(
    q: str = Query(min_length=1),
    db: AsyncSession = Depends(dependency=get_db),
    svc: OrgsService = Depends(dependency=get_service),
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
    return await svc.search_by_name(db=db, q=q)


@router.get(
    path="/organizations/{org_id}",
    response_model=OrganizationOut,
    tags=["Organizations"],
    summary="Get organization by id",
)
async def get_organization(
        org_id: int,
        db: AsyncSession = Depends(dependency=get_db),
        svc: OrgsService = Depends(dependency=get_service),
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
    return await svc.get_organization(db=db, org_id=org_id)


@router.get(
    path="/buildings/{building_id}/organizations",
    response_model=list[OrganizationOut],
    tags=["Buildings"],
    summary="List organizations in building",
)
async def organizations_in_building(
    building_id: int,
    db: AsyncSession = Depends(dependency=get_db),
    svc: OrgsService = Depends(dependency=get_service),
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
    return await svc.organizations_in_building(
        db=db,
        building_id=building_id,
    )


@router.get(
    path="/activities/{activity_id}/organizations",
    response_model=list[OrganizationOut],
    tags=["Activities"],
    summary="List organizations by activity (depth ≤ 3)",
)
async def organizations_by_activity(
    activity_id: int,
    db: AsyncSession = Depends(dependency=get_db),
    svc: OrgsService = Depends(dependency=get_service),
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
    return await svc.organizations_by_activity(
        db=db,
        activity_id=activity_id,
    )


@router.get(
    path="/geo/radius",
    response_model=GeoSearchOut,
    tags=["Geo"],
    summary="Geo search by radius",
)
async def geo_radius(
    lat: float,
    lon: float,
    r_m: float = Query(gt=0),
    db: AsyncSession = Depends(dependency=get_db),
    svc: OrgsService = Depends(dependency=get_service),
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
    return await svc.geo_radius(
        db=db,
        lat=lat,
        lon=lon,
        r_m=r_m,
    )


@router.get(
    path="/geo/rectangle",
    response_model=GeoSearchOut,
    tags=["Geo"],
    summary="Geo search by rectangle",
)
async def geo_rectangle(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    db: AsyncSession = Depends(dependency=get_db),
    svc: OrgsService = Depends(dependency=get_service),
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
    return await svc.geo_rectangle(
        db=db,
        lat1=lat1,
        lon1=lon1,
        lat2=lat2,
        lon2=lon2,
    )
