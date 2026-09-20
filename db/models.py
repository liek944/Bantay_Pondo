"""SQLAlchemy declarative models for Bantay Pondo."""

import datetime
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


hazard_type_enum = ENUM(
    "flood",
    "landslide",
    "storm_surge",
    name="hazard_type_enum",
    create_type=False,
)


class Region(Base):
    """PSGC Region administrative boundary."""

    __tablename__ = "regions"

    psgc_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_psgc: Mapped[str | None] = mapped_column(String(10), nullable=True)
    land_area_sqkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    population: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    population_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_regions_geom", "geom", postgresql_using="gist"),
    )


class Province(Base):
    """PSGC Province administrative boundary."""

    __tablename__ = "provinces"

    psgc_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_psgc: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("regions.psgc_code", name="fk_provinces_regions"),
        nullable=True,
    )
    land_area_sqkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    population: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    population_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_provinces_geom", "geom", postgresql_using="gist"),
        Index("idx_provinces_parent_psgc", "parent_psgc"),
    )


class Municipality(Base):
    """PSGC Municipality / City administrative boundary."""

    __tablename__ = "municipalities"

    psgc_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_psgc: Mapped[str | None] = mapped_column(String(10), nullable=True)
    land_area_sqkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    population: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    population_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_municipalities_geom", "geom", postgresql_using="gist"),
        Index("idx_municipalities_parent_psgc", "parent_psgc"),
    )


class Barangay(Base):
    """PSGC Barangay administrative boundary."""

    __tablename__ = "barangays"

    psgc_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_psgc: Mapped[str | None] = mapped_column(String(10), nullable=True)
    land_area_sqkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    population: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    population_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_barangays_geom", "geom", postgresql_using="gist"),
        Index("idx_barangays_parent_psgc", "parent_psgc"),
    )


class HazardZone(Base):
    """Project NOAH disaster hazard zones (flood, landslide, storm surge)."""

    __tablename__ = "hazard_zones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hazard_type: Mapped[str] = mapped_column(hazard_type_enum, nullable=False)
    severity_level: Mapped[int] = mapped_column(Integer, nullable=False)
    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    )
    source_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_hazard_zones_geom", "geom", postgresql_using="gist"),
        Index("idx_hazard_zones_type_severity", "hazard_type", "severity_level"),
    )


class Contractor(Base):
    """Deduplicated contractor entity preserving raw aliases."""

    __tablename__ = "contractors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    normalized_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    raw_names: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    total_contracts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_value_php: Mapped[Decimal] = mapped_column(Numeric, default=Decimal(0), nullable=False)

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="contractor")
    procurement_awards: Mapped[list["ProcurementAward"]] = relationship(
        "ProcurementAward", back_populates="contractor"
    )

    __table_args__ = (
        Index(
            "idx_contractors_normalized_name_trgm",
            "normalized_name",
            postgresql_using="gin",
            postgresql_ops={"normalized_name": "gin_trgm_ops"},
        ),
    )


class Project(Base):
    """DPWH infrastructure project entity with spatial join to barangays."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementing_office: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contractor_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("contractors.id", name="fk_projects_contractors"),
        nullable=True,
    )
    funding_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget_php: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    contract_cost_php: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    start_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    target_completion_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    physical_progress_pct: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    geom: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )
    psgc_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    source_row_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    contractor: Mapped[Contractor | None] = relationship("Contractor", back_populates="projects")

    __table_args__ = (
        Index("idx_projects_geom", "geom", postgresql_using="gist"),
        Index("idx_projects_ingested_at", "ingested_at", postgresql_using="brin"),
        Index("idx_projects_psgc_code", "psgc_code"),
        Index("idx_projects_contractor_id", "contractor_id"),
    )


class ProcurementAward(Base):
    """PhilGEPS procurement award entity."""

    __tablename__ = "procurement_awards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contractor_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("contractors.id", name="fk_procurement_awards_contractors"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    award_amount_php: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    award_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    procuring_entity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    psgc_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    contractor: Mapped[Contractor | None] = relationship(
        "Contractor", back_populates="procurement_awards"
    )

    __table_args__ = (
        Index("idx_procurement_awards_contractor_id", "contractor_id"),
        Index("idx_procurement_awards_psgc_code", "psgc_code"),
    )


class Official(Base):
    """Elected or public official entity."""

    __tablename__ = "officials"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    psgc_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    term_start: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    term_end: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    party: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_officials_psgc_code", "psgc_code"),
    )


class LocalityMetrics(Base):
    """Materialized mismatch score and risk metrics per locality and year."""

    __tablename__ = "locality_metrics"

    psgc_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    hazard_exposure_pct: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    flood_pct: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    landslide_pct: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    surge_pct: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    population_at_risk: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_spend_php: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    spend_per_capita: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    spend_per_exposed_sqkm: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    raw_ratio: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    mismatch_score: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    national_percentile: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    computed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_locality_metrics_psgc_year", "psgc_code", "year"),
        Index("idx_locality_metrics_mismatch", "mismatch_score"),
    )


class ProjectReview(Base):
    """Review queue for projects failing spatial join or lacking valid coordinates."""

    __tablename__ = "project_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Reject(Base):
    """Quarantine table for malformed rows during ingestion."""

    __tablename__ = "rejects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_dataset: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_row: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    failure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class DataVersion(Base):
    """Metadata tracking dataset versions and refresh timestamps."""

    __tablename__ = "data_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_tag: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    published_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    row_counts: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
