import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { AlertTriangle, Download, Building, ExternalLink } from 'lucide-react';

import {
  Breadcrumb,
  StatBlock,
  RiskBadge,
  FlagCallout,
  EvidenceCard,
  AuditFlag,
  EvidenceItem,
} from '../components';

export const ProjectDetail: React.FC = () => {
  const { contractId = '22BC0045' } = useParams<{ contractId: string }>();

  const breadcrumbs = [
    { label: 'National Registry', path: '/' },
    { label: 'Cagayan', path: '/' },
    { label: 'Tuguegarao City', path: '/locality/021500000' },
    { label: `Contract ${contractId}` },
  ];

  const auditFlags: AuditFlag[] = [
    {
      code: 'COA-AAR-2023-OBS-14',
      message:
        'Exceeds Mandatory Termination Threshold under RA 9184 (Government Procurement Reform Act)',
      severity: 'critical',
      details:
        'Negative slippage of -54.2% documented by COA technical audit team as of December 31, 2023. Implementing office failed to issue Notice of Termination or enforce surety bond forfeitures.',
      source: 'COA Annual Audit Report 2023',
    },
    {
      code: 'SARO-DISBURSEMENT-MISMATCH',
      message: '₱71.25M Disbursed vs 45.8% Physical Accomplishment',
      severity: 'high',
      details:
        'Financial progress (50.0%) outpaces actual verified sheet-pile linear meters installed along the active riverbank sector by ₱12.4M.',
      source: 'PhilGEPS Electronic Cash Disbursement Ledger',
    },
    {
      code: 'SINGLE-BIDDER-COLLUSION',
      message: 'Disqualification of Sole Competitor at Technical Envelope Stage',
      severity: 'moderate',
      details:
        'Only two entities submitted bids. Competitor was disqualified over non-notarized equipment pledge, leaving winning contractor unopposed at 98.3% of ABC.',
      source: 'Bids and Awards Committee (BAC) Resolution 2022-04',
    },
  ];

  const evidencePhotos: EvidenceItem[] = [
    {
      id: 'ev-1',
      title: 'Forensic Drone Survey: Sheet Pile Flood Wall Sector B',
      image_url: '/assets/cagayan-sheet-pile.jpg',
      alt_text:
        'Forensic audit drone surveillance photo of uncompleted reinforced concrete sheet pile flood wall along riverbank.',
      timestamp: '2024-07-18 10:14:22 PHT',
      coordinates: '17.6189° N, 121.7212° E',
      sha256_hash: '8f7a9d3e4b1c2a5e6f7d8c9b0a1e2f3d4c5b6a7e8f9d0c1b2a3e4f5d6c7b8a9e',
      description:
        'Idle heavy machinery and incomplete reinforcement bars exposed to elements without active protective capping.',
      verified: true,
    },
    {
      id: 'ev-2',
      title: 'Monsoon Water Surge Washout of Unfinished Earthworks',
      image_url: '/assets/cagayan-washout.jpg',
      alt_text:
        'Civil engineering technical view documenting collapsed earthworks embankment along unfinished dike.',
      timestamp: '2024-08-02 16:45:00 PHT',
      coordinates: '17.6210° N, 121.7245° E',
      sha256_hash: '3e4b1c2a5e6f7d8c9b0a1e2f3d4c5b6a7e8f9d0c1b2a3e4f5d6c7b8a9e8f7a9d',
      description:
        'Severe embankment erosion post-Typhoon Carina due to absence of concrete revetment toe-protection.',
      verified: true,
    },
  ];

  return (
    <div className="flex flex-col w-full bg-surface text-on-surface">
      {/* Top Project Banner */}
      <section className="w-full bg-surface-container-low border-b border-hairline px-margin md:px-margin-desktop py-space-xl">
        <div className="max-w-[1360px] mx-auto flex flex-col gap-space-md">
          <Breadcrumb items={breadcrumbs} />

          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-space-lg">
            <div className="flex flex-col gap-1 max-w-3xl">
              <div className="flex items-center gap-space-sm flex-wrap">
                <span className="font-code-tabular font-bold text-primary text-body-sm">
                  DPWH Project ID: {contractId}
                </span>
                <span className="text-outline-variant">|</span>
                <span className="font-code-tabular text-[0.75rem] text-secondary">
                  PhilGEPS Reference: 8749201
                </span>
                <span className="text-outline-variant">|</span>
                <span className="font-label-caps text-[0.6875rem] uppercase text-secondary">
                  DPWH Cagayan 3rd District Engineering Office
                </span>
              </div>

              <h1 className="font-serif font-bold text-headline-lg lg:text-[2.5rem] text-primary tracking-tight leading-tight mt-1">
                Construction of River Dike along Cagayan River Phase III, Tuguegarao Sector
              </h1>

              <div className="flex items-center gap-2 mt-2">
                <RiskBadge level="critical" label="CRITICAL DELAY • 3 COA AUDIT FLAGS" />
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                className="px-space-md py-2 rounded bg-surface-container-lowest border border-outline-variant hover:bg-surface-container text-on-surface font-label-caps text-label-caps uppercase tracking-wider flex items-center gap-1.5 transition-colors"
              >
                <Download className="w-4 h-4 text-primary" /> PhilGEPS Contract PDF
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Financial & Physical Accomplishment Stat Blocks */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop py-space-xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md">
          <StatBlock
            label="Approved Budget (ABC)"
            value="₱145.0M"
            subtext="GAA 2022 Flood Control Line Item"
          />
          <StatBlock
            label="Contract Cost"
            value="₱142.5M"
            subtext="-1.72% Variance below Approved Budget"
            trend="Awarded Bid"
          />
          <StatBlock
            label="Physical Accomplishment"
            value="45.8%"
            subtext="Target Completion was November 30, 2023"
            subtextColor="risk-critical"
          />
          <StatBlock
            label="Negative Slippage"
            value="-54.2%"
            subtext="Exceeds 15% Legal Limit for Contract Default"
            subtextColor="risk-critical"
          />
        </div>
      </section>

      {/* Main 2-Column Ledger and Red Flags */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop pb-space-2xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-start">
          {/* Left Column: Procurement Ledger & Evidence Photos */}
          <div className="lg:col-span-7 flex flex-col gap-space-xl">
            {/* Procurement Ledger Details Table */}
            <div className="bg-surface-container-lowest border border-hairline rounded p-space-lg flex flex-col gap-space-md shadow-sm">
              <div className="flex items-center justify-between border-b border-hairline pb-space-xs">
                <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                  Procurement &amp; Execution Ledger
                </span>
                <span className="font-code-tabular text-[0.6875rem] text-secondary">
                  Contract Status: STALLED / DEFAULT
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md text-body-sm">
                <div className="p-space-sm rounded bg-surface-container-low flex flex-col">
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    Procurement Mode
                  </span>
                  <span className="font-bold text-on-surface mt-0.5">
                    Competitive Public Bidding
                  </span>
                </div>
                <div className="p-space-sm rounded bg-surface-container-low flex flex-col">
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    Contractor of Record
                  </span>
                  <Link
                    to="/contractor/alpha-omega"
                    className="font-bold text-primary hover:underline mt-0.5"
                  >
                    Alpha &amp; Omega Gen. Contractor &amp; Devt. Corp.
                  </Link>
                </div>
                <div className="p-space-sm rounded bg-surface-container-low flex flex-col">
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    Notice to Proceed (NTP)
                  </span>
                  <span className="font-code-tabular font-medium text-on-surface mt-0.5">
                    June 14, 2022
                  </span>
                </div>
                <div className="p-space-sm rounded bg-surface-container-low flex flex-col">
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    Original Contract Duration
                  </span>
                  <span className="font-code-tabular font-medium text-on-surface mt-0.5">
                    360 Calendar Days
                  </span>
                </div>
                <div className="p-space-sm rounded bg-surface-container-low flex flex-col">
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    Total Amount Disbursed
                  </span>
                  <span className="font-code-tabular font-bold text-primary mt-0.5">
                    ₱71,250,000.00 (50.0%)
                  </span>
                </div>
                <div className="p-space-sm rounded bg-surface-container-low flex flex-col">
                  <span className="font-label-caps text-[0.625rem] text-secondary uppercase">
                    Days Past Expiry
                  </span>
                  <span className="font-code-tabular font-bold text-risk-critical-text mt-0.5">
                    301 Days Overdue
                  </span>
                </div>
              </div>
            </div>

            {/* Field Forensic Evidence Cards */}
            <div className="flex flex-col gap-space-md">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-serif font-bold text-headline-sm text-primary">
                    Field Evidence &amp; Drone Surveys
                  </h3>
                  <p className="font-body-sm text-[0.8125rem] text-secondary">
                    Cryptographically notarized on-site photographic inspections.
                  </p>
                </div>
                <Link
                  to="/methodology"
                  className="font-label-caps text-label-caps uppercase text-primary font-bold hover:underline"
                >
                  Submit Drone Footage &rarr;
                </Link>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                {evidencePhotos.map((photo) => (
                  <EvidenceCard key={photo.id} item={photo} />
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: COA Audit Red Flags & Contractor Card */}
          <div className="lg:col-span-5 flex flex-col gap-space-lg">
            {/* Red Flags Container */}
            <div className="bg-surface-container-lowest border border-hairline rounded p-space-lg flex flex-col gap-space-md shadow-sm">
              <div className="flex items-center gap-2 border-b border-hairline pb-space-xs">
                <AlertTriangle className="w-5 h-5 text-risk-critical-text" />
                <h3 className="font-serif font-bold text-headline-sm text-primary">
                  Auditor-General &amp; Watchdog Red Flags
                </h3>
              </div>

              <div className="flex flex-col gap-space-md">
                {auditFlags.map((flag) => (
                  <FlagCallout key={flag.code} flag={flag} />
                ))}
              </div>
            </div>

            {/* Contractor Summary Card */}
            <div className="bg-surface-container-lowest border border-hairline rounded p-space-lg flex flex-col gap-space-sm shadow-sm">
              <div className="flex items-center gap-2">
                <Building className="w-4 h-4 text-primary" />
                <span className="font-label-caps text-label-caps uppercase text-secondary font-bold">
                  Awarded Contractor Dossier
                </span>
              </div>

              <h4 className="font-serif font-bold text-headline-sm text-primary">
                Alpha &amp; Omega Gen. Contractor &amp; Devt. Corp.
              </h4>
              <p className="font-body-sm text-body-sm text-secondary">
                Registered in Pasig City, Metro Manila. Holds 64% of all active flood control
                contracts in Cagayan 3rd District.
              </p>

              <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-hairline font-code-tabular text-[0.8125rem]">
                <div>
                  <span className="text-secondary text-[0.6875rem] block uppercase">
                    Total DPWH Contracts
                  </span>
                  <span className="font-bold text-on-surface">₱4.82 Billion</span>
                </div>
                <div>
                  <span className="text-secondary text-[0.6875rem] block uppercase">
                    District HHI
                  </span>
                  <span className="font-bold text-risk-critical-text">
                    0.428 (Extreme Monopoly)
                  </span>
                </div>
              </div>

              <Link
                to="/contractor/alpha-omega"
                className="mt-space-md px-space-md py-2 rounded bg-surface-container-low border border-hairline text-primary font-label-caps text-label-caps uppercase tracking-wider text-center hover:bg-surface-container transition-colors flex items-center justify-center gap-1 font-bold"
              >
                Inspect Contractor Profile <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
