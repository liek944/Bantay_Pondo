import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, Download, User } from 'lucide-react';

interface HeaderProps {
  onOpenSearch?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenSearch }) => {
  const location = useLocation();

  const navLinks = [
    { name: 'National Map & Search', path: '/' },
    { name: 'Locality Dossiers', path: '/locality/021500000' },
    { name: 'Contractor Registry', path: '/contractor/alpha-omega' },
    { name: 'Compare Localities', path: '/compare' },
    { name: 'Methodology & Data', path: '/methodology' },
  ];

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    if (path.startsWith('/locality')) return location.pathname.startsWith('/locality');
    if (path.startsWith('/contractor')) return location.pathname.startsWith('/contractor');
    if (path.startsWith('/compare')) return location.pathname.startsWith('/compare');
    if (path.startsWith('/methodology')) return location.pathname.startsWith('/methodology');
    return location.pathname === path;
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest border-b border-outline-variant/60 shadow-[0_1px_4px_rgba(0,0,0,0.03)]">
      {/* Consolidated Live Status Bar */}
      <div className="bg-surface-container-low/80 border-b border-outline-variant/40 px-margin-desktop py-space-xs text-on-surface-variant hidden md:block">
        <div className="max-w-[1440px] mx-auto flex items-center justify-between font-label-caps text-label-caps uppercase tracking-wider">
          <div className="flex items-center gap-space-md">
            <span className="flex items-center gap-1.5 text-primary font-bold">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              Live Registry Feed
            </span>
            <span className="text-outline-variant">|</span>
            <span>Q3 2024 DPWH, PhilGEPS &amp; COA Consolidated Records</span>
          </div>
          <div className="flex items-center gap-space-lg">
            <span className="font-code-tabular text-code-tabular normal-case text-on-surface">
              148,204 Projects Audited
            </span>
            <span className="text-outline-variant">|</span>
            <span className="text-on-surface-variant">Updated 4h ago</span>
          </div>
        </div>
      </div>

      {/* Main Bar */}
      <div className="h-16 max-w-[1440px] mx-auto px-margin md:px-margin-desktop flex items-center justify-between gap-space-lg">
        <div className="flex items-center gap-space-lg">
          <Link to="/" className="flex items-center gap-space-sm group">
            <img
              alt="Bantay Pondo Brand Emblem"
              className="h-8 w-auto object-contain"
              src="/assets/brand-emblem.svg"
            />
            <div className="flex flex-col">
              <span className="font-headline-sm text-headline-sm font-bold text-primary tracking-tight leading-none group-hover:text-primary-container transition-colors">
                Bantay Pondo
              </span>
              <span className="font-label-caps text-[0.625rem] text-secondary tracking-wider uppercase mt-0.5">
                Infrastructure Ledger
              </span>
            </div>
          </Link>

          <div className="h-7 w-px bg-outline-variant/50 hidden xl:block" />

          <nav className="hidden lg:flex items-center gap-space-lg font-body-sm text-body-sm">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`py-space-sm transition-colors ${
                    active
                      ? 'text-primary font-bold border-b-2 border-primary'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-space-md">
          <button
            onClick={onOpenSearch}
            className="hidden sm:flex items-center gap-space-sm px-space-md py-1.5 rounded bg-surface-container border border-outline-variant/80 text-on-surface-variant hover:text-on-surface hover:border-outline transition-colors"
            type="button"
            aria-label="Search Registry"
          >
            <Search className="w-4 h-4 text-on-surface-variant" />
            <span className="font-body-sm text-body-sm font-label-caps uppercase text-[0.6875rem]">
              Registry Search
            </span>
            <kbd className="font-code-tabular text-[0.625rem] bg-surface-container-lowest border border-outline-variant/80 px-1.5 py-0.5 rounded text-secondary font-bold ml-1">
              ⌘K
            </kbd>
          </button>

          <button
            type="button"
            className="hidden md:inline-flex items-center gap-1.5 px-space-md py-1.5 rounded border border-outline-variant text-on-surface hover:bg-surface-container-low transition-colors font-label-caps text-label-caps uppercase tracking-wider"
          >
            <Download className="w-4 h-4 text-primary" />
            Audit CSV
          </button>

          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
            <User className="w-4 h-4 text-on-primary" />
          </div>
        </div>
      </div>
    </header>
  );
};
