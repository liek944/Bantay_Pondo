import React from 'react';

interface SkeletonRowProps {
  columns?: number;
  className?: string;
}

export const SkeletonRow: React.FC<SkeletonRowProps> = ({ columns = 5, className = '' }) => {
  return (
    <tr className={`border-b border-hairline animate-pulse ${className}`}>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="py-3.5 px-4">
          <div
            className="h-4 bg-surface-container rounded"
            style={{ width: `${Math.max(40, 90 - i * 15)}%` }}
          />
        </td>
      ))}
    </tr>
  );
};
