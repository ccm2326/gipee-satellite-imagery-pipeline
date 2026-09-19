import re
import sys
from pathlib import Path

import numpy as np
import rasterio
from dotenv import load_dotenv

import supabase_sync
from indices import DST_CRS, EC_INTERCEPT, EC_SLOPE, compute_ec

load_dotenv()

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_B3\.tif$")


def discover_dates(input_dir: str) -> list[str]:
    dates = []
    for path in sorted(Path(input_dir).glob("*_B3.tif")):
        match = DATE_RE.match(path.name)
        if match:
            dates.append(match.group(1))
    return dates


def write_cog(date: str, computed: dict) -> Path:
    profile = {
        "driver": "COG",
        "dtype": "float32",
        "nodata": np.nan,
        "width": computed["dst_width"],
        "height": computed["dst_height"],
        "count": 1,
        "crs": DST_CRS,
        "transform": computed["dst_transform"],
        "compress": "DEFLATE",
        "overview_resampling": "nearest",
    }

    output = Path(f"results/{date}_ec.tif")
    output.parent.mkdir(exist_ok=True)
    with rasterio.open(output, "w", **profile) as dst:
        dst.write(computed["ec"], 1)
        dst.set_band_description(1, f"Electrical conductivity estimate: EC = {EC_SLOPE}*SI5 + ({EC_INTERCEPT})")

    return output


def run(date: str, input_dir: str):
    computed = compute_ec(date, input_dir)
    output = write_cog(date, computed)

    print(f"{date}: saved to {output} ({output.stat().st_size / 1024:.1f} KB)")

    if supabase_sync.has_credentials():
        supabase_sync.upload_and_insert(output, date)
    else:
        supabase_sync.print_preview(date)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("venv/bin/python process_satellite_imagery.py <date:YYYY-MM-DD|all> <input_dir>")
        sys.exit(1)

    date_arg, input_dir = sys.argv[1], sys.argv[2]
    dates = discover_dates(input_dir) if date_arg == "all" else [date_arg]
    if not dates:
        print(f"No *_B3.tif files found in {input_dir}")
        sys.exit(1)

    for date in dates:
        run(date, input_dir)
