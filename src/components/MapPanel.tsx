import React, { useState } from 'react';
import { ZoomIn, ZoomOut, Maximize2, MapPin } from 'lucide-react';
import { LayerToggle, MapLayer } from './LayerToggle';

interface MapPinPoint {
  id: string;
  name: string;
  lat: number;
  lng: number;
  score?: number;
  category?: string;
  cost?: string;
}

interface MapPanelProps {
  title?: string;
  centerCoordinates?: string;
  zoomLevel?: number;
  heightClass?: string;
  pins?: MapPinPoint[];
  onSelectPin?: (pin: MapPinPoint) => void;
  className?: string;
}

export const MapPanel: React.FC<MapPanelProps> = ({
  title = 'National Infrastructure & Geohazard Viewport',
  centerCoordinates = '17.6132° N, 121.7270° E',
  zoomLevel = 12,
  heightClass = 'h-[540px]',
  pins = [],
  onSelectPin,
  className = '',
}) => {
  const [zoom, setZoom] = useState(zoomLevel);
  const [layers, setLayers] = useState<MapLayer[]>([
    { id: 'flood', name: 'NOAH Flood Hazard (100-yr)', active: true, color: 'bg-risk-500' },
    { id: 'landslide', name: 'MGB Landslide Susceptibility', active: false, color: 'bg-risk-300' },
    { id: 'projects', name: 'DPWH Flood Control Projects', active: true, color: 'bg-accent' },
    { id: 'spending', name: 'Per-Capita Allocation Heatmap', active: true, color: 'bg-primary' },
  ]);

  const toggleLayer = (id: string) => {
    setLayers((prev) => prev.map((l) => (l.id === id ? { ...l, active: !l.active } : l)));
  };

  return (
    <div
      className={`relative w-full ${heightClass} bg-canvas-sheet border border-hairline rounded overflow-hidden select-none ${className}`}
    >
      {/* Background Cartographic Vector / Grid */}
      <div className="absolute inset-0 bg-canvas-warm flex items-center justify-center overflow-hidden">
        {/* Subtle coordinate grid lines */}
        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-primary/10 via-transparent to-transparent pointer-events-none" />

        {/* SVG Topographic & Hazard Overlay simulation */}
        <svg
          className="w-full h-full object-cover pointer-events-none"
          viewBox="0 0 1000 600"
          preserveAspectRatio="xMidYMid slice"
        >
          <defs>
            <pattern id="cartoGrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path
                d="M 40 0 L 0 0 0 40"
                fill="none"
                stroke="currentColor"
                strokeWidth="0.5"
                className="text-hairline-dark"
              />
            </pattern>
          </defs>
          <rect width="1000" height="600" fill="url(#cartoGrid)" />

          {/* Contour Lines representing terrain & riverbank */}
          <path
            d="M 120,50 Q 250,150 400,240 T 700,320 T 950,550"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            strokeLinecap="round"
            className="text-primary/10"
          />
          <path
            d="M 120,50 Q 250,150 400,240 T 700,320 T 950,550"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray="4 2"
            className="text-accent"
          />

          {/* Simulated Flood Inundation Polygons (Visible if layer active) */}
          {layers.find((l) => l.id === 'flood')?.active && (
            <path
              d="M 320,180 Q 420,210 520,290 Q 610,380 480,420 Q 360,400 310,290 Z"
              fill="currentColor"
              className="text-risk-500/15 stroke-risk-500/40"
              strokeWidth="1.5"
            />
          )}

          {/* Landslide Polygon */}
          {layers.find((l) => l.id === 'landslide')?.active && (
            <path
              d="M 600,100 Q 750,120 780,240 Q 690,300 580,220 Z"
              fill="currentColor"
              className="text-risk-300/20 stroke-risk-300/50"
              strokeWidth="1.5"
            />
          )}
        </svg>

        {/* Project Pins */}
        <div className="absolute inset-0 pointer-events-auto">
          {pins.map((pin) => (
            <button
              key={pin.id}
              type="button"
              onClick={() => onSelectPin?.(pin)}
              className="absolute group transform -translate-x-1/2 -translate-y-1/2 transition-transform hover:scale-125 focus:outline-none"
              style={{
                left: `${((pin.lng - 120) / 5) * 100}%`,
                top: `${((19 - pin.lat) / 5) * 100}%`,
              }}
              title={`${pin.name} (${pin.cost || ''})`}
            >
              <div className="relative flex items-center justify-center">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
                <div className="w-6 h-6 rounded-full bg-accent border-2 border-surface flex items-center justify-center shadow-md">
                  <MapPin className="w-3.5 h-3.5 text-on-primary" />
                </div>
              </div>

              {/* Tooltip on hover */}
              <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full mb-1 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-surface-container-lowest border border-hairline shadow-md text-nowrap pointer-events-none z-30">
                <span className="font-bold text-on-surface text-[0.6875rem] block">{pin.name}</span>
                {pin.cost && (
                  <span className="font-code-tabular text-[0.625rem] text-accent block">
                    {pin.cost}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Top Header Overlay */}
      <div className="absolute top-3 left-3 right-3 flex items-start justify-between pointer-events-none z-20">
        <div className="p-space-sm px-space-md rounded bg-surface-container-lowest/95 backdrop-blur-sm border border-hairline shadow-sm pointer-events-auto">
          <h4 className="font-headline-sm text-[0.875rem] font-bold text-primary">{title}</h4>
          <span className="font-code-tabular text-[0.6875rem] text-secondary">
            {centerCoordinates} • Zoom {zoom}x
          </span>
        </div>

        {/* Layer Controls Dropdown */}
        <div className="pointer-events-auto max-w-xs">
          <LayerToggle layers={layers} onToggleLayer={toggleLayer} />
        </div>
      </div>

      {/* Map Zoom Controls */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-1 z-20">
        <button
          type="button"
          onClick={() => setZoom((z) => Math.min(18, z + 1))}
          className="w-8 h-8 rounded bg-surface-container-lowest border border-hairline flex items-center justify-center text-on-surface hover:bg-surface-container shadow-sm transition-colors"
          aria-label="Zoom in"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => setZoom((z) => Math.max(4, z - 1))}
          className="w-8 h-8 rounded bg-surface-container-lowest border border-hairline flex items-center justify-center text-on-surface hover:bg-surface-container shadow-sm transition-colors"
          aria-label="Zoom out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => setZoom(12)}
          className="w-8 h-8 rounded bg-surface-container-lowest border border-hairline flex items-center justify-center text-on-surface hover:bg-surface-container shadow-sm transition-colors"
          aria-label="Reset zoom"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Bottom Map Legend */}
      <div className="absolute bottom-4 left-4 p-space-xs px-space-md rounded bg-surface-container-lowest/95 backdrop-blur-sm border border-hairline text-[0.6875rem] font-label-caps uppercase tracking-wider text-secondary flex items-center gap-3 shadow-sm z-20">
        <span className="font-bold text-primary">Risk Spectrum:</span>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-risk-100" />
          <span>Low</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-risk-300" />
          <span>Mod</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-risk-500" />
          <span>High</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-risk-700" />
          <span>Critical</span>
        </div>
      </div>
    </div>
  );
};
