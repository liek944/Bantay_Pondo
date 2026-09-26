import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowLeftRight, Download, Scale, AlertTriangle } from 'lucide-react';
import { Breadcrumb, CompareColumn, LocalityCompareData } from '../components';

const localityPresets: Record<string, LocalityCompareData> = {
  '021500000': {
    psgc_code: '021500000',
    name: 'Tuguegarao City',
    province: 'Cagayan (Region II)',
    population: 166334,
    total_spend_php: 1420500000,
    spend_per_capita: 8540,
    hazard_exposure_pct: 84.2,
    mismatch_score: 92,
    risk_level: 'critical',
    major_projects_count: 41,
  },
  '035413000': {
    psgc_code: '035413000',
    name: 'Masantol',
    province: 'Pampanga (Region III)',
    population: 57064,
    total_spend_php: 310200000,
    spend_per_capita: 5435,
    hazard_exposure_pct: 91.5,
    mismatch_score: 89,
    risk_level: 'critical',
    major_projects_count: 14,
  },
  '031405000': {
    psgc_code: '031405000',
    name: 'Calumpit',
    province: 'Bulacan (Region III)',
    population: 118471,
    total_spend_php: 840100000,
    spend_per_capita: 7091,
    hazard_exposure_pct: 88.0,
    mismatch_score: 86,
    risk_level: 'critical',
    major_projects_count: 22,
  },
};

