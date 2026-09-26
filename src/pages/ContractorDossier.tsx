import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Download, AlertTriangle, Search } from 'lucide-react';
import { Breadcrumb, StatBlock, RiskBadge, ProjectList } from '../components';
import { ProjectSummary } from '../components/ProjectRow';

export const ContractorDossier: React.FC = () => {
  const { id = 'alpha-omega' } = useParams<{ id: string }>();
  const [filterQuery, setFilterQuery] = useState('');

  const breadcrumbs = [
    { label: 'National Registry', path: '/' },
    { label: 'Contractor Intelligence', path: '/' },
    { label: 'Alpha & Omega Gen. Contractor & Devt. Corp.' },
  ];

  const contractorProjects: ProjectSummary[] = [
    {
      contract_id: '22BC0045',
      title: 'Construction of River Dike along Cagayan River Phase III, Tuguegarao Sector',
      contractor_name: 'Alpha & Omega Gen. Contractor & Devt. Corp.',
      contractor_id: 'alpha-omega',
      implementing_office: 'DPWH Cagayan 3rd DEO',
      budget_php: 145000000,
      contract_cost_php: 142500000,
      physical_progress_pct: 45.8,
      target_completion_date: '2023-11-30',
      flags_count: 2,
      is_delayed: true,
    },
    {
      contract_id: '21BC0089',
      title: 'Rehabilitation of Flood Control Revetment along Pinacanauan River',
      contractor_name: 'Alpha & Omega Gen. Contractor & Devt. Corp.',
      contractor_id: 'alpha-omega',
      implementing_office: 'DPWH Cagayan 3rd DEO',
      budget_php: 98000000,
      contract_cost_php: 96800000,
      physical_progress_pct: 100.0,
      target_completion_date: '2022-08-15',
      flags_count: 1,
    },
    {
      contract_id: '20BC0114',
      title: 'Buntun Bridge Approach Riverbank Stabilization & Sheet Piling',
      contractor_name: 'Alpha & Omega Gen. Contractor & Devt. Corp.',
      contractor_id: 'alpha-omega',
      implementing_office: 'DPWH Cagayan 3rd DEO',
      budget_php: 220000000,
      contract_cost_php: 218400000,
      physical_progress_pct: 88.0,
      target_completion_date: '2022-03-31',
      flags_count: 2,
      is_delayed: true,
    },
    {
      contract_id: '23BC0078',
      title: 'Construction of Concrete Slope Protection, Enrile Floodway Sector',
      contractor_name: 'Alpha & Omega Gen. Contractor & Devt. Corp.',
      contractor_id: 'alpha-omega',
      implementing_office: 'DPWH Cagayan 3rd DEO',
      budget_php: 185000000,
      contract_cost_php: 182100000,
      physical_progress_pct: 32.0,
      target_completion_date: '2024-11-15',
      flags_count: 1,
      is_delayed: true,
    },
  ];

  const filteredProjects = contractorProjects.filter(
    (p) =>
      p.title.toLowerCase().includes(filterQuery.toLowerCase()) ||
      p.contract_id.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col w-full bg-surface text-on-surface">
      {/* Contractor Header Banner */}
      <section className="w-full bg-surface-container-low border-b border-hairline px-margin md:px-margin-desktop py-space-xl">
        <div className="max-w-[1360px] mx-auto flex flex-col gap-space-md">
          <Breadcrumb items={breadcrumbs} />

          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-space-lg">
            <div className="flex flex-col gap-1 max-w-3xl">
              <div className="flex items-center gap-space-sm flex-wrap">
                <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                  PCAB License: AAAA (Large B - Heavy Infras)
                </span>
                <span className="text-outline-variant">|</span>
                <span className="font-code-tabular text-[0.75rem] text-secondary">
                  SEC Reg: CS200812498
                </span>
                <span className="text-outline-variant">|</span>
                <span className="font-label-caps text-[0.6875rem] uppercase text-secondary">
                  TIN: 241-892-104-000
                </span>
                <span className="text-outline-variant">|</span>
                <span className="font-code-tabular text-[0.75rem] text-secondary">ID: {id}</span>
              </div>

              <h1 className="font-serif font-bold text-headline-lg lg:text-[2.75rem] text-primary tracking-tight leading-tight mt-1">
                Alpha &amp; Omega Gen. Contractor &amp; Devt. Corp.
              </h1>

              <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl mt-1">
                Incorporated in 2008. Primary office registered in Pasig City, Metro Manila.
                Identified as the dominant public flood mitigation works contractor across Cagayan
                River basin districts.
              </p>

              <div className="flex items-center gap-2 mt-2">
                <RiskBadge level="critical" label="CRITICAL DISTRICT MONOPOLY (HHI: 0.428)" />
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                className="px-space-md py-2 rounded bg-surface-container-lowest border border-outline-variant hover:bg-surface-container text-on-surface font-label-caps text-label-caps uppercase tracking-wider flex items-center gap-1.5 transition-colors"
              >
                <Download className="w-4 h-4 text-primary" /> PhilGEPS Award Ledger CSV
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Financial & Monopolistic Concentration Stat Blocks */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop py-space-xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md">
          <StatBlock
            label="Total Awarded Spend"
            value="₱4.82B"
            subtext="Consolidated Across 38 DPWH Contracts"
            trend="142 Total Tenders"
          />
          <StatBlock
            label="District Win Rate"
            value="64.2%"
            subtext="Percentage of all Flood Tenders in Cagayan 3rd DEO"
            subtextColor="risk-critical"
          />
          <StatBlock
            label="Delayed / Stalled Projects"
            value="42.1%"
            subtext="16 Contracts Past Legal Delivery Date"
            subtextColor="risk-high"
          />
          <StatBlock
            label="Herfindahl Index (HHI)"
            value="0.428"
            subtext="Federal Antitrust Scale (>0.25 = Highly Concentrated)"
            subtextColor="risk-critical"
          />
        </div>
      </section>

      {/* Congressional District Concentration & Red Flags */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop pb-space-2xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-start">
          {/* Left Column: District Concentration Breakdown */}
          <div className="lg:col-span-6 bg-surface-container-lowest border border-hairline rounded p-space-lg flex flex-col gap-space-md shadow-sm">
            <div className="flex items-center justify-between border-b border-hairline pb-space-xs">
              <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                Congressional District Concentration Breakdown
              </span>
              <span className="font-code-tabular text-[0.6875rem] text-secondary">
                2018–2024 Procurement Cycle
              </span>
            </div>

            <p className="font-body-sm text-body-sm text-secondary">
              Proportion of Alpha &amp; Omega&apos;s total portfolio concentrated within specific
              legislative districts and implementing engineering offices.
            </p>

            <div className="flex flex-col gap-space-md">
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-body-sm">
                  <span className="font-bold text-on-surface">
                    Cagayan 3rd Legislative District
                  </span>
                  <span className="font-code-tabular font-bold text-risk-critical-text">
                    ₱3.10B (64.2%)
                  </span>
                </div>
                <div className="w-full h-3 rounded bg-surface-container overflow-hidden">
                  <div className="h-full bg-risk-700 rounded" style={{ width: '64.2%' }} />
                </div>
                <span className="font-body-sm text-[0.75rem] text-secondary">
                  Implementing Office: DPWH Cagayan 3rd DEO • Rep. Joseph Lara
                </span>
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-body-sm">
                  <span className="font-bold text-on-surface">
                    Isabela 1st Legislative District
                  </span>
                  <span className="font-code-tabular font-bold text-risk-high-text">
                    ₱1.08B (22.5%)
                  </span>
                </div>
                <div className="w-full h-3 rounded bg-surface-container overflow-hidden">
                  <div className="h-full bg-risk-500 rounded" style={{ width: '22.5%' }} />
                </div>
                <span className="font-body-sm text-[0.75rem] text-secondary">
                  Implementing Office: DPWH Isabela 1st DEO
                </span>
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between font-body-sm">
                  <span className="font-bold text-on-surface">
                    Bulacan 2nd Legislative District
                  </span>
                  <span className="font-code-tabular font-bold text-on-surface">₱640M (13.3%)</span>
                </div>
                <div className="w-full h-3 rounded bg-surface-container overflow-hidden">
                  <div className="h-full bg-primary rounded" style={{ width: '13.3%' }} />
                </div>
                <span className="font-body-sm text-[0.75rem] text-secondary">
                  Implementing Office: DPWH Bulacan 1st DEO
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Cartel Patterns & COA Observations */}
          <div className="lg:col-span-6 bg-surface-container-lowest border border-hairline rounded p-space-lg flex flex-col gap-space-md shadow-sm">
            <div className="flex items-center gap-2 border-b border-hairline pb-space-xs">
              <AlertTriangle className="w-5 h-5 text-risk-critical-text" />
              <h3 className="font-serif font-bold text-headline-sm text-primary">
                Procurement Audit Patterns
              </h3>
            </div>

            <div className="flex flex-col gap-space-md text-body-sm">
              <div className="p-space-md rounded bg-surface-container-low border border-hairline flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="font-code-tabular font-bold text-risk-critical-text text-[0.75rem]">
                    PATTERN: SINGLE CALCULATED RESPONSIVE BID (SCRB)
                  </span>
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    28 Contracts
                  </span>
                </div>
                <p className="text-secondary text-[0.8125rem]">
                  73.6% of tenders won in Cagayan Valley were awarded under single-bidder conditions
                  following disqualification of competing bidders during preliminary eligibility
                  screening.
                </p>
              </div>

              <div className="p-space-md rounded bg-surface-container-low border border-hairline flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="font-code-tabular font-bold text-risk-high-text text-[0.75rem]">
                    PATTERN: PARALLEL EQUIPMENT PLEDGES
                  </span>
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    COA AAR 2022
                  </span>
                </div>
                <p className="text-secondary text-[0.8125rem]">
                  Heavy dredging excavators and sheet-pile vibro-hammers were pledged simultaneously
                  across multiple active project sites exceeding certified operational capacity.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* All Recorded Contracts Table */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop pb-space-2xl">
        <div className="flex items-center justify-between mb-space-sm">
          <div className="relative w-72">
            <Search className="w-4 h-4 text-secondary absolute left-3 top-2.5" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Filter contractor contracts..."
              className="w-full pl-9 pr-3 py-1.5 rounded bg-surface-container-lowest border border-hairline text-body-sm focus:outline-none focus:border-accent"
            />
          </div>

          <Link
            to="/locality/021500000"
            className="font-label-caps text-label-caps uppercase text-primary font-bold hover:underline"
          >
            Locality Dossier &rarr;
          </Link>
        </div>

        <ProjectList
          projects={filteredProjects}
          title="Contracts Awarded to Alpha & Omega"
          subtitle="Showing active and completed flood control, revetment, and bridge infrastructure packages."
        />
      </section>
    </div>
  );
};
