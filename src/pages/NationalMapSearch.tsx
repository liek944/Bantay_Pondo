import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  Building,
  ShieldAlert,
  Download,
  Filter,
} from 'lucide-react';
import {
  SearchInput,
  StatBlock,
  RiskBadge,
  MismatchScale,
  MapPanel,
  RiskLevel,
} from '../components';

interface LocalityRanking {
  rank: number;
  psgc_code: string;
  name: string;
  province: string;
  region: string;
  population: number;
  flood_pct: number;
  total_spend_php: number;
  spend_per_capita: number;
  mismatch_score: number;
  risk_level: RiskLevel;
  flags_count: number;
}

const mockRankings: LocalityRanking[] = [
  {
    rank: 1,
    psgc_code: '021500000',
    name: 'Tuguegarao City',
    province: 'Cagayan',
    region: 'Region II',
    population: 166334,
    flood_pct: 84.2,
    total_spend_php: 1420500000,
    spend_per_capita: 8540,
    mismatch_score: 92,
    risk_level: 'critical',
    flags_count: 5,
  },
  {
    rank: 2,
    psgc_code: '035413000',
    name: 'Masantol',
    province: 'Pampanga',
    region: 'Region III',
    population: 57064,
    flood_pct: 91.5,
    total_spend_php: 310200000,
    spend_per_capita: 5435,
    mismatch_score: 89,
    risk_level: 'critical',
    flags_count: 3,
  },
  {
    rank: 3,
    psgc_code: '031405000',
    name: 'Calumpit',
    province: 'Bulacan',
    region: 'Region III',
    population: 118471,
    flood_pct: 88.0,
    total_spend_php: 840100000,
    spend_per_capita: 7091,
    mismatch_score: 86,
    risk_level: 'critical',
    flags_count: 4,
  },
  {
    rank: 4,
    psgc_code: '137402000',
    name: 'Marikina City',
    province: 'Metro Manila',
    region: 'NCR',
    population: 456059,
    flood_pct: 76.4,
    total_spend_php: 4210000000,
    spend_per_capita: 9231,
    mismatch_score: 79,
    risk_level: 'critical',
    flags_count: 2,
  },
  {
    rank: 5,
    psgc_code: '023114000',
    name: 'Ilagan City',
    province: 'Isabela',
    region: 'Region II',
    population: 158218,
    flood_pct: 69.8,
    total_spend_php: 1180000000,
    spend_per_capita: 7458,
    mismatch_score: 73,
    risk_level: 'high',
    flags_count: 2,
  },
  {
    rank: 6,
    psgc_code: '083747000',
    name: 'Ormoc City',
    province: 'Leyte',
    region: 'Region VIII',
    population: 230998,
    flood_pct: 62.1,
    total_spend_php: 1950000000,
    spend_per_capita: 8441,
    mismatch_score: 68,
    risk_level: 'high',
    flags_count: 1,
  },
  {
    rank: 7,
    psgc_code: '104210000',
    name: 'Oroquieta City',
    province: 'Misamis Occidental',
    region: 'Region X',
    population: 72301,
    flood_pct: 54.3,
    total_spend_php: 740000000,
    spend_per_capita: 10235,
    mismatch_score: 58,
    risk_level: 'high',
    flags_count: 1,
  },
];

