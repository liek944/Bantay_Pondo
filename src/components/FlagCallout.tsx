import React from 'react';
import { AlertTriangle, AlertCircle, Info, ShieldAlert } from 'lucide-react';

export interface AuditFlag {
  code: string;
  message: string;
  severity: 'low' | 'moderate' | 'high' | 'critical';
  details?: string;
  source?: string;
}

interface FlagCalloutProps {
  flag: AuditFlag;
  className?: string;
}

export const FlagCallout: React.FC<FlagCalloutProps> = ({ flag, className = '' }) => {
  const isCritical = flag.severity === 'critical' || flag.severity === 'high';

  return (
    <div
      className={`p-space-md rounded border flex items-start gap-space-md ${
        isCritical
          ? 'bg-risk-critical-bg border-risk-critical-border text-on-surface'
          : 'bg-risk-moderate-bg border-risk-moderate-border text-on-surface'
      } ${className}`}
    >
      <div className="shrink-0 mt-0.5">
        {flag.severity === 'critical' ? (
          <ShieldAlert className="w-5 h-5 text-risk-critical-text" />
        ) : flag.severity === 'high' ? (
          <AlertTriangle className="w-5 h-5 text-risk-high-text" />
        ) : flag.severity === 'moderate' ? (
          <AlertCircle className="w-5 h-5 text-risk-moderate-text" />
        ) : (
          <Info className="w-5 h-5 text-secondary" />
        )}
      </div>

      <div className="flex flex-col gap-1 w-full">
        <div className="flex flex-wrap items-center justify-between gap-space-xs">
          <span
            className={`font-code-tabular font-bold text-[0.75rem] uppercase tracking-wide ${
              isCritical ? 'text-risk-critical-text' : 'text-risk-moderate-text'
            }`}
          >
            {flag.code}
          </span>
          {flag.source && (
            <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
              {flag.source}
            </span>
          )}
        </div>

        <p className="font-body-sm text-body-sm font-medium leading-relaxed">{flag.message}</p>

        {flag.details && (
          <p className="font-body-sm text-[0.75rem] text-secondary leading-normal mt-0.5">
            {flag.details}
          </p>
        )}
      </div>
    </div>
  );
};
