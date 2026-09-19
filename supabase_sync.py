import os
from pathlib import Path

"""Hardcoded for the current single-site, single-satellite setup.
If more sites or satellite sources are added later, these must become
parameters instead of constants. """
SITE_ID = 1
SATELLITE_PROVIDER = "Sentinel-2"
IMAGE_RESOLUTION = "10m"

STORAGE_BUCKET = "satellite-imagery"


def has_credentials() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))


def upload_and_insert(path: Path, capture_date: str):
    from supabase import create_client

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)

    filename = path.name
    with open(path, "rb") as f:
        client.storage.from_(STORAGE_BUCKET).upload(
            filename, f, {"content-type": "image/tiff", "upsert": "true"}
        )
    imagery_path = client.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    row = {
        "site_id": SITE_ID,
        "capture_date": capture_date,
        "satellite_provider": SATELLITE_PROVIDER,
        "image_resolution": IMAGE_RESOLUTION,
        "imagery_path": imagery_path,
    }
    client.table("satellite_imagery").insert(row).execute()
    print(f"Inserted into satellite_imagery: {row}")
    return row


def print_preview(capture_date: str):
    print("\n[preview mode] SUPABASE_URL / SUPABASE_SERVICE_KEY not set.")
    print("Row that would be inserted into satellite_imagery:")
    row = {
        "site_id": SITE_ID,
        "capture_date": capture_date,
        "satellite_provider": SATELLITE_PROVIDER,
        "image_resolution": IMAGE_RESOLUTION,
    }
    for k, v in row.items():
        print(f"  {k}: {v}")
