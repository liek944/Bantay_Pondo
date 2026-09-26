import React from 'react';
import { Search, X } from 'lucide-react';

interface SearchInputProps {
  value: string;
  onChange: (val: string) => void;
  onClear?: () => void;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
  scopeChips?: string[];
  activeChip?: string;
  onSelectChip?: (chip: string) => void;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  onClear,
  placeholder = 'Search by locality, province, contractor, or PhilGEPS ID...',
  autoFocus = false,
  className = '',
  scopeChips,
  activeChip,
  onSelectChip,
}) => {
  return (
    <div className={`flex flex-col gap-space-sm w-full ${className}`}>
      <div className="relative flex items-center w-full">
        <Search className="absolute left-3.5 w-4 h-4 text-on-surface-variant pointer-events-none" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="w-full pl-10 pr-10 py-2.5 bg-surface-container-lowest border border-outline-variant rounded text-on-surface placeholder:text-secondary font-body-md text-body-md focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
        />
        {value ? (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-3 p-1 rounded hover:bg-surface-container text-secondary hover:text-on-surface transition-colors"
            aria-label="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        ) : (
          <span className="absolute right-3 font-code-tabular text-[0.6875rem] text-secondary border border-outline-variant/60 rounded px-1.5 py-0.5">
            ESC
          </span>
        )}
      </div>

      {scopeChips && scopeChips.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {scopeChips.map((chip) => {
            const isSelected = activeChip === chip;
            return (
              <button
                key={chip}
                type="button"
                onClick={() => onSelectChip?.(chip)}
                className={`px-2.5 py-1 rounded text-label-caps font-label-caps uppercase tracking-wider transition-colors ${
                  isSelected
                    ? 'bg-primary text-on-primary font-bold'
                    : 'bg-surface-container-low border border-outline-variant/70 text-on-surface-variant hover:border-outline hover:text-on-surface'
                }`}
              >
                {chip}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
