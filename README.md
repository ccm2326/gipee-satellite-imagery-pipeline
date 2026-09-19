# Satellite Imagery Processing Pipeline

Estimates electrical conductivity (EC) from Sentinel-2 bands for the Quilca study area. It computes the spectral index SI5 for each capture date, converts it to EC with a regression calibrated on laboratory measurements, writes a georeferenced COG (Cloud Optimized GeoTIFF) and stores it in Supabase for use by the web map frontend.

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

## Input data

Sentinel-2 bands B3, B4 and B8 exported from Google Earth Engine at 10 m. Clip the export to the study polygon: pixels with `B3 = 0` are treated as no data.

## Usage

```bash
venv/bin/python process_satellite_imagery.py <date:YYYY-MM-DD|all> <input_dir>
```

Examples:

```bash
venv/bin/python process_satellite_imagery.py 2026-06-27 GEE_Quilca
venv/bin/python process_satellite_imagery.py all GEE_Quilca
```

`input_dir` must contain `{date}_B3.tif`, `{date}_B4.tif`, `{date}_B8.tif` for that date. `all` processes every date that has a `*_B3.tif` file. `input_dir` can be a relative or absolute path.

## Method

- **SI5** = (B8 × B4) / B3, that is (NIR × Red) / Green, computed per pixel.
- **EC** = 0.05384 × SI5 − 107.16. 

Bands are reprojected from the source UTM CRS to EPSG:4326 using nearest-neighbor resampling, so the raster aligns with the web map.

## Output

A single-band COG is written to `results/{date}_ec.tif`. If Supabase credentials are set, the file is uploaded to the `satellite-imagery` Storage bucket and a row (site_id, capture_date, satellite_provider, image_resolution, imagery_path) is inserted into the `satellite_imagery` table. 

## Project structure

```
.
├── process_satellite_imagery.py  # orchestrator: computes EC, writes COG, syncs to Supabase
├── indices.py                    # SI5, EC calibration and reprojection 
├── supabase_sync.py              # Storage upload + table insert / preview mode
├── requirements.txt
└── .env.example
```

