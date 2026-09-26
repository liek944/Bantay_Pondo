# Bantay Pondo — Implementation Progress

Project tracking across backend and frontend sequential delivery milestones specified in [SPEC.md](SPEC.md).

## Milestone Overview

### Backend (Milestones 1–9) — COMPLETED

| Milestone | Description | Status | Branch | Tests |
|:---:|---|:---:|---|:---:|
| 1 | Scaffolding, tooling, CI, docker-compose | **COMPLETED** | `milestone/01-repo-scaffold` | 8 passing |
| 2 | PostgreSQL + PostGIS schema, Alembic migrations | **COMPLETED** | `milestone/02-schema-migrations` | 14 passing |
| 3 | PSGC & NOAH hazard boundary ingestion | **COMPLETED** | `milestone/03-psgc-noah-ingestion` | 24 passing |
| 4 | DPWH project dataset ingestion & spatial join | **COMPLETED** | `milestone/04-dpwh-ingestion` | 32 passing |
| 5 | Scoring job with tests | **COMPLETED** | `milestone/05-scoring-job` | 41 passing |
| 6 | API endpoints, no tiles yet | **COMPLETED** | `milestone/06-api-endpoints` | 58 passing |
| 7 | Vector tiles | **COMPLETED** | `milestone/07-vector-tiles` | 69 passing |
| 8 | Contractor dedupe, procurement join, flags | **COMPLETED** | `milestone/08-contractor-flags` | 84 passing |
| 9 | CI, deployment compose, nginx, observability | **COMPLETED** | `milestone/09-ci-deployment-observability` | 103 passing |

---

### Frontend (Milestones 10–14 / Phases 0–4)

| Milestone / Phase | Description | Status | Branch | Tests |
|:---:|---|:---:|---|:---:|
| **10 / Phase 0** | **Discovery (Stitch export inspection & report)** | **COMPLETED** | `milestone/10-frontend-discovery` | Report verified |
| **11 / Phase 1** | **Scaffold Vite + React + TS & faithful port** | **COMPLETED** | `milestone/11-frontend-scaffold-port` | 13 passing |
| 12 / Phase 2 | Mock data layer (Zod schemas, MSW, fixtures) | Pending | `milestone/12-frontend-mock-data` | — |
| 13 / Phase 3 | Feature implementation (Search, Dashboards, MapLibre, Compare) | Pending | `milestone/13-frontend-make-it-work` | — |
| 14 / Phase 4 | Quality gates (Mobile responsive 375px, a11y, vitest, README) | Pending | `milestone/14-frontend-quality-gates` | — |


---

## Milestone 10 / Phase 0 Details: Discovery

- **Status**: Complete
- **Branch**: `milestone/10-frontend-discovery`
- **Completed On**: 2026-09-25

### Deliverables & Findings:

1. **Screen Inventory (7 HTML files inspected)**:
   - `05_national_map_search/code.html`: Route `/` (National Map & Search landing view, search drawer, audit rankings table)
   - `02_locality_dossier_tuguegarao_city/code.html`: Route `/locality/:psgcCode` (Locality audit profile, metrics, hazard breakdown, local leadership, projects)
   - `06_project_detail_cagayan_river_dike_phase_iii/code.html`: Route `/project/:contractId` (Project detail, contractor, progress, COA flags, milestone ledger, drone surveys)
   - `04_contractor_dossier_alpha_omega/code.html`: Route `/contractor/:id` (Contractor profile, aggregate metrics, district concentration, red flags, contracts table)
   - `03_compare_localities_system_states/code.html`: Route `/compare` (Side-by-side locality comparison ledger, swap control, empty/loading states)
   - `01_whistleblower_and_evidence/code.html`: Route `/methodology` / Whistleblower vault (Encrypted submission form, evidence cards, cryptographic hashing)
   - `07_brand_emblem/code.html` & `code.svg`: Brand emblem SVG (240x48 vector mark: archival seal, radar balance motif, Newsreader wordmark)

2. **Style Loading & Tailwind CDN**:
   - CDN Script: `<script src="https://cdn.tailwindcss.com"></script>` (Tailwind Play standalone runtime without pinned version).
   - Config: Inline `<script id="tailwind-config">tailwind.config = { ... }</script>` across screens 01–06. Screens 02–06 are semantically identical; screen 01 defines 3 additional tokens (`secondary-container`, `tertiary-fixed`, `on-tertiary-container`).
   - Base Layer: Common inline `<style>` resetting margins, disabling overscroll, and hiding scrollbars.
   - Screen 07 uses pure inline CSS without Tailwind.

