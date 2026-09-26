import React from 'react';
import { Camera, MapPin, Hash, ShieldCheck } from 'lucide-react';

export interface EvidenceItem {
  id: string;
  title: string;
  image_url: string;
  alt_text: string;
  timestamp: string;
  coordinates: string;
  sha256_hash: string;
  description: string;
  verified?: boolean;
}

interface EvidenceCardProps {
  item: EvidenceItem;
  className?: string;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ item, className = '' }) => {
  return (
    <div
      className={`bg-surface-container-lowest border border-hairline rounded overflow-hidden flex flex-col ${className}`}
    >
      <div className="relative aspect-[16/9] w-full bg-surface-container overflow-hidden">
        <img
          src={item.image_url}
          alt={item.alt_text}
          className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
        />
        {item.verified && (
          <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-accent text-on-primary font-label-caps text-[0.625rem] uppercase tracking-wider flex items-center gap-1 shadow-sm">
            <ShieldCheck className="w-3 h-3" /> Forensically Verified
          </div>
        )}
      </div>

      <div className="p-space-md flex flex-col gap-space-sm">
        <h4 className="font-headline-sm text-[0.9375rem] font-bold text-primary">{item.title}</h4>
        <p className="font-body-sm text-[0.8125rem] text-on-surface-variant leading-relaxed">
          {item.description}
        </p>

        <div className="border-t border-hairline pt-space-xs mt-1 flex flex-col gap-1 font-code-tabular text-[0.6875rem] text-secondary">
          <div className="flex items-center gap-1.5">
            <Camera className="w-3 h-3 text-on-surface-variant shrink-0" />
            <span>{item.timestamp}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <MapPin className="w-3 h-3 text-on-surface-variant shrink-0" />
            <span>{item.coordinates}</span>
          </div>
          <div
            className="flex items-center gap-1.5 text-[0.625rem] truncate"
            title={item.sha256_hash}
          >
            <Hash className="w-3 h-3 text-on-surface-variant shrink-0" />
            <span className="truncate font-mono">SHA-256: {item.sha256_hash}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
