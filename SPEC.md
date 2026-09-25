You are converting a Google Stitch UI export into a working frontend prototype
for "Bantay Pondo," a Philippine infrastructure accountability platform.

The exported HTML and image files are already in this directory. Do not assume
their structure — read them first.

=== PHASE 0: DISCOVERY (do this before writing any code) ===

Inspect every file in the directory and report back to me:

1. Every HTML file, and which screen from the design each one represents
2. How styles are loaded (Tailwind CDN? inline <style>? a stylesheet?) and the
   exact CDN URLs and versions
3. Every font family and icon set referenced
4. The exact hex values used, grouped by apparent role (background, surface,
   text, accent, data scale) — I need the real palette Stitch produced, not the
   one I specified
5. Every image file, its dimensions, and where it is referenced
6. Any absolute positioning, fixed pixel widths, or hardcoded heights that will
   break responsive layout
7. Markup blocks repeated across two or more screens — these become components

Print this as a short report. Then STOP and wait for my go-ahead.

=== TARGET STACK ===

- Vite + React 18 + TypeScript (strict)
- Tailwind CSS installed properly via PostCSS, NOT the CDN script
- React Router v6 for screen routing
- TanStack Query for all data fetching
- MapLibre GL JS for maps
- lucide-react for icons
- Zod for runtime validation of every API response

=== PHASE 1: SCAFFOLD AND FAITHFUL PORT ===

Non-negotiable rule for this phase: the rendered result must look identical to
the Stitch export. Do not improve the design, do not substitute colors, do not
adjust spacing to your taste. Any deviation you believe is necessary, raise with
me instead of applying it.

1. Scaffold Vite + React + TS in place without destroying the export — move the
   original HTML into /design-reference/ for side-by-side comparison
2. Install Tailwind locally. Extract every color, font size, font family,
   spacing value, and border radius from the export into tailwind.config.ts as
   named design tokens. Name them semantically:
   colors: canvas, surface, hairline, ink, ink-muted, accent
   colors.risk: 100 / 300 / 500 / 700 / 900 (the sand→maroon data scale)
   After this, no raw hex values may appear anywhere in /src. Enforce it.
3. Convert each HTML screen to a React route:
   / Landing / national map + search
   /locality/:psgcCode Locality dashboard
   /project/:contractId Project detail
   /contractor/:id Contractor profile
   /compare Compare view
   /methodology Methodology
4. Extract repeated markup into components under /src/components. At minimum
   expect: SearchInput, StatBlock, MismatchScale, HazardBars, ProjectRow,
   ProjectList, MapPanel, LayerToggle, OfficialStrip, DataTable, Breadcrumb,
   FlagCallout, SkeletonRow, EmptyState. Derive the actual list from your
   Phase 0 report, not from this list.
5. Replace Material Symbols with lucide-react equivalents. Keep visual weight
   and size the same.
6. Self-host the Google Fonts via @fontsource rather than CDN links.
7. Keep every exported image in /public/assets with its original filename.

=== PHASE 2: MOCK DATA LAYER (the important part) ===

Build /src/api as the only place the app touches data.

/src/api/types.ts — TypeScript types + Zod schemas for every response shape,
matching this contract exactly. Field names are final; do not rename them.

Locality { psgc_code, name, level, parent_name, province_name,
land_area_sqkm, population }
LocalityMetrics { psgc_code, year, hazard_exposure_pct, flood_pct,
landslide_pct, surge_pct, population_at_risk,
total_spend_php, spend_per_capita, spend_per_exposed_sqkm,
mismatch_score, raw_ratio, national_percentile,
computed_at }
Project { contract_id, title, description, implementing_office,
contractor_name, contractor_id, funding_source, budget_php,
contract_cost_php, start_date, target_completion_date,
physical_progress_pct, lat, lng, psgc_code, flags[] }
Flag { code, message, severity }
Contractor { id, normalized_name, total_contracts, total_value_php,
hhi_district_concentration, first_seen }
Official { id, name, position, district, term_start, term_end, party }
Paginated<T> { items: T[], total, page, page_size }

Every response envelope carries: { data, data_version, generated_at }

/src/api/client.ts — one fetch wrapper reading VITE_API_BASE_URL, validating
every response through its Zod schema, throwing typed errors.

/src/api/mocks/ — hand-authored fixture JSON covering these endpoints:
GET /v1/localities/search?q=
GET /v1/localities/{psgc_code}
GET /v1/localities/{psgc_code}/projects
GET /v1/localities/compare?a=&b=
GET /v1/projects/{contract_id}
GET /v1/contractors/{id}
GET /v1/rankings?metric=&level=&limit=
GET /v1/meta/datasets

Fixture requirements — the prototype is worthless if the data is bland:

- 12 real Philippine localities with correct PSGC codes and real names,
  spanning Metro Manila, a Visayas coastal municipality, a Mindanao inland
  municipality, and a Luzon province
- Mismatch scores spread across the full 0-100 range, including two clear
  underserved cases and one over-indexed case
- At least 60 projects, with realistic DPWH-style titles, peso budgets in the
  correct order of magnitude, and progress values including several stalled
  projects past their target completion date
- At least 4 projects carrying flags, covering different flag codes
- One contractor appearing across multiple localities so the concentration
  view has something to show
- Deliberate edge cases: a locality with zero projects, a project with null
  coordinates, a contractor name with inconsistent casing, a budget field
  arriving as a string

Wire mocks via MSW (Mock Service Worker) so the network layer is real. Toggle
with VITE_USE_MOCKS=true. When false, the identical calls hit VITE_API_BASE_URL
with zero code changes. Prove this by writing one test that runs the same
component against both.

=== PHASE 3: MAKE IT WORK ===

- Search: debounced typeahead against the search endpoint, keyboard navigable,
  Enter routes to the locality
- Locality dashboard: real loading skeletons, real error boundaries, real empty
  states. Project list virtualized if over 100 rows. Filters for year, funding
  source, and minimum budget, reflected in the URL query string so views are
  shareable
- Maps: MapLibre with a free raster basemap for now. Render mock GeoJSON for
  hazard polygons and project points from local fixtures. Structure the layer
  code so each layer's source can be swapped to a vector tile URL
  (/v1/tiles/{layer}/{z}/{x}/{y}.mvt) by changing only the source definition.
  Layer toggles control visibility, not remounts. Clicking a project marker
  opens its detail
- Compare: both localities in the URL as ?a=&b=, swap control, deep-linkable
- Every number formatted through shared utilities: peso amounts with proper
  thousands separators and abbreviated scale (₱1.2B), percentages to one
  decimal, dates as readable Philippine format. Tabular numerals on every
  aligned column

=== PHASE 4: QUALITY GATES ===

- Responsive down to 375px. The locality dashboard collapses per the mobile
  behavior: map becomes a 240px preview with Expand, project list becomes the
  primary scroll, hero row becomes a horizontal swipe strip
- Keyboard navigable throughout, visible focus rings, aria labels on every icon
  button, map has a table fallback for screen readers
- ESLint + Prettier + strict mypy-equivalent (tsc --noEmit) passing
- Vitest + Testing Library: a test per route rendering against mocks, plus tests
  for the formatting utilities and the Zod schemas against malformed input
- README documenting how to run with mocks, how to point at a real backend, and
  what is still stubbed

=== EXECUTION RULES ===
Stop after each phase and show me the result before continuing. Do not install
any library not listed above without asking. Do not invent design decisions —
where the export is ambiguous, ask. Commit at the end of each phase with a
descriptive message.

Start with Phase 0 now.
