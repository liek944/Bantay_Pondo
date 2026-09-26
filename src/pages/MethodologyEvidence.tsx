import React, { useState } from 'react';
import { Lock, UploadCloud, FileCheck, CheckCircle2, FileText } from 'lucide-react';
import { Breadcrumb, EvidenceCard, EvidenceItem } from '../components';

export const MethodologyEvidence: React.FC = () => {
  const [contractId, setContractId] = useState('');
  const [category, setCategory] = useState('Ghost Project / Non-existent Site');
  const [narrative, setNarrative] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const breadcrumbs = [
    { label: 'National Registry', path: '/' },
    { label: 'Whistleblower Vault & Methodology' },
  ];

  const recentEvidence: EvidenceItem = {
    id: 'ev-recent-1',
    title: 'Dry riverbank with zero concrete revetment toe wall',
    image_url: '/assets/evidence-riverbank.jpg',
    alt_text: 'Dry grassy Philippine riverbank showing raw untouched dirt and weeds.',
    timestamp: '2024-07-28 14:15:02 UTC',
    coordinates: '17.6312° N, 121.7340° E',
    sha256_hash: '9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b',
    description:
      'Contract 21BC0089 listed 100% completion on DPWH Transparency Portal. Field inspection shows raw unworked bank.',
    verified: true,
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="flex flex-col w-full bg-surface text-on-surface">
      {/* Top Banner */}
      <section className="w-full bg-surface-container-low border-b border-hairline px-margin md:px-margin-desktop py-space-xl">
        <div className="max-w-[1360px] mx-auto flex flex-col gap-space-md">
          <Breadcrumb items={breadcrumbs} />

          <div className="flex flex-col gap-1 max-w-3xl">
            <div className="flex items-center gap-space-sm">
              <Lock className="w-4 h-4 text-primary" />
              <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                End-to-End Encrypted Intake Channel
              </span>
            </div>

            <h1 className="font-serif font-bold text-headline-lg lg:text-[2.75rem] text-primary tracking-tight leading-tight mt-1">
              Whistleblower Vault &amp; Methodology
            </h1>

            <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl mt-1">
              Submit forensically notarized field evidence on ghost infrastructure, collapsed
              floodwalls, and contractor abandonment without exposing your identity.
            </p>
          </div>
        </div>
      </section>

      {/* Main 2-Column Layout */}
      <section className="max-w-[1360px] w-full mx-auto px-margin md:px-margin-desktop py-space-xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-start">
          {/* Left Column: Submission Form */}
          <div className="lg:col-span-7 bg-surface-container-lowest border border-hairline rounded p-space-lg flex flex-col gap-space-lg shadow-sm">
            {submitted ? (
              <div className="p-space-xl text-center flex flex-col items-center justify-center gap-space-md">
                <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center text-accent">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h3 className="font-serif font-bold text-headline-sm text-primary">
                  Evidence Cryptographically Sealed
                </h3>
                <p className="font-body-sm text-body-sm text-secondary max-w-md">
                  Your report has been hashed, encrypted using our newsroom PGP key, and queued for
                  forensic review. No client IP or browser fingerprint was recorded.
                </p>
                <div className="p-space-sm rounded bg-surface-container font-mono text-[0.6875rem] text-primary break-all">
                  Receipt: 7a8f9c0e2d3b4a5f6e7d8c9b0a1e2f3d4c5b6a7e8f9d0c1b
                </div>
                <button
                  type="button"
                  onClick={() => setSubmitted(false)}
                  className="mt-2 px-space-md py-1.5 rounded bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider hover:bg-primary-container"
                >
                  Submit Another Report
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-space-lg">
                <div className="flex items-center justify-between border-b border-hairline pb-space-xs">
                  <span className="font-label-caps text-label-caps uppercase text-secondary font-bold tracking-wider">
                    Forensic Intake Form
                  </span>
                  <span className="font-code-tabular text-[0.6875rem] text-accent font-bold">
                    Zero-Knowledge Encryption Enabled
                  </span>
                </div>

                {/* Field 1: Contract ID */}
                <div className="flex flex-col gap-1">
                  <label className="font-label-caps text-[0.6875rem] uppercase text-secondary font-bold">
                    DPWH Contract ID or Project Name
                  </label>
                  <input
                    type="text"
                    required
                    value={contractId}
                    onChange={(e) => setContractId(e.target.value)}
                    placeholder="e.g. 22BC0045 or Cagayan River Dike Ph III"
                    className="w-full px-3 py-2 rounded bg-surface-container border border-hairline text-body-sm focus:outline-none focus:border-accent"
                  />
                </div>

                {/* Field 2: Anomaly Category */}
                <div className="flex flex-col gap-1">
                  <label className="font-label-caps text-[0.6875rem] uppercase text-secondary font-bold">
                    Observed Anomaly Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded bg-surface-container border border-hairline text-body-sm focus:outline-none focus:border-accent"
                  >
                    <option>Ghost Project / Non-existent Site</option>
                    <option>Substandard Concrete &amp; Exposed Rebars</option>
                    <option>Negative Slippage / Abandoned Heavy Equipment</option>
                    <option>Premature Washout Post-Storm Surge</option>
                    <option>Disbursement Disparity vs Ground Truth</option>
                  </select>
                </div>

                {/* Field 3: Evidence Upload Mock Area */}
                <div className="flex flex-col gap-1">
                  <label className="font-label-caps text-[0.6875rem] uppercase text-secondary font-bold">
                    Photographic / Drone File Upload
                  </label>
                  <div className="border-2 border-dashed border-hairline-dark hover:border-accent p-space-xl rounded flex flex-col items-center justify-center text-center cursor-pointer transition-colors bg-surface-container-low/50">
                    <UploadCloud className="w-8 h-8 text-primary mb-2" />
                    <span className="font-body-sm font-semibold text-on-surface">
                      Drop high-resolution geotagged photographs or video
                    </span>
                    <span className="font-body-sm text-[0.75rem] text-secondary mt-1">
                      EXIF geolocation data is preserved; personal camera serials are stripped.
                    </span>
                  </div>
                </div>

                {/* Field 4: Narrative */}
                <div className="flex flex-col gap-1">
                  <label className="font-label-caps text-[0.6875rem] uppercase text-secondary font-bold">
                    Witness Narrative &amp; Ground Observations
                  </label>
                  <textarea
                    rows={4}
                    required
                    value={narrative}
                    onChange={(e) => setNarrative(e.target.value)}
                    placeholder="Describe exact physical condition, absence of equipment, dates of work stoppage, or discrepancies with official signboards..."
                    className="w-full px-3 py-2 rounded bg-surface-container border border-hairline text-body-sm focus:outline-none focus:border-accent"
                  />
                </div>

                {/* Submit button */}
                <button
                  type="submit"
                  className="w-full py-2.5 rounded bg-primary text-on-primary font-label-caps text-label-caps uppercase tracking-wider font-bold hover:bg-primary-container transition-colors shadow-sm"
                >
                  Seal &amp; Encrypt Evidence Submission
                </button>
              </form>
            )}
          </div>

          {/* Right Column: Recent Verified Evidence & Chain of Custody */}
          <div className="lg:col-span-5 flex flex-col gap-space-lg">
            {/* Chain of Custody Notice */}
            <div className="p-space-lg rounded bg-surface-container-lowest border border-hairline flex flex-col gap-space-sm shadow-sm">
              <div className="flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-accent" />
                <h3 className="font-serif font-bold text-headline-sm text-primary">
                  Chain of Custody Standard
                </h3>
              </div>
              <p className="font-body-sm text-body-sm text-secondary leading-relaxed">
                All uploaded materials undergo automated SHA-256 cryptographic hashing upon arrival.
                Records are verified against satellite SAR imagery (Sentinel-1 and Planet Labs)
                before incorporation into investigative dossiers.
              </p>
            </div>

            {/* Recent Verified Evidence Card */}
            <div className="flex flex-col gap-space-sm">
              <span className="font-label-caps text-label-caps uppercase text-secondary font-bold">
                Recently Notarized Field Inspection
              </span>
              <EvidenceCard item={recentEvidence} />
            </div>

            {/* Methodology Documentation Link */}
            <div className="p-space-lg rounded bg-surface-container-lowest border border-hairline flex flex-col gap-space-sm shadow-sm">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                <h3 className="font-serif font-bold text-headline-sm text-primary">
                  Mismatch Scoring Methodology
                </h3>
              </div>
              <p className="font-body-sm text-body-sm text-secondary leading-relaxed">
                Learn how Bantay Pondo correlates 100-year NOAH hazard raster pixels with DPWH
                physical expenditures and 2020 PSA census populations.
              </p>
              <div className="p-space-sm rounded bg-surface-container font-mono text-[0.75rem] text-primary">
                Mismatch = (Spend_Per_Capita / National_Baseline) / (Hazard_Exposure_Pct +
                &epsilon;)
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
