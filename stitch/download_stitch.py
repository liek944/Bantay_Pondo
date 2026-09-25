"""Download and catalog all Stitch screens for Bantay Pondo Platform."""

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ID = "7967343297171400144"
STITCH_DIR = Path("/home/keil/Bantay_Pondo/stitch")
SCREENS_DIR = STITCH_DIR / "screens"

SCREENS_DATA = [
    {
        "index": 1,
        "id": "2293d1ce9fd54f65af0fa6da03282525",
        "slug": "01_whistleblower_and_evidence",
        "title": "Whistleblower & Evidence — Bantay Pondo",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AEtjO1W99IFchiFmS4aTbJg4O4kaE-5szczxZVjz8PWHcc5hyU7fgt_UwO5aXTEIje0fvIKHyLmNU_QokIsD7w0bcrS30YXfJe_MXMZKUPcHeneHl0TwMgJ_dSw_TTLttDNsgA7EpxP-5J4MVbMqTFdijONZirfakAUZbXf_4MuBdtvTmyybqskIuIluKpiao9N4BGfbCdVVrHalkNflntteUUmHOk7rj9MXXya8HlWNcxC_iIYWvNXzIv-bpw",
        "code_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAwMDY1YzRkYzk3ZTY0MDkwNzc5OTNjN2I5MmFjZWFiEgsSBxDxps-opxgYAZIBIwoKcHJvamVjdF9pZBIVQhM3OTY3MzQzMjk3MTcxNDAwMTQ0&filename=&opi=89354086",
        "mime_type": "text/html",
        "width": 2560,
        "height": 7300,
        "code_ext": "html"
    },
    {
        "index": 2,
        "id": "416c4539979742ceb7a522f7da8bd1ed",
        "slug": "02_locality_dossier_tuguegarao_city",
        "title": "Locality Dossier: Tuguegarao City — Bantay Pondo",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AEtjO1VODZMgmGyaYH8CmZLndvqAm2yCIBIOSQfi3aOtOjrsp2_z4UKzZt-U8B624ftZvcEpCe-K_D43kBv7iDnBrXMwNziJju8nXGJ58LmPHTswao6tJGUQURkQ2bM_OMK3dU1PK69MCFJYm1JFv7tCx8sE0HmPCJAYj6o3LBir_xbfwoIyCWkKw8AfbhE9fnXGabDNjIhHnSiwziwi-Z-mFuV4Ejna7f3pW0MDEJqVN91W_eet_iW9vNi18bk",
        "code_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAwMDY1YmQ2YmI1OWRkN2QwMmQzZmQxZDkwMTgwOTViEgsSBxDxps-opxgYAZIBIwoKcHJvamVjdF9pZBIVQhM3OTY3MzQzMjk3MTcxNDAwMTQ0&filename=&opi=89354086",
        "mime_type": "text/html",
        "width": 2560,
        "height": 6494,
        "code_ext": "html"
    },
    {
        "index": 3,
        "id": "5f3664e6d0d8485ca8bc3ac9702875db",
        "slug": "03_compare_localities_system_states",
        "title": "Compare Localities & System States — Bantay Pondo",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AEtjO1Un63weUwMj6khZdnPW9zoK36CXat7izLVqwdE8bWnUVZgir6qpjGqE80MfVveMy2hGlLTIgxT-tLRse1mWw7SwEoMS7cMOTO8NxjX4BydoXKLUfMItU1dB-xDEmFmXtvYoxNfQctxlHZk7sCk6mQlRADQfM0EB5fov3nZa3Bzo2P4J2Is6fV3czVL302DtsZu9MfRHlIfrrjYVris25_cZsuip3ofNokofIXstvrSqKiz0jkJQh5dBAEQ",
        "code_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAwMDY1YmQ2YmIxYzE5ODUwMzMyY2ZkZTU0MTk5ZjdmEgsSBxDxps-opxgYAZIBIwoKcHJvamVjdF9pZBIVQhM3OTY3MzQzMjk3MTcxNDAwMTQ0&filename=&opi=89354086",
        "mime_type": "text/html",
        "width": 2560,
        "height": 6922,
        "code_ext": "html"
    },
    {
        "index": 4,
        "id": "9b188e8c7e414a239ef7f2e98237503f",
        "slug": "04_contractor_dossier_alpha_omega",
        "title": "Contractor Dossier: Alpha & Omega — Bantay Pondo",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AEtjO1UnD1n8GlOX57Evtwtn4uj2a41eYnqG49dvgcnrpfCQLoFa9fjS2TaQrQXo1BueoBV94gWqD3usesEBl9bOU1ZkcF7Zsbv_geno2PMANypsMPxKwvAsyTeoyEXs8V6hekGzEfUcH-wPB85NWJaBeDZE36D2w-pIBMKy8ezqWlVVe5Xumi259OrbrpesN7Ie8waCzvbcoMsoXTNxICO6P74PdqVk-4ubylPUWmlttuBQoVZmHjgUjLl3Xg",
        "code_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAwMDY1YmQ2YmI2OTllMDgwMjJkNGRmMWI0Mjk3NTA5EgsSBxDxps-opxgYAZIBIwoKcHJvamVjdF9pZBIVQhM3OTY3MzQzMjk3MTcxNDAwMTQ0&filename=&opi=89354086",
        "mime_type": "text/html",
        "width": 2560,
        "height": 6372,
        "code_ext": "html"
    },
    {
        "index": 5,
        "id": "9b2205e18dbc473d9f8c06cdfb0ecfa2",
        "slug": "05_national_map_search",
        "title": "National Map & Search — Bantay Pondo",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AEtjO1UJgx7sx6KL4V8tQNsBQZwNj1NGncEhyYiXQxdapogI_cOExfdEn_Mt4rii55MCpJsZdFrzkDI8_TwDCUKk4Y2cbbQQVji8-RTuCmYtaOP0mTmGWFFZDZRYtBb-BsaOJKwdHpOfgL7Pvig8uofGMLb9OIep_wieWKR78K7NRyOFfsFhEKk1je64EXlka5aQZiq2F3ZN7l4jtRQJF82OjkUEWiMNI68JoOXWZDlBbjAhbmR2ra6QsY-dJDQ",
        "code_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAwMDY1YmQ2YmI1MjNiYWMwMjJkNmE5Y2VkMTFiYzFiEgsSBxDxps-opxgYAZIBIwoKcHJvamVjdF9pZBIVQhM3OTY3MzQzMjk3MTcxNDAwMTQ0&filename=&opi=89354086",
        "mime_type": "text/html",
        "width": 2560,
        "height": 6538,
        "code_ext": "html"
    },
    {
        "index": 6,
        "id": "c040387006294616ac1f7c2ae0e1603e",
        "slug": "06_project_detail_cagayan_river_dike_phase_iii",
        "title": "Project Detail: Cagayan River Dike Phase III — Bantay Pondo",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AEtjO1U5fytmGbuCEvN01qVHZzB8378qlxB9ZfotDzCp2rdO8oWyVZ1E3BKy9IGLE_v4cU81eKHWBb84uKJyZxs4KoTSq5ZPK0YkSOkr6_4k9e24iXKErxSilEOfCmx5ivNbdkQWSMV-tn4hdLkMcGoJHv24-jsckotWt9oF4b30f7MyR2C1-b-EKpta6gC4Rj4HTeHfb7LFuZApPyu3rEpy79yRL4EG1VrIMSbel3Qfhj1H8cE_jAv81z6yjB0",
        "code_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAwMDY1YmQ2YmMwMTE5MDgwMzMyY2ZkZTU0MTk5ZjdmEgsSBxDxps-opxgYAZIBIwoKcHJvamVjdF9pZBIVQhM3OTY3MzQzMjk3MTcxNDAwMTQ0&filename=&opi=89354086",
        "mime_type": "text/html",
        "width": 2560,
        "height": 7264,
        "code_ext": "html"
    },
    {
        "index": 7,
        "id": "bca0f5a4112c47d0bc63bde65890e0b4",
        "slug": "07_brand_emblem",
        "title": "Bantay Pondo Brand Emblem",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AEtjO1Vm3WMrInkqwB66qOEcF51D-S9NHG7XkAwFJf3Q_WjiItvvnKUlyhGcr4ehemXAC6oUWriI0WCWePllFRht3pdUGzGhSWnAXLdS3ltBR5rdjiHTSr6GYMQsPlkRVilxfQsYRP8OUm5YtMh3K5WMp0U6mw1pj8BMCnYqprywU2UthEoqcccpz8B4roN3m-TL6XmNirPG-9CYg_TWIJqWnnPvwhaTf_qa0ZXO6wiAMC2_5KebtRjDmlGPw2o",
        "code_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAwMDY1YmQ2YjMyNWVlNDMwODlhZjY1ZDE0MmMwNTgyEgsSBxDxps-opxgYAZIBIwoKcHJvamVjdF9pZBIVQhM3OTY3MzQzMjk3MTcxNDAwMTQ0&filename=&opi=89354086",
        "mime_type": "image/svg+xml",
        "width": 240,
        "height": 48,
        "code_ext": "svg"
    }
]

