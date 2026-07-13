from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

DST_CRS = "EPSG:4326"


def read_band(input_dir: str, date: str, band: str) -> np.ndarray:
    path = Path(input_dir) / f"{date}_{band}.tif"
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32)


def calculate_rvi(b4: np.ndarray, b8: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where((b4 > 0) & (b8 > 0), b8 / b4, np.nan).astype(np.float32)


def calculate_r_nir_g(b3: np.ndarray, b4: np.ndarray, b8: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where((b3 > 0) & (b4 > 0) & (b8 > 0), (b4 * b8) / b3, np.nan).astype(np.float32)


def reproject_band(band: np.ndarray, src_crs, src_transform, dst_transform, dst_width, dst_height) -> np.ndarray:
    out = np.full((dst_height, dst_width), np.nan, dtype=np.float32)
    reproject(
        source=band,
        destination=out,
        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=np.nan,
        dst_transform=dst_transform,
        dst_crs=DST_CRS,
        dst_nodata=np.nan,
        resampling=Resampling.nearest,
    )
    return out


def compute_indices(date: str, input_dir: str) -> dict:
    b3 = read_band(input_dir, date, "B3")
    b4 = read_band(input_dir, date, "B4")
    with rasterio.open(Path(input_dir) / f"{date}_B8.tif") as src:
        b8 = src.read(1).astype(np.float32)
        src_crs = src.crs
        src_transform = src.transform
        src_width = src.width
        src_height = src.height

    rvi = calculate_rvi(b4, b8)
    r_nir_g = calculate_r_nir_g(b3, b4, b8)

    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs, DST_CRS, src_width, src_height,
        *rasterio.transform.array_bounds(src_height, src_width, src_transform),
    )

    rvi_reproj = reproject_band(rvi, src_crs, src_transform, dst_transform, dst_width, dst_height)
    r_nir_g_reproj = reproject_band(r_nir_g, src_crs, src_transform, dst_transform, dst_width, dst_height)

    return {
        "rvi": rvi_reproj,
        "r_nir_g": r_nir_g_reproj,
        "dst_transform": dst_transform,
        "dst_width": dst_width,
        "dst_height": dst_height,
    }
