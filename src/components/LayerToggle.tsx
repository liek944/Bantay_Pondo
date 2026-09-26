import React from 'react';
import { Layers, Eye, EyeOff } from 'lucide-react';

export interface MapLayer {
  id: string;
  name: string;
  active: boolean;
  color?: string;
  description?: string;
}

interface LayerToggleProps {
  layers: MapLayer[];
  onToggleLayer: (id: string) => void;
  className?: string;
}

export const LayerToggle: React.FC<LayerToggleProps> = ({
  layers,
  onToggleLayer,
  className = '',
}) => {
  return (
    <div
      className={`p-space-md rounded bg-surface-container-lowest/95 backdrop-blur-sm border border-hairline shadow-sm flex flex-col gap-2 ${className}`}
    >
      <div className="flex items-center gap-1.5 font-label-caps text-label-caps uppercase text-secondary font-bold border-b border-hairline pb-1.5">
        <Layers className="w-3.5 h-3.5 text-primary" />
        <span>Cartographic Layers</span>
      </div>

      <div className="flex flex-col gap-1">
        {layers.map((layer) => (
          <button
            key={layer.id}
            type="button"
            onClick={() => onToggleLayer(layer.id)}
            className={`flex items-center justify-between px-2 py-1.5 rounded text-left transition-colors font-body-sm text-[0.8125rem] ${
              layer.active
                ? 'bg-surface-container text-on-surface font-semibold'
                : 'text-secondary hover:text-on-surface hover:bg-surface-container-low'
            }`}
          >
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  layer.color || (layer.active ? 'bg-accent' : 'bg-outline-variant')
                }`}
              />
              <span>{layer.name}</span>
            </div>

            {layer.active ? (
              <Eye className="w-3.5 h-3.5 text-accent" />
            ) : (
              <EyeOff className="w-3.5 h-3.5 text-outline-variant" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
};