3. **Font Families & Icon Sets**:
   - Google Fonts: `Newsreader` (Headings & display figures) and `Inter` (System UI, metadata, tabular numbers).
   - Icon Set: Google Material Symbols Outlined (51 unique icons identified across screens). Target stack will map these to `lucide-react`.

4. **Real Color Palette Produced by Stitch**:
   - Canvas/Background: `#FAF8F5` (warm newsroom cream), `#FFF8F3`, `#FFFFFF` (white surface card), `#F9F2ED`, `#F3EDE7`.
   - Structural Borders: `#E2DDD5` (1px hairline), `#D8D2C7` (interactive border), `#C0C8C7`.
   - Ink & Text: `#1A1815` (near-black carbon ink), `#1D1B18`, `#404848`, `#68625B` (secondary metadata).
   - Editorial Teal Accent: `#0F5C5C` (primary active teal), `#002B2B` (deepest teal), `#0A4242` (button hover), `#E6F0F0` (soft focus wash).
   - Diagnostic Data Scale:
     - Low (0–25): bg `#FAF5EE`, border `#E8D5B7`, text `#68625B`.
     - Moderate (26–50): bg `#FDF6EC`, border `#D89B4A`, text `#7A4C10`.
     - High (51–75): bg `#FBF0ED`, border `#B4472F`, text `#B4472F`.
     - Critical (76–100): bg `#F7ECEB`, border `#7A2418`, text `#7A2418`.
   - Cartographic Tints: `#EEE6DE`, `#F4EDE6`, `#F8F2EB`.

5. **Image Inventory & References**:
   - 15 image files in `stitch/screens/` (screenshots, thumbnails, and `code.svg`).
   - 5 external image assets identified in markup: Brand Emblem logo (used in all headers and footers), riverbank evidence photo (Screen 01), sheet pile flood wall photo (Screen 06), drone washout photo (Screen 06), and satellite aerial map background (Screen 06).

6. **Responsive Layout Constraints**:
   - Fixed top header bar (`fixed top-0`) across all screens.
   - Hardcoded heights: Map containers (`h-[580px]`, `h-[620px]`, `h-[540px]`), contractor network (`h-[460px]`).
   - Fixed widths: Map search drawer (`sm:w-[430px]`), desktop grids (`max-w-[1440px]`, `max-w-[1360px]`).
   - Absolute positioning: Map controls and status callout strips.

7. **Repeated Markup Blocks / Extracted Components**:
   - `Header` / `NavBar`
   - `Footer`
   - `SearchInput`
   - `StatBlock`
   - `MismatchScale` / `RiskBadge`
   - `HazardBars`
   - `OfficialStrip`
   - `Breadcrumb`
   - `DataTable`
   - `ProjectRow` / `ProjectList`
   - `FlagCallout`
   - `MapPanel` / `LayerToggle`
   - `CompareColumn`
   - `EvidenceCard`

### Definition of Done Checklist:
- [x] All 7 HTML export files and metadata inspected.
- [x] Style loading mechanisms, exact CDN URLs, and configs documented.
- [x] Font families and complete Material Symbols icon catalog identified.
- [x] Real hex palette extracted and grouped by apparent visual role.
- [x] Image assets and dimensions cataloged.
- [x] Responsive layout bottlenecks identified.
- [x] Shared markup blocks mapped to reusable components.
- [x] `PROGRESS.md` updated.
- [x] Discovery report generated and execution paused for user go-ahead.

---

## Milestone 11 / Phase 1 Details: Scaffold Vite + React + TS & Faithful Port

- **Status**: Complete
- **Branch**: `milestone/11-frontend-scaffold-port`
- **Completed On**: 2026-09-26
- **Test Results**: 13 passed (across 3 test suites: components, routes, no-raw-hex)

### Deliverables:
1. **Target Stack In Place**:
   - Scaffolded Vite + React 18 + TypeScript (strict mode enabled with `"noUnusedLocals"`, `"noUnusedParameters"`, `"strict"`).
   - Tailwind CSS installed locally with PostCSS and Autoprefixer (no CDN scripts).
   - React Router v6 configuring all 6 target routes.
   - TanStack Query v5 integrated with QueryClientProvider.
   - MapLibre GL JS and Lucide React installed.
   - `@fontsource/newsreader` and `@fontsource/inter` installed and self-hosted (zero Google Fonts CDN links).
   - Moved all original HTML exports and screenshots to `/design-reference/` for side-by-side verification.
   - Preserved all exported visual assets in `/public/assets` with original and descriptive filenames.

