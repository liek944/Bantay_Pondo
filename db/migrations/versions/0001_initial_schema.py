"""Initial schema: administrative boundaries, hazards, projects, contractors, metrics.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-20 17:50:00.000000

"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all core Bantay Pondo tables, types, and spatial indexes."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # Ensure required PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # Hazard type enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'hazard_type_enum') THEN
                CREATE TYPE hazard_type_enum AS ENUM ('flood', 'landslide', 'storm_surge');
            END IF;
        END $$;
    """)

    # 1. regions
    if "regions" not in existing_tables:
        op.create_table(
            "regions",
            sa.Column("psgc_code", sa.String(length=10), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("parent_psgc", sa.String(length=10), nullable=True),
            sa.Column("land_area_sqkm", sa.Float(), nullable=True),
            sa.Column("population", sa.BigInteger(), nullable=True),
            sa.Column("population_year", sa.Integer(), nullable=True),
            sa.Column(
                "geom",
                geoalchemy2.types.Geometry(
                    geometry_type="MULTIPOLYGON",
                    srid=4326,
                    spatial_index=False,
                    from_text="ST_GeomFromEWKT",
                    name="geometry",
                ),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("psgc_code", name="pk_regions"),
        )
        op.create_index(
            "idx_regions_geom",
            "regions",
            ["geom"],
            unique=False,
            postgresql_using="gist",
        )

    # 2. provinces
    if "provinces" not in existing_tables:
        op.create_table(
            "provinces",
            sa.Column("psgc_code", sa.String(length=10), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("parent_psgc", sa.String(length=10), nullable=True),
            sa.Column("land_area_sqkm", sa.Float(), nullable=True),
            sa.Column("population", sa.BigInteger(), nullable=True),
            sa.Column("population_year", sa.Integer(), nullable=True),
            sa.Column(
                "geom",
                geoalchemy2.types.Geometry(
                    geometry_type="MULTIPOLYGON",
                    srid=4326,
                    spatial_index=False,
                    from_text="ST_GeomFromEWKT",
                    name="geometry",
                ),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["parent_psgc"],
                ["regions.psgc_code"],
                name="fk_provinces_regions",
            ),
            sa.PrimaryKeyConstraint("psgc_code", name="pk_provinces"),
        )
        op.create_index(
            "idx_provinces_geom",
            "provinces",
            ["geom"],
            unique=False,
            postgresql_using="gist",
        )
        op.create_index(
            "idx_provinces_parent_psgc",
            "provinces",
            ["parent_psgc"],
            unique=False,
        )

    # 3. municipalities
    if "municipalities" not in existing_tables:
        op.create_table(
            "municipalities",
            sa.Column("psgc_code", sa.String(length=10), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("parent_psgc", sa.String(length=10), nullable=True),
            sa.Column("land_area_sqkm", sa.Float(), nullable=True),
            sa.Column("population", sa.BigInteger(), nullable=True),
            sa.Column("population_year", sa.Integer(), nullable=True),
            sa.Column(
                "geom",
                geoalchemy2.types.Geometry(
                    geometry_type="MULTIPOLYGON",
                    srid=4326,
                    spatial_index=False,
                    from_text="ST_GeomFromEWKT",
                    name="geometry",
                ),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("psgc_code", name="pk_municipalities"),
        )
        op.create_index(
            "idx_municipalities_geom",
            "municipalities",
            ["geom"],
            unique=False,
            postgresql_using="gist",
        )
        op.create_index(
            "idx_municipalities_parent_psgc",
            "municipalities",
            ["parent_psgc"],
            unique=False,
        )

    # 4. barangays
    if "barangays" not in existing_tables:
        op.create_table(
            "barangays",
            sa.Column("psgc_code", sa.String(length=10), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("parent_psgc", sa.String(length=10), nullable=True),
            sa.Column("land_area_sqkm", sa.Float(), nullable=True),
            sa.Column("population", sa.BigInteger(), nullable=True),
            sa.Column("population_year", sa.Integer(), nullable=True),
            sa.Column(
                "geom",
                geoalchemy2.types.Geometry(
                    geometry_type="MULTIPOLYGON",
                    srid=4326,
                    spatial_index=False,
                    from_text="ST_GeomFromEWKT",
                    name="geometry",
                ),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("psgc_code", name="pk_barangays"),
        )
        op.create_index(
            "idx_barangays_geom",
            "barangays",
            ["geom"],
            unique=False,
            postgresql_using="gist",
        )
        op.create_index(
            "idx_barangays_parent_psgc",
            "barangays",
            ["parent_psgc"],
            unique=False,
        )

    # 5. hazard_zones
    if "hazard_zones" not in existing_tables:
        op.create_table(
            "hazard_zones",
            sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column(
                "hazard_type",
                postgresql.ENUM("flood", "landslide", "storm_surge", name="hazard_type_enum"),
                nullable=False,
            ),
            sa.Column("severity_level", sa.Integer(), nullable=False),
            sa.Column(
                "geom",
                geoalchemy2.types.Geometry(
                    geometry_type="MULTIPOLYGON",
                    srid=4326,
                    spatial_index=False,
                    from_text="ST_GeomFromEWKT",
                    name="geometry",
                ),
                nullable=False,
            ),
            sa.Column("source_dataset", sa.String(length=255), nullable=True),
            sa.Column("source_year", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id", name="pk_hazard_zones"),
        )
        op.create_index(
            "idx_hazard_zones_geom",
            "hazard_zones",
            ["geom"],
            unique=False,
            postgresql_using="gist",
        )
        op.create_index(
            "idx_hazard_zones_type_severity",
            "hazard_zones",
            ["hazard_type", "severity_level"],
            unique=False,
        )

    # 6. contractors
    if "contractors" not in existing_tables:
        op.create_table(
            "contractors",
            sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column("normalized_name", sa.String(length=255), nullable=False),
            sa.Column("raw_names", postgresql.ARRAY(sa.Text()), nullable=False),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("first_seen", sa.Date(), nullable=True),
            sa.Column("total_contracts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_value_php", sa.Numeric(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id", name="pk_contractors"),
            sa.UniqueConstraint("normalized_name", name="uq_contractors_normalized_name"),
        )
        op.create_index(
            "idx_contractors_normalized_name_trgm",
            "contractors",
            ["normalized_name"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"normalized_name": "gin_trgm_ops"},
        )

    # 7. projects
    if "projects" not in existing_tables:
        op.create_table(
            "projects",
            sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column("contract_id", sa.String(length=255), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("implementing_office", sa.String(length=255), nullable=True),
            sa.Column("contractor_id", sa.BigInteger(), nullable=True),
            sa.Column("funding_source", sa.String(length=255), nullable=True),
            sa.Column("budget_php", sa.Numeric(), nullable=True),
            sa.Column("contract_cost_php", sa.Numeric(), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("target_completion_date", sa.Date(), nullable=True),
            sa.Column("physical_progress_pct", sa.Numeric(), nullable=True),
            sa.Column(
                "geom",
                geoalchemy2.types.Geometry(
                    geometry_type="POINT",
                    srid=4326,
                    spatial_index=False,
                    from_text="ST_GeomFromEWKT",
                    name="geometry",
                ),
                nullable=True,
            ),
            sa.Column("psgc_code", sa.String(length=10), nullable=True),
            sa.Column("source_row_hash", sa.String(length=255), nullable=True),
            sa.Column(
                "ingested_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["contractor_id"],
                ["contractors.id"],
                name="fk_projects_contractors",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_projects"),
            sa.UniqueConstraint("contract_id", name="uq_projects_contract_id"),
        )
        op.create_index(
            "idx_projects_geom",
            "projects",
            ["geom"],
            unique=False,
            postgresql_using="gist",
        )
        op.create_index(
            "idx_projects_ingested_at",
            "projects",
            ["ingested_at"],
            unique=False,
            postgresql_using="brin",
        )
        op.create_index(
            "idx_projects_psgc_code",
            "projects",
            ["psgc_code"],
            unique=False,
        )
        op.create_index(
            "idx_projects_contractor_id",
            "projects",
            ["contractor_id"],
            unique=False,
        )

    # 8. procurement_awards
    if "procurement_awards" not in existing_tables:
        op.create_table(
            "procurement_awards",
            sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column("reference_id", sa.String(length=255), nullable=True),
            sa.Column("contractor_id", sa.BigInteger(), nullable=True),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("award_amount_php", sa.Numeric(), nullable=True),
            sa.Column("award_date", sa.Date(), nullable=True),
            sa.Column("procuring_entity", sa.String(length=255), nullable=True),
            sa.Column("psgc_code", sa.String(length=10), nullable=True),
            sa.ForeignKeyConstraint(
                ["contractor_id"],
                ["contractors.id"],
                name="fk_procurement_awards_contractors",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_procurement_awards"),
        )
        op.create_index(
            "idx_procurement_awards_contractor_id",
            "procurement_awards",
            ["contractor_id"],
            unique=False,
        )
        op.create_index(
            "idx_procurement_awards_psgc_code",
            "procurement_awards",
            ["psgc_code"],
            unique=False,
        )

    # 9. officials
    if "officials" not in existing_tables:
        op.create_table(
            "officials",
            sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("position", sa.String(length=255), nullable=False),
            sa.Column("psgc_code", sa.String(length=10), nullable=True),
            sa.Column("district", sa.String(length=255), nullable=True),
            sa.Column("term_start", sa.Date(), nullable=True),
            sa.Column("term_end", sa.Date(), nullable=True),
            sa.Column("party", sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint("id", name="pk_officials"),
        )
        op.create_index(
            "idx_officials_psgc_code",
            "officials",
            ["psgc_code"],
            unique=False,
        )

    # 10. locality_metrics
    if "locality_metrics" not in existing_tables:
        op.create_table(
            "locality_metrics",
            sa.Column("psgc_code", sa.String(length=10), nullable=False),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("hazard_exposure_pct", sa.Numeric(), nullable=False),
            sa.Column("flood_pct", sa.Numeric(), nullable=False),
            sa.Column("landslide_pct", sa.Numeric(), nullable=False),
            sa.Column("surge_pct", sa.Numeric(), nullable=False),
            sa.Column("population_at_risk", sa.BigInteger(), nullable=False),
            sa.Column("total_spend_php", sa.Numeric(), nullable=False),
            sa.Column("spend_per_capita", sa.Numeric(), nullable=False),
            sa.Column("spend_per_exposed_sqkm", sa.Numeric(), nullable=False),
            sa.Column("raw_ratio", sa.Numeric(), nullable=False),
            sa.Column("mismatch_score", sa.Numeric(), nullable=False),
            sa.Column("national_percentile", sa.Numeric(), nullable=False),
            sa.Column(
                "computed_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("psgc_code", "year", name="pk_locality_metrics"),
        )
        op.create_index(
            "idx_locality_metrics_psgc_year",
            "locality_metrics",
            ["psgc_code", "year"],
            unique=False,
        )
        op.create_index(
            "idx_locality_metrics_mismatch",
            "locality_metrics",
            ["mismatch_score"],
            unique=False,
        )

    # 11. project_reviews
    if "project_reviews" not in existing_tables:
        op.create_table(
            "project_reviews",
            sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column("contract_id", sa.String(length=255), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=False),
            sa.Column("latitude", sa.Numeric(), nullable=True),
            sa.Column("longitude", sa.Numeric(), nullable=True),
            sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id", name="pk_project_reviews"),
        )

    # 12. rejects
    if "rejects" not in existing_tables:
        op.create_table(
            "rejects",
            sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column("source_dataset", sa.String(length=255), nullable=False),
            sa.Column("raw_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("failure_reason", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id", name="pk_rejects"),
        )

    # 13. data_versions
    if "data_versions" not in existing_tables:
        op.create_table(
            "data_versions",
            sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
            sa.Column("version_tag", sa.String(length=50), nullable=False),
            sa.Column(
                "published_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("row_counts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
            sa.PrimaryKeyConstraint("id", name="pk_data_versions"),
            sa.UniqueConstraint("version_tag", name="uq_data_versions_version_tag"),
        )


def downgrade() -> None:
    """Drop all created tables, indexes, and custom types."""
    op.drop_table("data_versions")
    op.drop_table("rejects")
    op.drop_table("project_reviews")
    op.drop_table("locality_metrics")
    op.drop_table("officials")
    op.drop_table("procurement_awards")
    op.drop_table("projects")
    op.drop_table("contractors")
    op.drop_table("hazard_zones")
    op.drop_table("barangays")
    op.drop_table("municipalities")
    op.drop_table("provinces")
    op.drop_table("regions")

    op.execute("DROP TYPE IF EXISTS hazard_type_enum;")
