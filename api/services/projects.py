"""Project query and flag evaluation services."""

import datetime
from decimal import Decimal
from typing import Any

from api.schemas.projects import (
    ProcurementAwardSummary,
    ProjectDetailResponse,
    ProjectFlag,
)
from db.session import get_async_db_connection


async def evaluate_project_flags(
    project_data: dict[str, Any],
) -> list[ProjectFlag]:
    """Evaluate rule-based flags for a project (never declarations of fraud/wrongdoing)."""
    flags: list[ProjectFlag] = []

    budget = project_data.get("budget_php")
    cost = project_data.get("contract_cost_php")
    progress = project_data.get("physical_progress_pct")
    target_completion = project_data.get("target_completion_date")
    contractor_id = project_data.get("contractor_id")
    office = project_data.get("implementing_office")
    description = project_data.get("description")
    psgc_code = project_data.get("psgc_code")
    start_date = project_data.get("start_date")
    contract_id = project_data.get("contract_id")

    # Flag 1: contract_cost exceeds budget by more than 15%
    if budget and cost and budget > 0:
        cost_dec = Decimal(str(cost))
        budget_dec = Decimal(str(budget))
        if cost_dec > budget_dec * Decimal("1.15"):
            overrun_pct = round(((cost_dec - budget_dec) / budget_dec) * 100, 2)
            flags.append(
                ProjectFlag(
                    code="COST_OVERRUN_15PCT",
                    message=f"Contract cost exceeds approved budget by {overrun_pct}%",
                    severity="warning",
                    details={
                        "budget_php": str(budget_dec),
                        "contract_cost_php": str(cost_dec),
                        "overrun_pct": float(overrun_pct),
                    },
                )
            )

    # Flag 2: physical_progress below 20% more than 12 months past target completion
    if target_completion and progress is not None:
        prog_dec = Decimal(str(progress))
        today = datetime.date.today()
        one_year_past = target_completion + datetime.timedelta(days=365)
        if today > one_year_past and prog_dec < Decimal("20.0"):
            flags.append(
                ProjectFlag(
                    code="DELAYED_LOW_PROGRESS",
                    message=(
                        f"Physical progress ({prog_dec}%) is below 20% more than "
                        f"12 months past target completion date ({target_completion})"
                    ),
                    severity="critical",
                    details={
                        "target_completion_date": str(target_completion),
                        "physical_progress_pct": float(prog_dec),
                        "days_overdue": (today - target_completion).days,
                    },
                )
            )

    # Database-assisted checks for flags 3, 4, 5
    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            # Flag 3: contractor holds more than 40% of a district's total contract value
            if contractor_id and office:
                await cur.execute(
                    """
                    SELECT
                        COALESCE(SUM(budget_php), 0) AS total_office_value,
                        COALESCE(SUM(CASE WHEN contractor_id = %s THEN budget_php ELSE 0 END), 0)
                            AS contractor_office_value
                    FROM projects
                    WHERE implementing_office = %s
                    """,
                    (contractor_id, office),
                )
                row = await cur.fetchone()
                if row and row[0] and row[0] > 0:
                    total_val = Decimal(str(row[0]))
                    contractor_val = Decimal(str(row[1]))
                    share = contractor_val / total_val
                    if share > Decimal("0.40"):
                        share_pct = round(share * 100, 2)
                        flags.append(
                            ProjectFlag(
                                code="DISTRICT_CONTRACTOR_CONCENTRATION_40PCT",
                                message=(
                                    f"Contractor holds {share_pct}% of total project value "
                                    f"in implementing office '{office}'"
                                ),
                                severity="warning",
                                details={
                                    "implementing_office": office,
                                    "share_pct": float(share_pct),
                                    "contractor_value_php": str(contractor_val),
                                    "total_office_value_php": str(total_val),
                                },
                            )
                        )

            # Flag 4: duplicate project descriptions within the same barangay and year
            if description and psgc_code and start_date:
                year = start_date.year
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM projects
                    WHERE psgc_code = %s
                      AND EXTRACT(YEAR FROM start_date) = %s
                      AND LOWER(TRIM(description)) = LOWER(TRIM(%s))
                      AND contract_id != %s
                    """,
                    (psgc_code, year, description, contract_id),
                )
                dup_row = await cur.fetchone()
                if dup_row and dup_row[0] > 0:
                    dup_count = int(dup_row[0])
                    flags.append(
                        ProjectFlag(
                            code="DUPLICATE_DESCRIPTION_BARANGAY_YEAR",
                            message=(
                                f"Found {dup_count} duplicate project description(s) "
                                f"in the same locality and year ({year})"
                            ),
                            severity="info",
                            details={
                                "duplicate_count": dup_count,
                                "year": year,
                                "psgc_code": psgc_code,
                            },
                        )
                    )

            # Flag 5: project coordinates fall outside its stated region
            stated_region_psgc: str | None = project_data.get("stated_region_psgc")
            has_geom = project_data.get("has_geom") or (
                project_data.get("latitude") is not None
                and project_data.get("longitude") is not None
            )

            if not stated_region_psgc and office:
                # Check if office name matches a region name
                await cur.execute(
                    """
                    SELECT psgc_code FROM regions
                    WHERE %s ILIKE '%%' || name || '%%'
                       OR name ILIKE '%%' || %s || '%%'
                    LIMIT 1;
                    """,
                    (office, office),
                )
                r_match = await cur.fetchone()
                if r_match:
                    stated_region_psgc = str(r_match[0])
                else:
                    # Check if office matches a province name, then get province's region parent
                    await cur.execute(
                        """
                        SELECT parent_psgc FROM provinces
                        WHERE %s ILIKE '%%' || name || '%%'
                        LIMIT 1;
                        """,
                        (office,),
                    )
                    p_match = await cur.fetchone()
                    if p_match and p_match[0]:
                        stated_region_psgc = str(p_match[0])

            if stated_region_psgc and has_geom:
                await cur.execute(
                    """
                    SELECT ST_Contains(r.geom, p.geom)
                    FROM projects p, regions r
                    WHERE p.contract_id = %s
                      AND r.psgc_code = %s
                    LIMIT 1;
                    """,
                    (contract_id, stated_region_psgc),
                )
                spatial_row = await cur.fetchone()
                if spatial_row is not None and spatial_row[0] is False:
                    flags.append(
                        ProjectFlag(
                            code="COORDINATES_OUTSIDE_REGION",
                            message="Project coordinates fall outside the stated region boundary",
                            severity="warning",
                            details={
                                "contract_id": contract_id,
                                "stated_region_psgc": stated_region_psgc,
                            },
                        )
                    )
            elif psgc_code and has_geom:
                # Fallback to checking assigned region
                await cur.execute(
                    """
                    SELECT ST_Contains(r.geom, p.geom)
                    FROM projects p
                    JOIN barangays b ON p.psgc_code = b.psgc_code
                    JOIN municipalities m ON b.parent_psgc = m.psgc_code
                    JOIN provinces prov ON m.parent_psgc = prov.psgc_code
                    JOIN regions r ON prov.parent_psgc = r.psgc_code
                    WHERE p.contract_id = %s
                    LIMIT 1;
                    """,
                    (contract_id,),
                )
                spatial_row = await cur.fetchone()
                if spatial_row is not None and spatial_row[0] is False:
                    flags.append(
                        ProjectFlag(
                            code="COORDINATES_OUTSIDE_REGION",
                            message="Project coordinates fall outside the assigned region boundary",
                            severity="warning",
                            details={"contract_id": contract_id, "psgc_code": psgc_code},
                        )
                    )

    return flags


async def get_project_detail(
    contract_id: str,
    data_version: str,
) -> ProjectDetailResponse | None:
    """Retrieve full project detail, evaluate flags, and fetch related procurement awards."""
    sql = """
        SELECT
            p.contract_id,
            p.title,
            p.description,
            p.implementing_office,
            p.funding_source,
            p.budget_php,
            p.contract_cost_php,
            p.start_date,
            p.target_completion_date,
            p.physical_progress_pct,
            ST_Y(p.geom) AS latitude,
            ST_X(p.geom) AS longitude,
            (p.geom IS NOT NULL) AS has_geom,
            p.psgc_code,
            p.contractor_id,
            c.normalized_name AS contractor_name,
            p.ingested_at,
            b.name AS barangay_name,
            m.name AS municipality_name,
            prov.name AS province_name,
            r.name AS region_name
        FROM projects p
        LEFT JOIN contractors c ON p.contractor_id = c.id
        LEFT JOIN barangays b ON p.psgc_code = b.psgc_code
        LEFT JOIN municipalities m ON b.parent_psgc = m.psgc_code
        LEFT JOIN provinces prov ON m.parent_psgc = prov.psgc_code
        LEFT JOIN regions r ON prov.parent_psgc = r.psgc_code
        WHERE p.contract_id = %s
        LIMIT 1
    """

    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (contract_id,))
            row = await cur.fetchone()
            if not row:
                return None

            proj_data: dict[str, Any] = {
                "contract_id": row[0],
                "title": row[1],
                "description": row[2],
                "implementing_office": row[3],
                "funding_source": row[4],
                "budget_php": Decimal(str(row[5])) if row[5] is not None else None,
                "contract_cost_php": Decimal(str(row[6])) if row[6] is not None else None,
                "start_date": row[7],
                "target_completion_date": row[8],
                "physical_progress_pct": Decimal(str(row[9])) if row[9] is not None else None,
                "latitude": float(row[10]) if row[10] is not None else None,
                "longitude": float(row[11]) if row[11] is not None else None,
                "has_geom": bool(row[12]),
                "psgc_code": row[13],
                "contractor_id": row[14],
                "contractor_name": row[15],
                "ingested_at": row[16],
                "barangay_name": row[17],
                "municipality_name": row[18],
                "province_name": row[19],
                "region_name": row[20],
            }

            # Fetch related procurement awards matching contract ID, contractor, or PSGC
            awards_sql = """
                SELECT id, reference_id, title, award_amount_php, award_date, procuring_entity
                FROM procurement_awards
                WHERE reference_id = %s
                   OR title ILIKE '%%' || %s || '%%'
                   OR (contractor_id IS NOT NULL AND contractor_id = %s)
                   OR (psgc_code IS NOT NULL AND psgc_code = %s)
                ORDER BY
                    (reference_id = %s) DESC,
                    award_date DESC NULLS LAST
                LIMIT 10
            """
            await cur.execute(
                awards_sql,
                (
                    contract_id,
                    contract_id,
                    proj_data["contractor_id"],
                    proj_data["psgc_code"],
                    contract_id,
                ),
            )
            award_rows = await cur.fetchall()
            related_awards = [
                ProcurementAwardSummary(
                    id=ar[0],
                    reference_id=ar[1],
                    title=ar[2],
                    award_amount_php=Decimal(str(ar[3])) if ar[3] is not None else None,
                    award_date=ar[4],
                    procuring_entity=ar[5],
                )
                for ar in award_rows
            ]

    flags = await evaluate_project_flags(proj_data)

    return ProjectDetailResponse(
        contract_id=proj_data["contract_id"],
        title=proj_data["title"],
        description=proj_data["description"],
        implementing_office=proj_data["implementing_office"],
        funding_source=proj_data["funding_source"],
        budget_php=proj_data["budget_php"],
        contract_cost_php=proj_data["contract_cost_php"],
        start_date=proj_data["start_date"],
        target_completion_date=proj_data["target_completion_date"],
        physical_progress_pct=proj_data["physical_progress_pct"],
        latitude=proj_data["latitude"],
        longitude=proj_data["longitude"],
        psgc_code=proj_data["psgc_code"],
        barangay_name=proj_data["barangay_name"],
        municipality_name=proj_data["municipality_name"],
        province_name=proj_data["province_name"],
        region_name=proj_data["region_name"],
        contractor_id=proj_data["contractor_id"],
        contractor_name=proj_data["contractor_name"],
        flags=flags,
        related_awards=related_awards,
        ingested_at=proj_data["ingested_at"],
        data_version=data_version,
    )
