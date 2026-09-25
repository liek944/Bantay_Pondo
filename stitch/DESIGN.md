---
name: Investigative Public Ledger
colors:
  surface: '#fff8f3'
  surface-dim: '#dfd9d4'
  surface-bright: '#fff8f3'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f9f2ed'
  surface-container: '#f3ede7'
  surface-container-high: '#ede7e2'
  surface-container-highest: '#e8e1dc'
  on-surface: '#1d1b18'
  on-surface-variant: '#404848'
  inverse-surface: '#33302d'
  inverse-on-surface: '#f6f0ea'
  outline: '#707978'
  outline-variant: '#c0c8c7'
  surface-tint: '#366666'
  primary: '#002b2b'
  on-primary: '#ffffff'
  primary-container: '#0a4242'
  on-primary-container: '#7daead'
  inverse-primary: '#9ed0cf'
  secondary: '#635d57'
  on-secondary: '#ffffff'
  secondary-container: '#eae1d8'
  on-secondary-container: '#69635c'
  tertiary: '#510501'
  on-tertiary: '#ffffff'
  tertiary-container: '#701d12'
  on-tertiary-container: '#f98370'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b9eceb'
  primary-fixed-dim: '#9ed0cf'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#1b4e4e'
  secondary-fixed: '#eae1d8'
  secondary-fixed-dim: '#cec5bd'
  on-secondary-fixed: '#1f1b16'
  on-secondary-fixed-variant: '#4b463f'
  tertiary-fixed: '#ffdad4'
  tertiary-fixed-dim: '#ffb4a7'
  on-tertiary-fixed: '#400100'
  on-tertiary-fixed-variant: '#80281c'
  background: '#fff8f3'
  on-background: '#1d1b18'
  surface-variant: '#e8e1dc'
typography:
  display-figure:
    fontFamily: Newsreader
    fontSize: 3.75rem
    fontWeight: '500'
    lineHeight: '1.05'
    letterSpacing: -0.025em
  display-figure-mobile:
    fontFamily: Newsreader
    fontSize: 2.5rem
    fontWeight: '500'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 2.25rem
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 1.75rem
    fontWeight: '600'
    lineHeight: '1.25'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Newsreader
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Newsreader
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Newsreader
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: '1.75'
  body-md:
    fontFamily: Inter
    fontSize: 0.9375rem
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: '1.5'
  data-metric:
    fontFamily: Inter
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  label-caps:
    fontFamily: Inter
    fontSize: 0.6875rem
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: 0.08em
  code-tabular:
    fontFamily: Inter
    fontSize: 0.8125rem
    fontWeight: '500'
    lineHeight: '1.4'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-desktop: 1.75rem
  margin: 1rem
  margin-tablet: 2rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.875rem
  space-lg: 1.5rem
  space-xl: 2.5rem
  space-2xl: 4rem
---

## Brand & Style

The design system is constructed for rigorous public interest journalism and civic expenditure accountability. Designed to evoke the authority and precision of investigative outlets like *ProPublica*, *The Upshot*, and the *International Consortium of Investigative Journalists (ICIJ)*, it bridges classical broadsheet editorial elegance with utilitarian, high-density civic data reporting.

The visual style embraces an editorial-minimalist architecture: crisp ink, archival warm-paper backdrops, fine hairline boundaries, and unyielding typographic hierarchy. It intentionally rejects corporate software tropes—avoiding saturated decorative gradients, floating drop shadows, playful organic shapes, or frivolous illustrations. The user interface functions as an open legal and financial dossier: objective, unimpeachable, dense yet calm, treating citizens, watchdogs, and investigative reporters with civic seriousness.

## Colors

The palette reproduces the tactile contrast of high-grade newsprint and legal registries, accented by precise state accountability indicators.

- **Foundational Surfaces:** 
  - Canvas Base: `#FAF8F5` (warm newsroom cream), delivering low eye-fatigue over long investigative reads.
  - Surface Card/Panel: `#FFFFFF` (pure white sheet), deployed for data grids, primary dossiers, and query tables.
  - Borders & Hairlines: Structural dividers use `#E2DDD5`, with a deeper `#D8D2C7` for interactive borders and table heads.

- **Typography & Monochrome:**
  - Primary Readership / Ink: `#1A1815` (near-black carbon), rendering headlines, metrics, and report bodies with severe contrast.
  - Secondary Context / Metadata: `#68625B` for column descriptors, timestamps, and legal disclaimers.
  - Tertiary / Subdued: `#8C847A` for inactive states, disabled affordances, and non-essential schema markers.

