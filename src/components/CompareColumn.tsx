import React from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import { RiskBadge, RiskLevel } from './RiskBadge';
import { MismatchScale } from './MismatchScale';

export interface LocalityCompareData {
  psgc_code: string;
  name: string;
  province: string;
  population: number;
  total_spend_php: number;
  spend_per_capita: number;
  hazard_exposure_pct: number;
  mismatch_score: number;
  risk_level: RiskLevel;
  major_projects_count: number;
}

interface CompareColumnProps {
  locality: LocalityCompareData;
  slotName: 'Locality A' | 'Locality B';
  className?: string;
}

export const CompareColumn: React.FC<CompareColumnProps> = ({
  locality,
  slotName,
  className = '',
}) => {
  const formatPeso = (val: number) => {
    if (val >= 1e9) return `₱${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `₱${(val / 1e6).toFixed(1)}M`;
    return `₱${val.toLocaleString()}`;
  };

  return (
    <div
      className={`p-space-lg bg-surface-container-lowest border border-hairline rounded flex flex-col gap-space-lg ${className}`}
    >
      {/* Slot header */}
      <div className="flex items-center justify-between border-b border-hairline pb-space-sm">
        <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
          {slotName}
        </span>
        <Link
          to={`/locality/${locality.psgc_code}`}
          className="inline-flex items-center gap-1 font-label-caps text-[0.6875rem] text-primary hover:underline uppercase"
        >
          View Full Dossier <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      {/* Locality Title & Province */}
      <div>
        <h3 className="font-headline-md text-headline-md font-bold text-primary">
          {locality.name}
        </h3>
        <p className="font-body-sm text-body-sm text-secondary">
          {locality.province} • PSGC: {locality.psgc_code}
        </p>
      </div>

      {/* Risk Assessment */}
      <div className="flex items-center justify-between bg-surface-container-low p-space-md rounded border border-hairline">
        <div className="flex flex-col">
          <span className="font-label-caps text-[0.625rem] uppercase text-secondary">
            Accountability Status
          </span>
          <span className="font-bold text-on-surface text-body-md mt-0.5">
            {locality.risk_level.toUpperCase()}
          </span>
        </div>
        <RiskBadge level={locality.risk_level} score={locality.mismatch_score} />
      </div>

      <MismatchScale score={locality.mismatch_score} />

      {/* Key Comparative Ledger Metrics */}
      <div className="grid grid-cols-2 gap-space-sm border-t border-hairline pt-space-md">
        <div className="p-space-sm rounded bg-surface-container-low">
          <span className="font-label-caps text-[0.625rem] text-secondary uppercase block">
            Total Spend
          </span>
          <span className="font-code-tabular font-bold text-primary text-body-md">
            {formatPeso(locality.total_spend_php)}
          </span>
        </div>
        <div className="p-space-sm rounded bg-surface-container-low">
          <span className="font-label-caps text-[0.625rem] text-secondary uppercase block">
            Spend Per Capita
          </span>
          <span className="font-code-tabular font-bold text-on-surface text-body-md">
            {formatPeso(locality.spend_per_capita)}
          </span>
        </div>
        <div className="p-space-sm rounded bg-surface-container-low">
          <span className="font-label-caps text-[0.625rem] text-secondary uppercase block">
            Hazard Exposure
          </span>
          <span className="font-code-tabular font-bold text-risk-500 text-body-md">
            {locality.hazard_exposure_pct.toFixed(1)}%
          </span>
        </div>
        <div className="p-space-sm rounded bg-surface-container-low">
          <span className="font-label-caps text-[0.625rem] text-secondary uppercase block">
            Audited Projects
          </span>
          <span className="font-code-tabular font-bold text-on-surface text-body-md">
            {locality.major_projects_count}
          </span>
        </div>
      </div>
    </div>
  );
};
