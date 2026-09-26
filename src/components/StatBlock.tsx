import React from 'react';

interface StatBlockProps {
  label: string;
  value: string | number;
  subtext?: string;
  subtextColor?: 'default' | 'risk-low' | 'risk-moderate' | 'risk-high' | 'risk-critical';
  trend?: string;
  size?: 'normal' | 'large';
  className?: string;
}

export const StatBlock: React.FC<StatBlockProps> = ({
  label,
  value,
  subtext,
  subtextColor = 'default',
  trend,
  size = 'normal',
  className = '',
}) => {
  const getSubtextClass = () => {
    switch (subtextColor) {
      case 'risk-low':
        return 'text-risk-low-text';
      case 'risk-moderate':
        return 'text-risk-moderate-text font-medium';
      case 'risk-high':
        return 'text-risk-high-text font-medium';
      case 'risk-critical':
        return 'text-risk-critical-text font-bold';
      default:
        return 'text-secondary';
    }
  };

  return (
    <div
      className={`p-space-lg bg-surface-container-lowest border border-hairline rounded flex flex-col justify-between ${className}`}
    >
      <div className="flex items-center justify-between gap-space-sm mb-2">
        <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
          {label}
        </span>
        {trend && (
          <span className="font-code-tabular text-[0.6875rem] px-1.5 py-0.5 rounded bg-surface-container text-on-surface-variant">
            {trend}
          </span>
        )}
      </div>

      <div
        className={`font-serif font-bold text-primary tracking-tight leading-none ${
          size === 'large'
            ? 'text-display-figure-mobile lg:text-display-figure my-2'
            : 'text-headline-lg my-1'
        }`}
      >
        {value}
      </div>

      {subtext && (
        <div className={`font-body-sm text-body-sm mt-1 leading-snug ${getSubtextClass()}`}>
          {subtext}
        </div>
      )}
    </div>
  );
};