- **Editorial Teal (Interactive & Civic Authority):**
  - Primary Active: `#0F5C5C` (deep archival sea teal).
  - Hover & Pressed Accent: `#0A4242` (seed tone, resolute dense teal).
  - Soft Highlight Wash: `#E6F0F0` for active row state selections, tag backdrops, and active focus envelopes.

- **Investigative Risk & Anomaly Spectrum (Reserved Exclusively for Data Diagnostics):**
  - Low Variance / Pass: `#E8D5B7` (sand ochre).
  - Moderate Anomaly: `#D89B4A` (warm regulatory amber).
  - High Discrepancy: `#B4472F` (investigative rust).
  - Critical Mismatch / Alert: `#7A2418` (deep civic maroon).

The anomaly colors must never be applied to generic interface ornamentation or non-diagnostic elements; they are strictly diagnostic data-weight tokens.

## Typography

Typography establishes an investigative cadence. The system balances literary editorial gravity with structured utilitarian scannability.

- **Headline & Numeric Anchor (`Newsreader`):** Used for analytical broadsheet headings, article titles, narrative intros, and massive callout figures (e.g., total unliquidated pork barrel balances, project delay counts). `Newsreader` conveys legal weight, high-grade scholarship, and archival responsibility. Numbers in this family must enable proportional lining numerals.
- **System Interface & Metadata (`Inter`):** Drives application navigation, analytical tables, chart axes, contract statuses, inputs, and form controls. Provides neutral, high-density legibility without distraction.
- **Tabular Data Treatment:** All financial allocations, Philippine Standard Geographic Codes (PSGC), PhilGEPS IDs, coordinates, and percentage variances must enforce `font-feature-settings: "tnum" 1, "zero" 1` via CSS on the `Inter` body or tabular classes to preserve column alignment across stacked balances and ledger rows.
- **Section Kicker / Metadata Caps:** `label-caps` must be rendered in uppercase with wide tracking (`0.08em`) to act as institutional categorizers above major data panels.

## Layout & Spacing

The layout model is anchored to an asymmetrical, editorial broadsheet column structure optimized for parallel narrative-plus-data consumption.

- **Grid Framework:** A 12-column dynamic desktop grid with a maximum content canvas of `1360px`. Major investigative dossier pages follow an intentional 8:4 or 7:5 ratio:
  - The wider column holds the investigative narrative, detailed audit trail tables, and multi-year comparative spending charts.
  - The narrower rail holds the key performance indicators, regional geolocation preview, contractor dispute history, and timeline sparklines.
- **Structural Rhythms:**
  - `space-xs` (4px) and `space-sm` (8px) govern tight metric pairings, chip insets, and icon-to-label gaps.
  - `space-md` (14px) establishes table cell vertical padding and interactive control enclosures.
  - `space-lg` (24px) separates logical blocks within a dossier panel.
  - `space-xl` (40px) and `space-2xl` (64px) provide generous whitespace around massive key audit metrics, creating intentional pauses that allow staggering spending sums to register emotionally with the reader.
- **Responsive Adaptations:**
  - *Mobile (< 640px):* Collapses to a 4-column single-stream ledger. Rails drop below primary summaries. Interactive split maps convert to toggleable views (Map vs. List). Margins compress to `margin` (16px).
  - *Tablet (640px - 1024px):* 8-column layout. Split data views stack metric cards in 2x2 grids above main data tables.
  - *Desktop (> 1024px):* Full 12-column editorial canvas. Fixed sticky sidebar query anchors and synchronized cross-filtering timelines.

## Elevation & Depth

This design system completely repudiates floating blurred drop shadows, multi-layered skeuomorphism, and translucent decorative glassmorphism. Authority is communicated through paper-layered planar structures, precise hairline borders, and value-based contrast.

- **Flat Editorial Surface Separation:** Depth is produced by layering pure white (`#FFFFFF`) data dossiers atop the warm newsprint canvas (`#FAF8F5`). 
- **1px Hairline Structural Enclosures:** Every card, data cluster, table frame, and split map viewport is bounded by a crisp 1px solid border (`#E2DDD5`).
- **Focus & Selection Elevation:** When an element is focused, hovered, or actively filtered, depth is registered strictly via a 1px tint shift to `#0F5C5C` or `#D8D2C7`, supported internally by the subtle `#E6F0F0` light wash. 
- **Sticky Dossier Layers:** Navigational headers and pinned chart timeline summaries stick during long investigative scrolls using a crisp bottom hairline divider (`#D8D2C7`) with zero blur shadows.

## Shapes

