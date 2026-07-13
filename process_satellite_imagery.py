import sys
from pathlib import Path

import numpy as np
import rasterio
from dotenv import load_dotenv

import supabase_sync
from indices import compute_indices

load_dotenv()


def write_cog(date: str, computed: dict) -> Path:
    profile = {
        "driver": "COG",
        "dtype": "float32",
        "nodata": np.nan,
        "width": computed["dst_width"],
        "height": computed["dst_height"],
        "count": 2,
        "crs": "EPSG:4326",
        "transform": computed["dst_transform"],
        "compress": "DEFLATE",
        "overview_resampling": "nearest",
    }

    output = Path(f"results/indices_{date}.tif")
    output.parent.mkdir(exist_ok=True)
    with rasterio.open(output, "w", **profile) as dst:
        dst.write(computed["rvi"], 1)
        dst.write(computed["r_nir_g"], 2)
        dst.set_band_description(1, "RVI (B8/B4)")
        dst.set_band_description(2, "R*NIR/G ((B4*B8)/B3)")

    return output


def run(date: str, input_dir: str):
    computed = compute_indices(date, input_dir)
    output = write_cog(date, computed)

    valid_rvi = computed["rvi"][~np.isnan(computed["rvi"])]
    valid_rng = computed["r_nir_g"][~np.isnan(computed["r_nir_g"])]
    avg_rvi = float(valid_rvi.mean())
    avg_rng = float(valid_rng.mean())

    print(f"Saved to {output} ({output.stat().st_size / 1024:.1f} KB)")
    print(f"  RVI mean:         {avg_rvi:.4f}")
    print(f"  R*NIR/G mean:     {avg_rng:.4f}")

    if supabase_sync.has_credentials():
        supabase_sync.upload_and_insert(output, date, avg_rvi, avg_rng)
    else:
        supabase_sync.print_preview(date, avg_rvi, avg_rng)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("venv/bin/python process_satellite_imagery.py <date:YYYY-MM-DD> <input_dir>")
        sys.exit(1)

    run(sys.argv[1], sys.argv[2])
