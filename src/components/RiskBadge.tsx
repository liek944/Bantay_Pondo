import React from 'react';

export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical';

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  label?: string;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, score, label, className = '' }) => {
  const getStyles = () => {
    switch (level) {
      case 'low':
        return 'bg-risk-low-bg border-risk-low-border text-risk-low-text';
      case 'moderate':
        return 'bg-risk-moderate-bg border-risk-moderate-border text-risk-moderate-text';
      case 'high':
        return 'bg-risk-high-bg border-risk-high-border text-risk-high-text';
      case 'critical':
        return 'bg-risk-critical-bg border-risk-critical-border text-risk-critical-text font-bold';
    }
  };

  const displayLabel = label || `${level.toUpperCase()} ${score !== undefined ? `(${score})` : ''}`;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border font-label-caps text-label-caps uppercase tracking-wider ${getStyles()} ${className}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          level === 'low'
            ? 'bg-secondary'
            : level === 'moderate'
              ? 'bg-risk-300'
              : level === 'high'
                ? 'bg-risk-500'
                : 'bg-risk-700 animate-pulse'
        }`}
      />
      {displayLabel}
    </span>
  );
};