In harmony with a serious civic newsroom aesthetic, shapes are restrained, architectural, and compact. 

The roundedness token is locked to `1` (`0.25rem` / `4px`). This slight softening prevents the UI from feeling hostile while preserving the disciplined look of ledger index cards, official gazettes, and printed registry slips.

- **Components, Inputs, Buttons, & Data Chips:** Strictly `4px` corner radius.
- **Card Containers & Modal Dossiers:** Strictly `4px` corner radius. Under no circumstances should `8px`, `16px`, or pill-shaped cards be deployed.
- **Data Gauges & Visualizations:** Semicircular progress gauges and sparklines use crisp terminal caps. Segmented progress blocks rely on precise rectangle segments separated by 1.5px gaps rather than continuous soft-pill tracks.

## Components

### Buttons & Actions
- **Primary Civic Action:** Background `#0F5C5C`, text `#FFFFFF`, border 1px solid `#0A4242`, radius 4px, font `Inter` 13px weight 600. Hover: `#0A4242`.
- **Secondary Ledger Action:** Background `#FFFFFF`, text `#1A1815`, border 1px solid `#D8D2C7`, radius 4px. Hover: background `#FAF8F5`, border `#68625B`.
- **Ghost Action / Text Link:** Background transparent, text `#0F5C5C`, weight 600, underline with 2px offset. Hover: text `#0A4242`.

### Anomaly Chips & Risk Badges
- Compact markers displaying budget disparity risk levels (`Low`, `Moderate`, `High`, `Critical`).
- Structure: 4px radius, padding `2px 8px`, `label-caps` typography, 1px perimeter border.
- Styling Rules:
  - *Low:* Background `#FAF5EE`, border `#E8D5B7`, text `#68625B`.
  - *Moderate:* Background `#FDF6EC`, border `#D89B4A`, text `#7A4C10`.
  - *High:* Background `#FBF0ED`, border `#B4472F`, text `#87230E`.
  - *Critical:* Background `#F7ECEB`, border `#7A2418`, text `#7A2418`, weight 700.

### Tabular Stat Blocks & Big Figures
- Large-scale investigative metric containers. Pure `#FFFFFF` background, `#E2DDD5` 1px border, padding `space-lg`.
- Top: uppercase section kicker in `#8C847A` (`label-caps`).
- Middle: colossal numerical total in `Newsreader` (`display-figure`), color `#1A1815`.
- Bottom: tabular delta context (e.g., *"+312% over original SARO allocation"*), with discrepancy values highlighted using the risk color spectrum.

### Semicircle Budget Gauges & Metric Meters
- Minimalist circular arc visualization charting disbursement against obligation.
- Built with crisp 6px stroke lines over an `#E2DDD5` background track. No neon glow or drop shadows; endpoints are flat or slightly rounded (radius 1). Central interior displays percentage value in `Inter` tabular bold.

### Typeahead Registry Search Box
- Prominent investigative input field. Background `#FFFFFF`, 1px border `#D8D2C7`, radius 4px, height 44px, text `#1A1815`.
- Active focus: 1px border `#0F5C5C`, paired with a 2px outer hairline glow of `#E6F0F0`.
- Integrated monospace indicator specifying search scope (e.g., `[PhilGEPS-ID / Agency / Contractor / Region]`).

### Split Maps & Timeline Sparklines
- Geospatial infrastructure split-view: Map container on one pane bounded by `#E2DDD5`, juxtaposed with real-time filtered audit rows on the parallel pane.
- Micro sparklines embedded in table cells: Raw SVG line plots, 1.5px stroke `#0F5C5C`, zero fill or flat 8% opacity fill, with high-risk variance nodes marked in `#7A2418`.

### Data Tables & Dossier Grids
- Pure `#FFFFFF` background with sticky headers.
- Header row: `#FAF8F5`, border-bottom 2px solid `#1A1815`, typography `label-caps` in `#68625B`.
- Data rows: height 44px, border-bottom 1px solid `#E2DDD5`. Hover state `#FAF8F5`.
- Numeric cells: right-aligned, monospace/tabular lining (`font-feature-settings: "tnum"`).

### Professional Empty & Skeleton States
- **Skeleton Shimmers:** No energetic high-frequency pulses. Uses static or subtle 3-second breathing tone blocks in `#EFECE6` with hairline `#E2DDD5` containers.
- **Empty Query Dossier:** Muted line-drawn document glyph, headline in `Newsreader` 18px (`headline-sm`), body description detailing zero matching allocations under specified legislative filters, followed by an explicit "Clear Registry Filters" link.