def download_file(url: str, output_path: Path) -> bool:
    """Download a file using curl -sSL."""
    cmd = ["curl", "-sSL", url, "-o", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error downloading {url}: {result.stderr}", file=sys.stderr)
        return False
    if not output_path.exists() or output_path.stat().st_size == 0:
        print(f"Error: downloaded file is empty: {output_path}", file=sys.stderr)
        return False
    return True

def main():
    SCREENS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []

    print("Beginning download of 7 Stitch screens...")

    for item in SCREENS_DATA:
        screen_dir = SCREENS_DIR / item["slug"]
        screen_dir.mkdir(parents=True, exist_ok=True)

        code_filename = f"code.{item['code_ext']}"
        code_path = screen_dir / code_filename
        screenshot_full_path = screen_dir / "screenshot.png"
        screenshot_thumb_path = screen_dir / "thumbnail.png"
        metadata_path = screen_dir / "metadata.json"

        print(f"\n[{item['index']}/7] {item['title']} (ID: {item['id']})")

        # 1. Download code
        print(f"  Downloading code to {code_path.name}...")
        if not download_file(item["code_url"], code_path):
            sys.exit(1)
        print(f"  ✓ Code: {code_path.stat().st_size:,} bytes")

        # For SVG brand emblem, also create code.html wrapper
        if item["code_ext"] == "svg":
            svg_content = code_path.read_text(encoding="utf-8")
            html_wrapper = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{item['title']}</title>
  <style>
    body {{
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background-color: #FAF8F5;
      margin: 0;
      padding: 2rem;
    }}
    .emblem-card {{
      background: #FFFFFF;
      padding: 2rem 3rem;
      border: 1px solid #E2DDD5;
      border-radius: 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
  </style>
</head>
<body>
  <div class="emblem-card">
    {svg_content}
  </div>
</body>
</html>"""
            (screen_dir / "code.html").write_text(html_wrapper, encoding="utf-8")

        # 2. Download full resolution screenshot (=s0)
        print(f"  Downloading full-res screenshot ({item['width']}x{item['height']})...")
        full_screenshot_url = f"{item['screenshot_url']}=s0"
        if not download_file(full_screenshot_url, screenshot_full_path):
            sys.exit(1)
        print(f"  ✓ Full Screenshot: {screenshot_full_path.stat().st_size:,} bytes")

        # 3. Download thumbnail screenshot (default preview)
        print(f"  Downloading thumbnail preview...")
        if not download_file(item["screenshot_url"], screenshot_thumb_path):
            sys.exit(1)
        print(f"  ✓ Thumbnail: {screenshot_thumb_path.stat().st_size:,} bytes")

        # 4. Save metadata.json
        metadata = {
            "index": item["index"],
            "id": item["id"],
            "title": item["title"],
            "slug": item["slug"],
            "width": item["width"],
            "height": item["height"],
            "mime_type": item["mime_type"],
            "code_file": code_filename,
            "screenshot_file": "screenshot.png",
            "thumbnail_file": "thumbnail.png",
            "code_url": item["code_url"],
            "screenshot_url": item["screenshot_url"],
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        manifest.append(metadata)

    # Save manifest.json in screens directory
    (SCREENS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("\n✓ Successfully downloaded and cataloged all 7 screens!")

if __name__ == "__main__":
    main()
