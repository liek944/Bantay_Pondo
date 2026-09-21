"""Contractor service with district concentration and HHI calculation."""

from decimal import Decimal

from api.schemas.contractors import (
    ContractorProfileResponse,
    ContractorSummary,
    DistrictConcentration,
    DistrictConcentrationItem,
)
from api.schemas.projects import ProjectSummary
from db.session import get_async_db_connection


async def get_contractor_profile(
    contractor_id: int,
    data_version: str,
) -> ContractorProfileResponse | None:
    """Retrieve contractor profile, list of awarded contracts, and district HHI concentration."""
    profile_sql = """
        SELECT id, normalized_name, raw_names, address, first_seen, total_contracts, total_value_php
        FROM contractors
        WHERE id = %s
        LIMIT 1
    """

    contracts_sql = """
        SELECT
            contract_id, title, implementing_office, funding_source,
            budget_php, contract_cost_php, start_date, target_completion_date,
            physical_progress_pct, psgc_code, contractor_id
        FROM projects
        WHERE contractor_id = %s
        ORDER BY start_date DESC NULLS LAST, budget_php DESC NULLS LAST
    """

    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(profile_sql, (contractor_id,))
            prof_row = await cur.fetchone()
            if not prof_row:
                return None

            profile = ContractorSummary(
                id=prof_row[0],
                normalized_name=prof_row[1],
                raw_names=list(prof_row[2]) if prof_row[2] else [],
                address=prof_row[3],
                first_seen=prof_row[4],
                total_contracts=prof_row[5],
                total_value_php=Decimal(str(prof_row[6])),
            )

            await cur.execute(contracts_sql, (contractor_id,))
            contract_rows = await cur.fetchall()

    contracts: list[ProjectSummary] = []
    district_totals: dict[str, Decimal] = {}
    district_counts: dict[str, int] = {}
    total_val = Decimal("0")

    for r in contract_rows:
        val = (
            Decimal(str(r[5]))
            if r[5] is not None
            else (Decimal(str(r[4])) if r[4] is not None else Decimal("0"))
        )
        office = str(r[2]) if r[2] else "Unassigned District"
        district_totals[office] = district_totals.get(office, Decimal("0")) + val
        district_counts[office] = district_counts.get(office, 0) + 1
        total_val += val

        contracts.append(
            ProjectSummary(
                contract_id=r[0],
                title=r[1],
                implementing_office=r[2],
                funding_source=r[3],
                budget_php=Decimal(str(r[4])) if r[4] is not None else None,
                contract_cost_php=Decimal(str(r[5])) if r[5] is not None else None,
                start_date=r[6],
                target_completion_date=r[7],
                physical_progress_pct=Decimal(str(r[8])) if r[8] is not None else None,
                psgc_code=r[9],
                contractor_id=r[10],
                contractor_name=profile.normalized_name,
            )
        )

    # Compute Herfindahl-Hirschman Index (HHI)
    market_shares: list[DistrictConcentrationItem] = []
    hhi = 0.0

    if total_val > 0:
        for office, val in sorted(district_totals.items(), key=lambda x: x[1], reverse=True):
            share_pct = float((val / total_val) * Decimal("100"))
            hhi += (share_pct) ** 2
            market_shares.append(
                DistrictConcentrationItem(
                    district=office,
                    contract_count=district_counts[office],
                    total_value_php=val,
                    share_pct=round(share_pct, 2),
                )
            )
    elif district_counts:
        # Fallback to contract count share if monetary values are all zero
        total_contracts = sum(district_counts.values())
        for office, count in sorted(district_counts.items(), key=lambda x: x[1], reverse=True):
            share_pct = float((count / total_contracts) * 100)
            hhi += (share_pct) ** 2
            market_shares.append(
                DistrictConcentrationItem(
                    district=office,
                    contract_count=count,
                    total_value_php=Decimal("0"),
                    share_pct=round(share_pct, 2),
                )
            )

    hhi = round(hhi, 2)
    norm_hhi = round(hhi / 10000.0, 4)

    if hhi > 2500:
        interpretation = "Highly Concentrated (Operations concentrated in few districts)"
    elif hhi >= 1500:
        interpretation = "Moderately Concentrated"
    else:
        interpretation = "Diversified / Competitive"

    district_concentration = DistrictConcentration(
        hhi=hhi,
        normalized_hhi=norm_hhi,
        interpretation=interpretation,
        market_shares=market_shares,
    )

    return ContractorProfileResponse(
        profile=profile,
        contracts=contracts,
        district_concentration=district_concentration,
        data_version=data_version,
    )
