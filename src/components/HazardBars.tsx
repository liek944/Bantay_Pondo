import React from 'react';

interface HazardExposure {
  label: string;
  percentage: number;
  description?: string;
  riskTier?: 'low' | 'moderate' | 'high' | 'critical';
}

interface HazardBarsProps {
  items: HazardExposure[];
  className?: string;
}

export const HazardBars: React.FC<HazardBarsProps> = ({ items, className = '' }) => {
  const getBarColor = (percentage: number, riskTier?: string) => {
    if (riskTier === 'critical' || percentage >= 75) return 'bg-risk-700';
    if (riskTier === 'high' || percentage >= 50) return 'bg-risk-500';
    if (riskTier === 'moderate' || percentage >= 25) return 'bg-risk-300';
    return 'bg-secondary';
  };

  return (
    <div
      className={`p-space-lg bg-surface-container-lowest border border-hairline rounded flex flex-col gap-space-md ${className}`}
    >
      <div className="flex items-center justify-between border-b border-hairline pb-space-xs">
        <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
          NOAH &amp; MGB Geohazard Exposure
        </span>
        <span className="font-code-tabular text-[0.6875rem] text-secondary">
          100-Year Return Flood / High Inundation
        </span>
      </div>

      <div className="flex flex-col gap-space-md">
        {items.map((item) => (
          <div key={item.label} className="flex flex-col gap-1">
            <div className="flex items-center justify-between font-body-sm text-body-sm">
              <span className="font-medium text-on-surface">{item.label}</span>
              <span className="font-code-tabular font-bold text-on-surface">
                {item.percentage.toFixed(1)}%
              </span>
            </div>

            <div className="w-full h-2 rounded bg-surface-container overflow-hidden">
              <div
                className={`h-full rounded transition-all duration-500 ${getBarColor(
                  item.percentage,
                  item.riskTier
                )}`}
                style={{ width: `${Math.min(100, Math.max(0, item.percentage))}%` }}
              />
            </div>

            {item.description && (
              <span className="font-body-sm text-[0.75rem] text-secondary">{item.description}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