export const CompareLocalities: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const paramA = searchParams.get('a') || '021500000';
  const paramB = searchParams.get('b') || '035413000';

  const [locAKey, setLocAKey] = useState(paramA in localityPresets ? paramA : '021500000');
  const [locBKey, setLocBKey] = useState(paramB in localityPresets ? paramB : '035413000');

  const locA = localityPresets[locAKey] || localityPresets['021500000'];
  const locB = localityPresets[locBKey] || localityPresets['035413000'];

  const breadcrumbs = [
    { label: 'National Registry', path: '/' },
    { label: 'Comparative Ledger' },
    { label: 'Dual Locality Audit' },
  ];

  const handleSwap = () => {
    const temp = locAKey;
    setLocAKey(locBKey);
    setLocBKey(temp);
    setSearchParams({ a: locBKey, b: temp });
  };

  const handleChangeA = (key: string) => {
    setLocAKey(key);
    setSearchParams({ a: key, b: locBKey });
  };

  const handleChangeB = (key: string) => {
    setLocBKey(key);
    setSearchParams({ a: locAKey, b: key });
  };

  const spendRatio = (locA.total_spend_php / (locB.total_spend_php || 1)).toFixed(1);

  return (
    <div className="flex flex-col w-full bg-surface text-on-surface">
      {/* Top Banner */}
      <section className="w-full bg-surface-container-low border-b border-hairline px-margin md:px-margin-desktop py-space-xl">
        <div className="max-w-[1360px] mx-auto flex flex-col gap-space-md">
          <Breadcrumb items={breadcrumbs} />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-lg">
            <div className="flex flex-col gap-1 max-w-3xl">
              <div className="flex items-center gap-space-sm">
                <Scale className="w-4 h-4 text-primary" />
                <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                  Comparative Forensic Audit
                </span>
              </div>

              <h1 className="font-serif font-bold text-headline-lg lg:text-[2.75rem] text-primary tracking-tight leading-tight mt-1">
                Side-by-Side Expenditure vs. Vulnerability
              </h1>

              <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl mt-1">
                Evaluating equity, hazard alignment, and contractor concentration across two
                Philippine local government units facing comparable flood hazards.
              </p>
            </div>

            <button
              type="button"
              className="px-space-md py-2 rounded bg-surface-container-lowest border border-outline-variant hover:bg-surface-container text-on-surface font-label-caps text-label-caps uppercase tracking-wider flex items-center gap-1.5 transition-colors self-start lg:self-auto"
            >
              <Download className="w-4 h-4 text-primary" /> Export Comparative Brief PDF
            </button>
          </div>
        </div>
      </section>

      {/* Locality Selector & Swap Strip */}
      <section className="w-full max-w-[1360px] mx-auto px-margin md:px-margin-desktop py-space-lg">
        <div className="p-space-md rounded bg-surface-container-lowest border border-hairline flex flex-col md:flex-row items-center justify-between gap-space-md shadow-sm">
          {/* Select A */}
          <div className="flex items-center gap-space-sm w-full md:w-auto">
            <span className="font-label-caps text-label-caps uppercase text-secondary font-bold">
              Benchmark LGU A:
            </span>
            <select
              value={locAKey}
              onChange={(e) => handleChangeA(e.target.value)}
              className="px-3 py-1.5 rounded bg-surface-container border border-hairline font-body-sm text-on-surface focus:outline-none focus:border-accent"
            >
              <option value="021500000">Tuguegarao City (Cagayan)</option>
              <option value="035413000">Masantol (Pampanga)</option>
              <option value="031405000">Calumpit (Bulacan)</option>
            </select>
          </div>

          {/* Swap Button */}
          <button
            type="button"
            onClick={handleSwap}
            className="p-2 rounded-full border border-hairline bg-surface-container-low hover:bg-surface-container text-primary hover:rotate-180 transition-all duration-300 shadow-sm"
            title="Swap Localities"
            aria-label="Swap Localities"
          >
            <ArrowLeftRight className="w-4 h-4" />
          </button>

          {/* Select B */}
          <div className="flex items-center gap-space-sm w-full md:w-auto">
            <span className="font-label-caps text-label-caps uppercase text-secondary font-bold">
              Benchmark LGU B:
            </span>
            <select
              value={locBKey}
              onChange={(e) => handleChangeB(e.target.value)}
              className="px-3 py-1.5 rounded bg-surface-container border border-hairline font-body-sm text-on-surface focus:outline-none focus:border-accent"
            >
              <option value="035413000">Masantol (Pampanga)</option>
              <option value="021500000">Tuguegarao City (Cagayan)</option>
              <option value="031405000">Calumpit (Bulacan)</option>
            </select>
          </div>
        </div>
      </section>

      {/* Side-by-Side Dual Dossier Columns */}
      <section className="w-full max-w-[1360px] mx-auto px-margin md:px-margin-desktop pb-space-2xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg items-start">
          <CompareColumn locality={locA} slotName="Locality A" />
          <CompareColumn locality={locB} slotName="Locality B" />
        </div>

        {/* Comparative Analytical Disparity Finding Card */}
        <div className="mt-space-xl p-space-lg bg-surface-container-lowest border border-hairline rounded flex flex-col gap-space-md shadow-sm">
          <div className="flex items-center gap-2 border-b border-hairline pb-space-xs">
            <AlertTriangle className="w-5 h-5 text-risk-critical-text" />
            <h3 className="font-serif font-bold text-headline-sm text-primary">
              Expenditure &amp; Vulnerability Variance Findings
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md font-body-sm">
            <div className="p-space-md rounded bg-surface-container-low border border-hairline flex flex-col gap-1">
              <span className="font-label-caps text-[0.625rem] text-secondary uppercase font-bold">
                Spend Asymmetry Ratio
              </span>
              <span className="font-serif font-bold text-headline-md text-primary">
                {spendRatio}x Multiplier
              </span>
              <p className="text-secondary text-[0.8125rem] mt-1">
                {locA.name} received {spendRatio}x more DPWH flood control funding than {locB.name}{' '}
                despite both experiencing over 80% flood inundation footprint.
              </p>
            </div>

            <div className="p-space-md rounded bg-surface-container-low border border-hairline flex flex-col gap-1">
              <span className="font-label-caps text-[0.625rem] text-secondary uppercase font-bold">
                Per-Capita Protection Delta
              </span>
              <span className="font-serif font-bold text-headline-md text-on-surface">
                ₱{Math.abs(locA.spend_per_capita - locB.spend_per_capita).toLocaleString()} / person
              </span>
              <p className="text-secondary text-[0.8125rem] mt-1">
                Net difference in public tax allocation per citizen between the two municipalities.
              </p>
            </div>

            <div className="p-space-md rounded bg-surface-container-low border border-hairline flex flex-col gap-1">
              <span className="font-label-caps text-[0.625rem] text-secondary uppercase font-bold">
                Accountability Conclusion
              </span>
              <span className="font-serif font-bold text-headline-md text-risk-critical-text">
                Severe Policy Misallocation
              </span>
              <p className="text-secondary text-[0.8125rem] mt-1">
                Public works funding exhibits high correlation with legislative seniority rather
                than empirical NOAH catastrophic hazard probability.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
