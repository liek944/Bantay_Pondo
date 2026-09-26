import React from 'react';

interface MismatchScaleProps {
  score: number;
  nationalPercentile?: number;
  className?: string;
}

export const MismatchScale: React.FC<MismatchScaleProps> = ({
  score,
  nationalPercentile,
  className = '',
}) => {
  // Clamp score between 0 and 100
  const clampedScore = Math.max(0, Math.min(100, score));

  return (
    <div className={`flex flex-col gap-1.5 w-full ${className}`}>
      <div className="flex items-center justify-between text-label-caps font-label-caps uppercase tracking-wider text-secondary">
        <span>Expenditure-Hazard Mismatch Score</span>
        <span className="font-code-tabular font-bold text-on-surface">
          {clampedScore}/100 {nationalPercentile ? `(P${nationalPercentile})` : ''}
        </span>
      </div>

      {/* 4 Segmented Spectrum Bars */}
      <div className="grid grid-cols-4 gap-1 h-3 rounded overflow-hidden p-0.5 bg-surface-container border border-hairline">
        {/* Low (0-25) */}
        <div
          className={`h-full rounded-sm transition-all ${
            clampedScore <= 25 ? 'bg-risk-100 ring-2 ring-primary ring-offset-1' : 'bg-risk-100/50'
          }`}
          title="Low Mismatch (0-25)"
        />
        {/* Moderate (26-50) */}
        <div
          className={`h-full rounded-sm transition-all ${
            clampedScore > 25 && clampedScore <= 50
              ? 'bg-risk-300 ring-2 ring-primary ring-offset-1'
              : 'bg-risk-300/50'
          }`}
          title="Moderate Mismatch (26-50)"
        />
        {/* High (51-75) */}
        <div
          className={`h-full rounded-sm transition-all ${
            clampedScore > 50 && clampedScore <= 75
              ? 'bg-risk-500 ring-2 ring-primary ring-offset-1'
              : 'bg-risk-500/50'
          }`}
          title="High Mismatch (51-75)"
        />
        {/* Critical (76-100) */}
        <div
          className={`h-full rounded-sm transition-all ${
            clampedScore > 75 ? 'bg-risk-700 ring-2 ring-primary ring-offset-1' : 'bg-risk-700/50'
          }`}
          title="Critical Mismatch (76-100)"
        />
      </div>

      <div className="flex justify-between font-label-caps text-[0.625rem] uppercase text-secondary">
        <span>0 Balanced</span>
        <span>25 Moderate</span>
        <span>50 High</span>
        <span className="text-risk-critical-text font-bold">100 Severe Anomaly</span>
      </div>
    </div>
  );
};
