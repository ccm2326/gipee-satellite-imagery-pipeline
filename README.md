# Satellite Imagery Processing Pipeline

Computes RVI (vegetation health) and R*NIR/G (water stress) indices from Sentinel-2 bands, generates a georeferenced COG (Cloud Optimized GeoTIFF) and stores it in Supabase alongside a summary row for use by the web map frontend.

## Setup

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in real credentials:

```bash
cp .env.example .env
```

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

Without a valid `.env`, the script still runs and generates the local file, but skips the Supabase upload/insert and prints the row it would have inserted (preview mode).

## Usage

```bash
venv/bin/python process_satellite_imagery.py <date:YYYY-MM-DD> <input_dir>
```

Example:

```bash
venv/bin/python process_satellite_imagery.py 2025-01-08 GEE_Quilca
```

`input_dir` must contain `{date}_B3.tif`, `{date}_B4.tif`, `{date}_B8.tif` for that date. `input_dir` can be a relative or absolute path.

## Indices

- **RVI** = B8 / B4 (vegetation vigor)
- **R\*NIR/G** = (B4 × B8) / B3 (water stress)

Bands are reprojected from the source UTM CRS to EPSG:4326 using nearest-neighbor resampling.

## Output

A 2-band COG is written to `results/indices_{date}.tif` (band 1 = RVI, band 2 = R\*NIR/G). If Supabase credentials are set, the file is uploaded to the `satellite-imagery` Storage bucket and a summary row (site_id, capture_date, satellite_provider, vegetation_index, water_stress_index, image_resolution, imagery_path) is inserted into the `satellite_imagery` table.

## Project structure

```
.
├── process_satellite_imagery.py  # orchestrator: computes indices, writes COG, syncs to Supabase
├── indices.py                    # index formulas + reprojection, no Supabase dependency
├── supabase_sync.py              # Storage upload + table insert / preview mode
├── requirements.txt
└── .env.example
```

## Known limitations

- `SITE_ID`, `SATELLITE_PROVIDER`, and `IMAGE_RESOLUTION` are hardcoded in `supabase_sync.py` for the current single-site, single-satellite setup. Adding a second site or satellite source requires turning these into parameters.
- The output directory is currently hardcoded to `results/`, relative to wherever the script is run from.
