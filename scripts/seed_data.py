"""Заполнение БД тестовыми данными"""
import asyncio

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal
from app.models.models import (
    Activity,
    Building,
    Organization,
    OrganizationPhone,
)


async def _clear_tables(db: AsyncSession) -> None:
    """Очищает таблицы с учетом FK"""
    await db.execute(
        statement=text(
            """
        TRUNCATE TABLE
            organization_activities,
            organization_phones,
            organizations,
            activities,
            buildings
        RESTART IDENTITY CASCADE
        """
        ),
    )
    await db.commit()


async def _is_seeded(db: AsyncSession) -> bool:
    """Проверяет, есть ли уже данные в базе."""
    result = await db.execute(select(func.count(Building.id)))
    return int(result.scalar_one()) > 0


async def seed_data(*, reset: bool = True) -> None:
    """Заполняет БД тестовыми данными

    Args:
        reset: если True, очищает таблицы перед заполнением.
    """
    async with SessionLocal() as db:
        try:
            if reset:
                await _clear_tables(db)
            elif await _is_seeded(db):
                print("Database already contains data. Skip seeding.")
                return

            buildings = [
                Building(address="г. Москва, ул. Ленина, 1, офис 3", lat=55.755864, lon=37.617698),
                Building(address="г. Москва, ул. Тверская, 18к1", lat=55.765919, lon=37.604187),
                Building(address="г. Москва, ул. Арбат, 12", lat=55.749579, lon=37.592523),
                Building(address="г. Москва, ул. Профсоюзная, 56", lat=55.670005, lon=37.552445),
                Building(address="г. Москва, пр-т Мира, 119", lat=55.829796, lon=37.633111),
                Building(address="г. Москва, ул. Вавилова, д. 19", lat=55.700182, lon=37.580158),
            ]
            db.add_all(buildings)
            await db.flush()

            food = Activity(name="Еда")
            meat = Activity(name="Мясная продукция", parent=food)
            milk = Activity(name="Молочная продукция", parent=food)
            cars = Activity(name="Автомобили")
            trucks = Activity(name="Грузовые", parent=cars)
            passenger = Activity(name="Легковые", parent=cars)
            parts = Activity(name="Запчасти", parent=passenger)
            accessories = Activity(name="Аксессуары", parent=passenger)
            bank = Activity(name="Банковские услуги")
            credit = Activity(name="Кредиты", parent=bank)
            deposit = Activity(name="Вклады", parent=bank)
            services = Activity(name="Услуги")
            catering = Activity(name="Доставка еды", parent=services)
            it_services = Activity(name="IT услуги", parent=services)

            activities = [
                food,
                meat,
                milk,
                cars,
                trucks,
                passenger,
                parts,
                accessories,
                services,
                catering,
                it_services,
                bank,
                credit,
                deposit,
            ]
            db.add_all(activities)
            await db.flush()

            organizations = [
                Organization(
                    name='ООО Рога и Копыта',
                    building=buildings[0],
                    phones=[
                        OrganizationPhone(phone="2-222-222"),
                        OrganizationPhone(phone="8-923-666-13-13"),
                    ],
                    activities=[meat, milk],
                ),
                Organization(
                    name='ООО Молочный мир',
                    building=buildings[1],
                    phones=[OrganizationPhone(phone="3-333-333")],
                    activities=[milk, food],
                ),
                Organization(
                    name='ООО Фура Сервис',
                    building=buildings[3],
                    phones=[
                        OrganizationPhone(phone="8-495-120-45-67"),
                        OrganizationPhone(phone="8-800-700-11-22"),
                    ],
                    activities=[trucks, parts],
                ),
                Organization(
                    name='ООО АвтоЛюкс',
                    building=buildings[2],
                    phones=[OrganizationPhone(phone="8-499-555-00-77")],
                    activities=[passenger, accessories],
                ),
                Organization(
                    name='ООО Арбат Доставка',
                    building=buildings[2],
                    phones=[OrganizationPhone(phone="8-495-600-12-12")],
                    activities=[catering, food],
                ),
                Organization(
                    name='ООО Код и кофе',
                    building=buildings[4],
                    phones=[OrganizationPhone(phone="8-901-123-45-67")],
                    activities=[it_services, services],
                ),
                Organization(
                    name='ООО ВДНХ Фудкорт',
                    building=buildings[4],
                    phones=[
                        OrganizationPhone(phone="8-903-222-33-44"),
                        OrganizationPhone(phone="8-903-222-33-45"),
                    ],
                    activities=[food, meat, milk],
                ),
                Organization(
                    name='ПАО Сбербанк',
                    building=buildings[5],
                    phones=[
                        OrganizationPhone(phone="8-904-555-00-77"),
                        OrganizationPhone(phone="8-495-555-03-21"),
                    ],
                    activities=[bank, credit, deposit],
                )
            ]
            db.add_all(organizations)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        print("Seed completed successfully.")
        print(f"Buildings: {len(buildings)}")
        print(f"Activities: {len(activities)}")
        print(f"Organizations: {len(organizations)}")


if __name__ == "__main__":
    asyncio.run(seed_data())
