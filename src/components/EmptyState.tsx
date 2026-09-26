import React from 'react';
import { FolderX } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description = 'No matching infrastructure allocations or audit findings match your active filters.',
  actionText = 'Reset Query Filters',
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`p-space-2xl bg-surface-container-lowest border border-hairline rounded flex flex-col items-center justify-center text-center max-w-lg mx-auto my-space-lg ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-surface-container flex items-center justify-center text-secondary mb-space-md">
        <FolderX className="w-6 h-6" />
      </div>

      <h3 className="font-headline-sm text-headline-sm font-bold text-primary mb-1">{title}</h3>

      <p className="font-body-sm text-body-sm text-on-surface-variant max-w-sm mb-space-lg leading-relaxed">
        {description}
      </p>

      {onAction && (
        <button
          type="button"
          onClick={onAction}
          className="px-space-lg py-2 rounded bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider hover:bg-primary-container transition-colors shadow-sm"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
