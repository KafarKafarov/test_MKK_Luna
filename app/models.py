"""ORM-модели"""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс декларативных ORM-моделей"""
    pass


class Building(Base):
    """
       Здание(точка на карте + адрес)

       Attributes:
           id: PK
           address: адрес
           lat: Широта
           lon: Долгота
           organizations: Организации, находящиеся в здании
    """
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lon: Mapped[float] = mapped_column(nullable=False)

    organizations: Mapped[list[Organization]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )


class Organization(Base):
    """
        Организация(привязана к зданию)

        Attributes:
            id: PK
            name: Название организации
            building_id: FK на buildings.id
            building: ORM-ссылка на здание
            phones: Телефоны
            activities: Виды деятельности
    """
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id"), nullable=False)
    building: Mapped[Building] = relationship(back_populates="organizations")
    phones: Mapped[list[OrganizationPhone]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list[Activity]] = relationship(
        secondary="organization_activities",
        back_populates="organizations",
    )


class OrganizationPhone(Base):
    """
        Телефон организации

        Attributes:
            id: PK
            organization_id: FK на organizations.id
            phone: Телефонный номер
            organization: ORM-ссылка на организацию
    """
    __tablename__ = "organization_phones"
    __table_args__ = (UniqueConstraint("organization_id", "phone", name="uq_org_phone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    organization: Mapped[Organization] = relationship(back_populates="phones")


class Activity(Base):
    """
        Вид деятельности

        Attributes:
            id: PK
            name: Название вида деятельности
            parent_id: FK на activities.id | None
            parent: ORM-ссылка на родителя
            children: Дочерние активности
            organizations: Организации, у которых есть этот вид деятельности
    """
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id"),
        nullable=True,
    )
    parent: Mapped[Activity | None] = relationship(
        remote_side="Activity.id",
        back_populates="children",
    )
    children: Mapped[list[Activity]] = relationship(back_populates="parent")
    organizations: Mapped[list[Organization]] = relationship(
        secondary="organization_activities",
        back_populates="activities",
    )


class OrganizationActivity(Base):
    """Связующая таблица для связи M:N"""
    __tablename__ = "organization_activities"
    __table_args__ = (UniqueConstraint("organization_id", "activity_id", name="uq_org_activity"),)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        primary_key=True,
    )
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"),
        primary_key=True,
    )
