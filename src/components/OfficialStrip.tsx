import React from 'react';
import { UserCheck } from 'lucide-react';

export interface OfficialInfo {
  id: string;
  name: string;
  position: string;
  district?: string;
  term_start?: number | string;
  term_end?: number | string;
  party?: string;
}

interface OfficialStripProps {
  officials: OfficialInfo[];
  className?: string;
}

export const OfficialStrip: React.FC<OfficialStripProps> = ({ officials, className = '' }) => {
  return (
    <div
      className={`p-space-lg bg-surface-container-lowest border border-hairline rounded flex flex-col gap-space-md ${className}`}
    >
      <div className="flex items-center justify-between border-b border-hairline pb-space-xs">
        <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
          Incumbent Political Leadership &amp; Jurisdiction
        </span>
        <span className="font-code-tabular text-[0.6875rem] text-secondary">
          19th Congress / 2022–2025 Term
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-space-md">
        {officials.map((official) => (
          <div
            key={official.id}
            className="p-space-md rounded bg-surface-container-low border border-outline-variant/60 flex items-start gap-space-sm"
          >
            <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center shrink-0 text-primary mt-0.5">
              <UserCheck className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-label-caps text-[0.6875rem] uppercase text-secondary font-semibold">
                {official.position}
                {official.district ? ` • ${official.district}` : ''}
              </span>
              <span className="font-body-md font-bold text-on-surface leading-tight mt-0.5">
                {official.name}
              </span>
              <div className="flex items-center gap-1.5 mt-1 font-code-tabular text-[0.75rem] text-secondary">
                {official.party && <span>{official.party}</span>}
                {official.term_start && official.term_end && (
                  <>
                    <span>•</span>
                    <span>
                      {official.term_start}–{official.term_end}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