2. **Semantic Design Token Extraction (`tailwind.config.ts`)**:
   - Named semantic color tokens: `canvas`, `surface`, `hairline`, `ink`, `ink-muted`, `accent`.
   - Five-tier diagnostic data scale: `risk.100` (sand ochre), `risk.300` (regulatory amber), `risk.500` (investigative rust), `risk.700` (civic maroon), `risk.900` (deepest maroon).
   - Exact Stitch compatibility tokens: `primary`, `secondary`, `tertiary`, `surface-container-*`, `outline-variant`.
   - Typography tokens matching broadsheet specifications: `Newsreader` (display figures and headlines) and `Inter` (system interface and tabular lining numerals).
   - **Enforced Zero Raw Hex Values**: Automated test `src/test/no-raw-hex.test.ts` scanning `/src` confirms 0 raw hex literals exist in any source file.

3. **Reusable Components Extracted (`src/components/`)**:
   - `Header`: Live registry feed ticker, brand emblem mark, route navigation, quick search trigger (`⌘K`), audit CSV action, user profile.
   - `Footer`: Mission statement, editorial scope notice, data sources & ingestion links, investigations, civic access, and CC BY 4.0 license attribution.
   - `SearchInput`: Typeahead registry search with clear trigger, ESC badge, and scope chips (`All Localities`, `Critical Anomaly`, `High Inundation`, `Flood Hotspots`).
   - `StatBlock`: Kicker category, large display figure in `Newsreader`, subtext with risk-spectrum semantic highlighting.
   - `RiskBadge`: 4-tier diagnostic risk badge with animated indicators (`low`, `moderate`, `high`, `critical`).
   - `MismatchScale`: 4-segment visual spectrum displaying mismatch score (0-100) and national percentile.
   - `HazardBars`: NOAH 100-year flood inundation, MGB landslide, and storm surge exposure breakdown.
   - `OfficialStrip`: Political leadership accountability cards for Representative, City Mayor, and Provincial Governor.
   - `Breadcrumb`: Accessible broadsheet trail with chevron dividers.
   - `DataTable`: Generic high-density tabular data ledger with sticky headers and right-aligned lining numerals.
   - `ProjectRow` / `ProjectList`: DPWH infrastructure contracts table with progress bars, COA flag markers, and contractor links.
   - `FlagCallout`: Critical, high, and moderate COA audit observation callouts.
   - `MapPanel` / `LayerToggle`: Topographic vector map viewport with layer toggles (NOAH Flood, MGB Landslide, DPWH Projects, Per-Capita Heatmap), zoom controls, and risk legend.
   - `CompareColumn`: Comparative municipality dossier column for side-by-side audit benchmarking.
   - `EvidenceCard`: Notarized on-site inspection photo card with timestamp, GPS coordinates, and SHA-256 hash.
   - `SkeletonRow`: Editorial breathing tone loading state.
   - `EmptyState`: Zero-result search dossier card with query reset action.

4. **Complete Route Switchboard (`src/pages/`)**:
   - `/`: `NationalMapSearch` (Landing, mission hero, interactive map drawer, quarterly audit rankings).
   - `/locality/:psgcCode`: `LocalityDossier` (Tuguegarao City audit profile, NOAH hazard breakdown, leadership strip, flood control projects ledger).
   - `/project/:contractId`: `ProjectDetail` (Contract 22BC0045, procurement details, negative slippage alert, field evidence photos, COA observations).
   - `/contractor/:id`: `ContractorDossier` (Alpha & Omega profile, district concentration HHI 0.428, single-bidder patterns, awards ledger).
   - `/compare`: `CompareLocalities` (Side-by-side comparison between Tuguegarao City and Masantol with swap control and disparity findings).
   - `/methodology`: `MethodologyEvidence` (Cryptographic whistleblower vault, PGP encryption intake form, chain of custody standard).

### Definition of Done Checklist:
- [x] `tsc --noEmit` passes with 0 errors (strict mode enabled).
- [x] `eslint` passes with 0 errors and 0 warnings.
- [x] `prettier --check` passes with 0 errors.
- [x] `vitest run` passes with 13 passing tests.
- [x] Zero raw hex colors in `/src` (verified by automated test).
- [x] Original HTML exports moved to `/design-reference/` for side-by-side verification.
- [x] Google Fonts self-hosted via `@fontsource` with zero CDN links.
- [x] Production bundle verified via `npm run build`.
- [x] `PROGRESS.md` updated.
- [x] Ready to commit on branch `milestone/11-frontend-scaffold-port`.

