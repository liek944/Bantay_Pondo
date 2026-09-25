# Bantay Pondo Platform — Stitch Design System & Screens

Design assets, UI code, and screenshots downloaded from Stitch project **Bantay Pondo Platform** (ID: `7967343297171400144`).

## Project Overview
- **Project Title:** Bantay Pondo Platform
- **Project ID:** `7967343297171400144`
- **Design System:** [Investigative Public Ledger](DESIGN.md)
- **Primary Typography:** Newsreader (Headings & Key Figures), Inter (System Interface & Tabular Metrics)
- **Primary Colors:** Deep Archival Sea Teal (`#0F5C5C`), Seed Dense Teal (`#0A4242`), Warm Newsroom Cream Canvas (`#FAF8F5`), White Sheet (`#FFFFFF`), Structural Dividers (`#E2DDD5`)
- **Diagnostic Risk Spectrum:** Sand Ochre (`#E8D5B7`), Regulatory Amber (`#D89B4A`), Investigative Rust (`#B4472F`), Civic Maroon (`#7A2418`)

---

## Catalog of Screens

| # | Screen Title | Screen ID | Dimensions | Code File | High-Res Screenshot | Thumbnail |
|---|---|---|---|---|---|---|
| 1 | **Whistleblower & Evidence** | `2293d1ce9fd54f65af0fa6da03282525` | 2560 × 7300 | [`code.html`](screens/01_whistleblower_and_evidence/code.html) | [`screenshot.png`](screens/01_whistleblower_and_evidence/screenshot.png) | [`thumbnail.png`](screens/01_whistleblower_and_evidence/thumbnail.png) |
| 2 | **Locality Dossier: Tuguegarao City** | `416c4539979742ceb7a522f7da8bd1ed` | 2560 × 6494 | [`code.html`](screens/02_locality_dossier_tuguegarao_city/code.html) | [`screenshot.png`](screens/02_locality_dossier_tuguegarao_city/screenshot.png) | [`thumbnail.png`](screens/02_locality_dossier_tuguegarao_city/thumbnail.png) |
| 3 | **Compare Localities & System States** | `5f3664e6d0d8485ca8bc3ac9702875db` | 2560 × 6922 | [`code.html`](screens/03_compare_localities_system_states/code.html) | [`screenshot.png`](screens/03_compare_localities_system_states/screenshot.png) | [`thumbnail.png`](screens/03_compare_localities_system_states/thumbnail.png) |
| 4 | **Contractor Dossier: Alpha & Omega** | `9b188e8c7e414a239ef7f2e98237503f` | 2560 × 6372 | [`code.html`](screens/04_contractor_dossier_alpha_omega/code.html) | [`screenshot.png`](screens/04_contractor_dossier_alpha_omega/screenshot.png) | [`thumbnail.png`](screens/04_contractor_dossier_alpha_omega/thumbnail.png) |
| 5 | **National Map & Search** | `9b2205e18dbc473d9f8c06cdfb0ecfa2` | 2560 × 6538 | [`code.html`](screens/05_national_map_search/code.html) | [`screenshot.png`](screens/05_national_map_search/screenshot.png) | [`thumbnail.png`](screens/05_national_map_search/thumbnail.png) |
| 6 | **Project Detail: Cagayan River Dike Phase III** | `c040387006294616ac1f7c2ae0e1603e` | 2560 × 7264 | [`code.html`](screens/06_project_detail_cagayan_river_dike_phase_iii/code.html) | [`screenshot.png`](screens/06_project_detail_cagayan_river_dike_phase_iii/screenshot.png) | [`thumbnail.png`](screens/06_project_detail_cagayan_river_dike_phase_iii/thumbnail.png) |
| 7 | **Bantay Pondo Brand Emblem** | `bca0f5a4112c47d0bc63bde65890e0b4` | 240 × 48 | [`code.svg`](screens/07_brand_emblem/code.svg) / [`code.html`](screens/07_brand_emblem/code.html) | [`screenshot.png`](screens/07_brand_emblem/screenshot.png) | [`thumbnail.png`](screens/07_brand_emblem/thumbnail.png) |

---

## Directory Structure

```
stitch/
├── DESIGN.md                                 # Full Stitch design system guidelines & tokens
├── README.md                                 # This catalog
├── download_stitch.py                        # Automated download & sync script
├── project.json                              # Stitch project metadata & screen coordinates
└── screens/
    ├── manifest.json                         # Structured JSON manifest of all screens
    ├── 01_whistleblower_and_evidence/
    │   ├── code.html                         # Full HTML/CSS markup
    │   ├── metadata.json                     # Screen parameters & API endpoints
    │   ├── screenshot.png                    # Original full-resolution image (2560x7300)
    │   └── thumbnail.png                     # Standard preview image
    ├── 02_locality_dossier_tuguegarao_city/
    │   ├── code.html
    │   ├── metadata.json
    │   ├── screenshot.png                    # Original full-resolution image (2560x6494)
    │   └── thumbnail.png
    ├── 03_compare_localities_system_states/
    │   ├── code.html
    │   ├── metadata.json
    │   ├── screenshot.png                    # Original full-resolution image (2560x6922)
    │   └── thumbnail.png
    ├── 04_contractor_dossier_alpha_omega/
    │   ├── code.html
    │   ├── metadata.json
    │   ├── screenshot.png                    # Original full-resolution image (2560x6372)
    │   └── thumbnail.png
    ├── 05_national_map_search/
    │   ├── code.html
    │   ├── metadata.json
    │   ├── screenshot.png                    # Original full-resolution image (2560x6538)
    │   └── thumbnail.png
    ├── 06_project_detail_cagayan_river_dike_phase_iii/
    │   ├── code.html
    │   ├── metadata.json
    │   ├── screenshot.png                    # Original full-resolution image (2560x7264)
    │   └── thumbnail.png
    └── 07_brand_emblem/
        ├── code.html                         # HTML preview wrapper
        ├── code.svg                          # Vector SVG graphic
        ├── metadata.json
        ├── screenshot.png                    # Rendered emblem PNG (480x96)
        └── thumbnail.png
```

---

## Re-downloading / Syncing Assets

To refresh or re-download the screen assets at any time:

```bash
python3 stitch/download_stitch.py
```
