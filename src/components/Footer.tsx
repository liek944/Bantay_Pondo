import React from 'react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-surface-container-low border-t border-outline-variant/70">
      <div className="max-w-[1440px] mx-auto px-margin md:px-margin-desktop py-space-2xl">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-space-xl border-b border-outline-variant/50 pb-space-2xl">
          <div className="md:col-span-5 flex flex-col gap-space-md">
            <div className="flex items-center gap-space-sm">
              <img
                alt="Bantay Pondo Brand Emblem"
                className="h-7 w-auto object-contain grayscale opacity-85"
                src="/assets/brand-emblem.svg"
              />
              <span className="font-headline-sm text-headline-sm text-primary font-bold">
                Bantay Pondo
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
              An independent public-interest civic data project tracking Philippine government
              infrastructure allocations, contractor accountability, and hazard-zone public spending
              fidelity.
            </p>
            <div className="p-space-md rounded bg-surface-container-lowest border border-outline-variant/80 font-body-sm text-body-sm text-on-surface-variant">
              <strong className="text-on-surface font-semibold block mb-1 font-label-caps text-label-caps uppercase">
                Editorial Notice &amp; Scope
              </strong>
              Bantay Pondo is an independent public interest data repository. Absence of recorded
              project spend in high-risk zones indicates potential audit blind spots or reporting
              delays, not absence of vulnerability.
            </div>
          </div>

          <div className="md:col-span-3 flex flex-col gap-space-sm">
            <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
              Data Sources &amp; Ingestion
            </span>
            <ul className="space-y-2 font-body-sm text-body-sm text-on-surface-variant">
              <li>
                <a
                  className="hover:text-primary transition-colors underline decoration-outline-variant/60 underline-offset-4"
                  href="https://www.dpwh.gov.ph"
                  target="_blank"
                  rel="noreferrer"
                >
                  DPWH Transparency Portal
                </a>
              </li>
              <li>
                <a
                  className="hover:text-primary transition-colors underline decoration-outline-variant/60 underline-offset-4"
                  href="https://notices.philgeps.gov.ph"
                  target="_blank"
                  rel="noreferrer"
                >
                  PhilGEPS Contract Registers
                </a>
              </li>
              <li>
                <a
                  className="hover:text-primary transition-colors underline decoration-outline-variant/60 underline-offset-4"
                  href="https://www.coa.gov.ph"
                  target="_blank"
                  rel="noreferrer"
                >
                  COA Annual Audit Reports (AAR)
                </a>
              </li>
              <li>
                <a
                  className="hover:text-primary transition-colors underline decoration-outline-variant/60 underline-offset-4"
                  href="https://noah.up.edu.ph"
                  target="_blank"
                  rel="noreferrer"
                >
                  NOAH / PAGASA / MGB Hazard Maps
                </a>
              </li>
              <li>
                <a
                  className="hover:text-primary transition-colors underline decoration-outline-variant/60 underline-offset-4"
                  href="https://www.dbm.gov.ph"
                  target="_blank"
                  rel="noreferrer"
                >
                  DBM National Expenditure Program
                </a>
              </li>
            </ul>
          </div>

          <div className="md:col-span-2 flex flex-col gap-space-sm">
            <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
              Investigations
            </span>
            <ul className="space-y-2 font-body-sm text-body-sm text-on-surface-variant">
              <li>
                <Link className="hover:text-primary transition-colors" to="/locality/021500000">
                  Flood Control Audits
                </Link>
              </li>
              <li>
                <Link className="hover:text-primary transition-colors" to="/compare">
                  Barangay-Level Disparities
                </Link>
              </li>
              <li>
                <Link className="hover:text-primary transition-colors" to="/project/22BC0045">
                  Ghost Projects Database
                </Link>
              </li>
              <li>
                <Link className="hover:text-primary transition-colors" to="/contractor/alpha-omega">
                  Top 100 Contractors
                </Link>
              </li>
              <li>
                <Link className="hover:text-primary transition-colors" to="/methodology">
                  Red-Flag Risk Models
                </Link>
              </li>
            </ul>
          </div>

          <div className="md:col-span-2 flex flex-col gap-space-sm">
            <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
              Civic Access
            </span>
            <ul className="space-y-2 font-body-sm text-body-sm text-on-surface-variant">
              <li>
                <Link className="hover:text-primary transition-colors" to="/methodology">
                  Freedom of Information (FOI) API
                </Link>
              </li>
              <li>
                <Link className="hover:text-primary transition-colors" to="/methodology">
                  Open Data Philippines Export
                </Link>
              </li>
              <li>
                <Link className="hover:text-primary transition-colors" to="/methodology">
                  Research Methodology
                </Link>
              </li>
              <li>
                <a
                  className="hover:text-primary transition-colors"
                  href="https://github.com"
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub Repository
                </a>
              </li>
              <li>
                <Link className="hover:text-primary transition-colors" to="/methodology">
                  Whistleblower Channel
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-space-lg flex flex-col sm:flex-row items-center justify-between gap-space-md font-body-sm text-body-sm text-secondary">
          <p className="font-code-tabular text-code-tabular text-secondary">
            &copy; 2024 Bantay Pondo Initiative. Released under Creative Commons Attribution 4.0
            International (CC BY 4.0).
          </p>
          <div className="flex items-center gap-space-lg font-label-caps text-label-caps uppercase tracking-wider">
            <Link className="hover:text-on-surface transition-colors" to="/methodology">
              Privacy &amp; Terms
            </Link>
            <Link className="hover:text-on-surface transition-colors" to="/methodology">
              Audit Log
            </Link>
            <Link className="hover:text-on-surface transition-colors" to="/methodology">
              Contact Newsroom
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};