export const NationalMapSearch: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('All Localities');
  const navigate = useNavigate();

  const scopeChips = [
    'All Localities',
    'Critical Anomaly (>75)',
    'High Inundation',
    'Flood Hotspots',
  ];

  const filteredRankings = mockRankings.filter((r) => {
    const matchesSearch =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.province.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.psgc_code.includes(searchQuery);

    if (selectedFilter === 'Critical Anomaly (>75)') {
      return matchesSearch && r.mismatch_score > 75;
    }
    if (selectedFilter === 'High Inundation') {
      return matchesSearch && r.flood_pct > 75;
    }
    return matchesSearch;
  });

  const formatPeso = (val: number) => {
    if (val >= 1e9) return `₱${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `₱${(val / 1e6).toFixed(1)}M`;
    return `₱${val.toLocaleString()}`;
  };

  return (
    <div className="flex flex-col w-full bg-surface text-on-surface">
      {/* Editorial Mission Hero Section */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop pt-space-xl pb-space-lg">
        <div className="flex flex-col gap-space-md max-w-4xl">
          <div className="flex flex-wrap items-center gap-space-sm">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-tertiary/10 text-tertiary font-label-caps text-label-caps uppercase tracking-wider font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
              National Audit Investigation
            </span>
            <span className="text-outline-variant">/</span>
            <span className="font-code-tabular text-body-sm text-secondary">
              NOAH-DPWH Cross-Index 2018–2024
            </span>
          </div>

          <h1 className="font-serif font-bold text-headline-lg md:text-[3.25rem] text-primary tracking-tight leading-[1.08] mt-1">
            Where Public Billions Meet Disaster Vulnerability.
          </h1>

          <p className="font-serif text-body-lg text-on-surface-variant leading-relaxed text-balance">
            Bantay Pondo cross-references every DPWH flood control and road infrastructure
            expenditure against geohazard maps from NOAH and MGB. Discover whether tax money
            protects the most endangered communities or flows elsewhere.
          </p>
        </div>

        {/* 4 Key Stat Blocks */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md mt-space-xl">
          <StatBlock
            label="Audited National Spend"
            value="₱584.2B"
            subtext="Consolidated DPWH Flood Control 2018–2024"
            trend="+18.4% YoY"
          />
          <StatBlock
            label="High Hazard Population"
            value="24.8M"
            subtext="Filipinos in 100-Year Flood & Landslide Zones"
            subtextColor="risk-high"
          />
          <StatBlock
            label="Discrepancy Alert Index"
            value="68.4"
            subtext="National Median Expenditure-Hazard Mismatch"
            subtextColor="risk-critical"
          />
          <StatBlock
            label="Tracked Contractors"
            value="3,412"
            subtext="Entities Cross-Referenced with PhilGEPS & SEC"
          />
        </div>
      </section>

      {/* Interactive Map & Search Drawer Section */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop mb-space-2xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
          {/* Left Search & Locality Filter Drawer */}
          <div className="lg:col-span-5 bg-surface-container-lowest border border-hairline rounded p-space-lg flex flex-col gap-space-md shadow-sm">
            <div className="flex items-center justify-between border-b border-hairline pb-space-xs">
              <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                Geographic Investigation Registry
              </span>
              <span className="font-code-tabular text-[0.6875rem] text-secondary">
                1,489 LGUs Audited
              </span>
            </div>

            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              onClear={() => setSearchQuery('')}
              scopeChips={scopeChips}
              activeChip={selectedFilter}
              onSelectChip={setSelectedFilter}
            />

            {/* Quick Filter Selectors */}
            <div className="flex items-center justify-between gap-space-sm pt-1">
              <div className="flex items-center gap-1.5 text-secondary text-body-sm">
                <Filter className="w-3.5 h-3.5" />
                <span className="font-label-caps text-[0.6875rem] uppercase">Quick Focus:</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSearchQuery('Tuguegarao')}
                  className="px-2 py-0.5 rounded bg-surface-container text-primary font-code-tabular text-[0.75rem] hover:bg-primary hover:text-on-primary transition-colors"
                >
                  Tuguegarao
                </button>
                <button
                  type="button"
                  onClick={() => setSearchQuery('Marikina')}
                  className="px-2 py-0.5 rounded bg-surface-container text-primary font-code-tabular text-[0.75rem] hover:bg-primary hover:text-on-primary transition-colors"
                >
                  Marikina
                </button>
                <button
                  type="button"
                  onClick={() => setSearchQuery('Calumpit')}
                  className="px-2 py-0.5 rounded bg-surface-container text-primary font-code-tabular text-[0.75rem] hover:bg-primary hover:text-on-primary transition-colors"
                >
                  Calumpit
                </button>
              </div>
            </div>

            {/* Filtered Localities List */}
            <div className="flex flex-col divide-y divide-hairline max-h-[380px] overflow-y-auto mt-2">
              {filteredRankings.map((locality) => (
                <div
                  key={locality.psgc_code}
                  onClick={() => navigate(`/locality/${locality.psgc_code}`)}
                  className="py-3 px-2 flex items-center justify-between hover:bg-surface-container-low cursor-pointer transition-colors group"
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-body-md font-bold text-on-surface group-hover:text-primary transition-colors">
                        {locality.name}
                      </span>
                      <RiskBadge level={locality.risk_level} score={locality.mismatch_score} />
                    </div>
                    <span className="font-body-sm text-[0.75rem] text-secondary">
                      {locality.province} • Pop. {locality.population.toLocaleString()} • Spend:{' '}
                      {formatPeso(locality.total_spend_php)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <div className="text-right">
                      <span className="font-code-tabular text-body-sm font-bold text-risk-500 block">
                        {locality.flood_pct}% Hazard
                      </span>
                      <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                        {locality.flags_count} COA Flags
                      </span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-outline-variant group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-space-sm border-t border-hairline flex items-center justify-between text-secondary font-label-caps text-[0.6875rem] uppercase">
              <span>Showing {filteredRankings.length} matching LGUs</span>
              <Link to="/compare" className="text-primary font-semibold hover:underline">
                Compare Multiple LGUs &rarr;
              </Link>
            </div>
          </div>

          {/* Right Geospatial Map Panel */}
          <div className="lg:col-span-7 flex flex-col gap-space-sm">
            <MapPanel
              title="NOAH Hazard & Public Works Infrastructure Viewport"
              centerCoordinates="17.6132° N, 121.7270° E (Cagayan Basin Focus)"
              heightClass="h-[520px]"
              pins={[
                {
                  id: 'p1',
                  name: 'Cagayan River Dike Ph III',
                  lat: 17.61,
                  lng: 121.72,
                  cost: '₱142.5M',
                },
                {
                  id: 'p2',
                  name: 'Pampanga Delta Revetment',
                  lat: 14.85,
                  lng: 120.65,
                  cost: '₱310.2M',
                },
                {
                  id: 'p3',
                  name: 'Marikina Retarding Basin',
                  lat: 14.65,
                  lng: 121.1,
                  cost: '₱1.2B',
                },
              ]}
              onSelectPin={() => navigate('/project/22BC0045')}
            />
          </div>
        </div>
      </section>

      {/* Highest Mismatch Rankings Table Section */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop mb-space-2xl">
        <div className="p-space-lg bg-surface-container-lowest border border-hairline rounded flex flex-col gap-space-md shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-sm border-b border-hairline pb-space-md">
            <div>
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-risk-critical-text" />
                <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                  Civic Anomaly Ledger
                </span>
              </div>
              <h2 className="font-serif font-bold text-headline-md text-primary mt-1">
                Highest Expenditure-Hazard Mismatch This Quarter
              </h2>
              <p className="font-body-sm text-body-sm text-secondary mt-0.5">
                Municipalities with extreme flood exposure but disproportionate or stalled DPWH
                flood-mitigation disbursements.
              </p>
            </div>

            <button
              type="button"
              className="inline-flex items-center gap-1.5 px-space-md py-1.5 rounded border border-outline-variant text-on-surface hover:bg-surface-container-low transition-colors font-label-caps text-label-caps uppercase tracking-wider self-start md:self-auto"
            >
              <Download className="w-4 h-4 text-primary" /> Export Top 100 CSV
            </button>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container border-b-2 border-primary/20 font-label-caps text-label-caps uppercase text-secondary">
                  <th className="py-3 px-4 font-bold">Rank</th>
                  <th className="py-3 px-4 font-bold">Locality &amp; Province</th>
                  <th className="py-3 px-4 font-bold text-right">Population</th>
                  <th className="py-3 px-4 font-bold text-right">NOAH Inundation</th>
                  <th className="py-3 px-4 font-bold text-right">2018–2024 Spend</th>
                  <th className="py-3 px-4 font-bold text-right">Spend / Capita</th>
                  <th className="py-3 px-4 font-bold min-w-[180px]">Mismatch Anomaly</th>
                  <th className="py-3 px-4 font-bold text-center">COA Flags</th>
                  <th className="py-3 px-4 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {mockRankings.map((lgu) => (
                  <tr
                    key={lgu.psgc_code}
                    className="hover:bg-surface-container-low transition-colors group"
                  >
                    <td className="py-3.5 px-4 font-code-tabular font-bold text-primary">
                      #{lgu.rank}
                    </td>

                    <td className="py-3.5 px-4">
                      <Link
                        to={`/locality/${lgu.psgc_code}`}
                        className="font-bold text-on-surface hover:text-primary transition-colors block"
                      >
                        {lgu.name}
                      </Link>
                      <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                        {lgu.province} • {lgu.region}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-code-tabular text-right text-on-surface">
                      {lgu.population.toLocaleString()}
                    </td>

                    <td className="py-3.5 px-4 font-code-tabular text-right font-bold text-risk-500">
                      {lgu.flood_pct.toFixed(1)}%
                    </td>

                    <td className="py-3.5 px-4 font-code-tabular text-right font-bold text-primary whitespace-nowrap">
                      {formatPeso(lgu.total_spend_php)}
                    </td>

                    <td className="py-3.5 px-4 font-code-tabular text-right text-on-surface whitespace-nowrap">
                      {formatPeso(lgu.spend_per_capita)}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex flex-col gap-1">
                        <RiskBadge level={lgu.risk_level} score={lgu.mismatch_score} />
                        <MismatchScale score={lgu.mismatch_score} />
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-center">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-risk-high-bg border border-risk-high-border text-risk-high-text font-label-caps text-[0.6875rem] font-bold">
                        <AlertTriangle className="w-3 h-3 text-risk-500" />
                        {lgu.flags_count}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/locality/${lgu.psgc_code}`}
                        className="inline-flex items-center gap-1 font-label-caps text-[0.6875rem] text-primary hover:underline uppercase font-bold"
                      >
                        Dossier &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Explanatory Editorial Cards */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop pb-space-2xl">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-space-lg">
          <div className="p-space-lg rounded bg-surface-container-lowest border border-hairline flex flex-col gap-space-sm">
            <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary">
              <TrendingUp className="w-4 h-4" />
            </div>
            <h3 className="font-serif font-bold text-headline-sm text-primary">
              How Mismatch Is Computed
            </h3>
            <p className="font-body-sm text-body-sm text-secondary leading-relaxed">
              We divide historical 6-year DPWH capital infrastructure outlays against NOAH flood
              exposure and population density. A high score means vast budgets flow to low-hazard
              zones or zero funds reach flood-threatened communities.
            </p>
            <Link
              to="/methodology"
              className="mt-auto font-label-caps text-label-caps uppercase text-primary hover:underline font-bold"
            >
              Read Full Formula Spec &rarr;
            </Link>
          </div>

          <div className="p-space-lg rounded bg-surface-container-lowest border border-hairline flex flex-col gap-space-sm">
            <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary">
              <Building className="w-4 h-4" />
            </div>
            <h3 className="font-serif font-bold text-headline-sm text-primary">
              Contractor Cartel Detection
            </h3>
            <p className="font-body-sm text-body-sm text-secondary leading-relaxed">
              Using the Herfindahl-Hirschman Index (HHI), we track whether single contractors
              monopolize legislative districts, winning upwards of 60% of all public flood
              mitigation tenders.
            </p>
            <Link
              to="/contractor/alpha-omega"
              className="mt-auto font-label-caps text-label-caps uppercase text-primary hover:underline font-bold"
            >
              Inspect Top Contractors &rarr;
            </Link>
          </div>

          <div className="p-space-lg rounded bg-surface-container-lowest border border-hairline flex flex-col gap-space-sm">
            <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <h3 className="font-serif font-bold text-headline-sm text-primary">
              Whistleblower Vault
            </h3>
            <p className="font-body-sm text-body-sm text-secondary leading-relaxed">
              Have evidence of ghost revetment walls, washed-out sheet piles, or unliquidated SARO
              allocations? Submit encrypted photos with immutable cryptographic timestamps.
            </p>
            <Link
              to="/methodology"
              className="mt-auto font-label-caps text-label-caps uppercase text-primary hover:underline font-bold"
            >
              Submit Evidence Privately &rarr;
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
