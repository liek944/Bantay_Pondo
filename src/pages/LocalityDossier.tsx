import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Download, ArrowLeftRight, ShieldAlert, Calendar } from 'lucide-react';

import {
  Breadcrumb,
  StatBlock,
  RiskBadge,
  MismatchScale,
  HazardBars,
  OfficialStrip,
  ProjectList,
  OfficialInfo,
} from '../components';
import { ProjectSummary } from '../components/ProjectRow';

export const LocalityDossier: React.FC = () => {
  const { psgcCode = '021500000' } = useParams<{ psgcCode: string }>();
  const [selectedYear, setSelectedYear] = useState('All Years (2018–2024)');

  const breadcrumbs = [
    { label: 'National Registry', path: '/' },
    { label: 'Region II (Cagayan Valley)', path: '/' },
    { label: 'Cagayan', path: '/' },
    { label: 'Tuguegarao City' },
  ];

  const hazardExposures = [
    {
      label: '100-Year Flood Inundation (NOAH)',
      percentage: 84.2,
      riskTier: 'critical' as const,
      description:
        'Extensive low-lying plains along Cagayan & Pinacanauan rivers subject to deep flooding.',
    },
    {
      label: 'Rain-Induced Landslide (MGB)',
      percentage: 12.6,
      riskTier: 'low' as const,
      description: 'Eastern periphery rolling terrain and elevated barangay slopes.',
    },
    {
      label: 'Storm Surge Vulnerability',
      percentage: 0.0,
      riskTier: 'low' as const,
      description: 'Inland river basin; zero direct coastal surge exposure.',
    },
  ];

  const officials: OfficialInfo[] = [
    {
      id: 'off-1',
      name: 'Hon. Joseph L. Lara',
      position: 'Representative',
      district: '3rd District of Cagayan',
      party: 'PDP-Laban / NUP',
      term_start: 2019,
      term_end: 2025,
    },
    {
      id: 'off-2',
      name: 'Hon. Maila Rosario S. Ting-Que',
      position: 'City Mayor',
      district: 'Tuguegarao City LGU',
      party: 'Liberal / Independent',
      term_start: 2022,
      term_end: 2025,
    },
    {
      id: 'off-3',
      name: 'Hon. Manuel N. Mamba',
      position: 'Provincial Governor',
      district: 'Province of Cagayan',
      party: 'Nacionalista',
      term_start: 2016,
      term_end: 2025,
    },
  ];

  const projects: ProjectSummary[] = [
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
      contract_id: '23BC0012',
      title: 'Urban Drainage Mains & Outfall Channel Construction, Centro Sector',
      contractor_name: 'Northern Builders & Supply Corp.',
      contractor_id: 'northern-builders',
      implementing_office: 'DPWH Regional Office II',
      budget_php: 78500000,
      contract_cost_php: 76200000,
      physical_progress_pct: 62.4,
      target_completion_date: '2024-12-15',
      flags_count: 0,
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
  ];

  return (
    <div className="flex flex-col w-full bg-surface text-on-surface">
      {/* Dossier Banner */}
      <section className="w-full bg-surface-container-low border-b border-hairline px-margin md:px-margin-desktop py-space-xl">
        <div className="max-w-[1360px] mx-auto flex flex-col gap-space-md">
          <Breadcrumb items={breadcrumbs} />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-lg">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-space-sm flex-wrap">
                <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                  Provincial Capital Dossier • PSGC {psgcCode}
                </span>
                <span className="text-outline-variant">|</span>
                <span className="font-code-tabular text-body-sm text-secondary">
                  Class 1 City • 49 Barangays
                </span>
              </div>

              <h1 className="font-serif font-bold text-headline-lg md:text-[3rem] text-primary tracking-tight leading-tight mt-0.5">
                Tuguegarao City
              </h1>

              <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl mt-1">
                Located at the confluence of the Cagayan and Pinacanauan Rivers, Tuguegarao acts as
                the commercial and administrative capital of Cagayan Valley while bearing recurrent,
                catastrophic riverine flooding.
              </p>
            </div>

            {/* Risk Indicator Card & Actions */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-space-md shrink-0">
              <div className="p-space-md rounded bg-surface-container-lowest border border-hairline flex flex-col gap-1 min-w-[200px]">
                <div className="flex items-center justify-between">
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase font-bold">
                    Audit Classification
                  </span>
                  <RiskBadge level="critical" score={92} />
                </div>
                <span className="font-serif font-bold text-headline-md text-risk-critical-text">
                  Score 92 / 100
                </span>
                <span className="font-body-sm text-[0.75rem] text-secondary">
                  Ranked #1 Most Mismatched in Region II
                </span>
              </div>

              <div className="flex flex-col sm:flex-row gap-2">
                <Link
                  to="/compare?a=021500000&b=035413000"
                  className="px-space-md py-2 rounded bg-surface-container-lowest border border-outline-variant hover:bg-surface-container text-on-surface font-label-caps text-label-caps uppercase tracking-wider flex items-center justify-center gap-1.5 transition-colors"
                >
                  <ArrowLeftRight className="w-4 h-4 text-primary" /> Compare
                </Link>
                <button
                  type="button"
                  className="px-space-md py-2 rounded bg-primary text-on-primary hover:bg-primary-container font-label-caps text-label-caps uppercase tracking-wider flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                >
                  <Download className="w-4 h-4" /> Export Dossier
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Metric Cards and Hazard Profile */}
      <section className="w-full max-w-[1360px] mx-auto px-margin md:px-margin-desktop py-space-xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
          {/* 4 Primary Stat Blocks */}
          <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-space-md">
            <StatBlock
              label="Consolidated Spend"
              value="₱1.42B"
              subtext="41 DPWH Flood & River Works Projects (2018–2024)"
              trend="SARO Verified"
            />
            <StatBlock
              label="Spend Per Capita"
              value="₱8,540"
              subtext="Population 166,334 (2020 Census PSA)"
            />
            <StatBlock
              label="Hazard Exposure"
              value="84.2%"
              subtext="95.8 sq km within 100-Year High Inundation Zone"
              subtextColor="risk-critical"
            />
            <StatBlock
              label="Discrepancy Multiplier"
              value="3.4x"
              subtext="Over expected regional flood expenditure curve"
              subtextColor="risk-high"
            />

            {/* Mismatch Visualizer Container */}
            <div className="sm:col-span-2 p-space-md bg-surface-container-lowest border border-hairline rounded flex flex-col gap-2">
              <MismatchScale score={92} nationalPercentile={99} />
              <div className="flex items-start gap-2 mt-1 p-2 rounded bg-risk-critical-bg border border-risk-critical-border text-on-surface text-[0.75rem]">
                <ShieldAlert className="w-4 h-4 text-risk-critical-text shrink-0 mt-0.5" />
                <span>
                  <strong>Audit Warning:</strong> Over 64% of all local flood mitigation tenders
                  were awarded to a single contractor, with severe repeat delay observations noted
                  by the Commission on Audit.
                </span>
              </div>
            </div>
          </div>

          {/* Right Hazard Breakdown */}
          <div className="lg:col-span-5 flex flex-col gap-space-md">
            <HazardBars items={hazardExposures} />
          </div>
        </div>
      </section>

      {/* Audited Infrastructure Projects Ledger */}
      <section className="w-full max-w-[1360px] mx-auto px-margin md:px-margin-desktop pb-space-2xl">
        <div className="flex items-center justify-between mb-space-sm">
          <div className="flex items-center gap-space-sm">
            <Calendar className="w-4 h-4 text-primary" />
            <span className="font-label-caps text-label-caps uppercase text-secondary font-bold">
              Filter By Legislative Year:
            </span>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="bg-surface-container-lowest border border-hairline rounded px-2 py-1 font-body-sm text-[0.8125rem] text-on-surface focus:outline-none"
            >
              <option>All Years (2018–2024)</option>
              <option>2024 Projects</option>
              <option>2023 Projects</option>
              <option>2022 Projects</option>
            </select>
          </div>

          <Link
            to="/contractor/alpha-omega"
            className="font-label-caps text-label-caps uppercase text-primary font-bold hover:underline"
          >
            Inspect Contractor Ties &rarr;
          </Link>
        </div>

        <ProjectList
          projects={projects}
          title="Audited DPWH Flood Control Projects"
          subtitle="Cross-matched with PhilGEPS procurement contracts, COA observation memos, and satellite ground truths."
        />
      </section>

      {/* Incumbent Political Representation */}
      <section className="w-full max-w-[1360px] mx-auto px-margin md:px-margin-desktop pb-space-2xl">
        <OfficialStrip officials={officials} />
      </section>
    </div>
  );
};
