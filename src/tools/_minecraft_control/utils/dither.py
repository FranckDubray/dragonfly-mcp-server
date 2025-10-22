"""
Image quantization utilities: palette selection, Lab distance, and optional Floyd–Steinberg dithering.
"""
from typing import Dict, Tuple, List
import numpy as np

RGB = Tuple[int, int, int]
Palette = Dict[str, RGB]


# --- Color space conversion helpers (sRGB -> Lab) ---

def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = c / 255.0
    a = 0.055
    return np.where(c <= 0.04045, c / 12.92, ((c + a) / (1 + a)) ** 2.4)


def _linear_to_xyz(rgb: np.ndarray) -> np.ndarray:
    # sRGB D65 conversion matrix
    m = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ])
    return rgb @ m.T


def _xyz_to_lab(xyz: np.ndarray) -> np.ndarray:
    # Reference white D65
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    x = xyz[:, 0] / Xn
    y = xyz[:, 1] / Yn
    z = xyz[:, 2] / Zn

    def f(t):
        delta = 6 / 29
        return np.where(t > delta ** 3, t ** (1 / 3), (t / (3 * delta ** 2)) + (4 / 29))

    fx, fy, fz = f(x), f(y), f(z)
    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return np.stack([L, a, b], axis=1)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    lin = _srgb_to_linear(rgb.astype(np.float64))
    xyz = _linear_to_xyz(lin)
    return _xyz_to_lab(xyz)


# --- Distance metrics ---

def nearest_palette_index_rgb(px: np.ndarray, pal_rgb: np.ndarray) -> np.ndarray:
    # px: (H,W,3), pal_rgb: (P,3)
    # Compute squared Euclidean distance in RGB
    diffs = px[:, :, None, :] - pal_rgb[None, None, :, :]
    d2 = np.sum(diffs * diffs, axis=3)
    return np.argmin(d2, axis=2)


def nearest_palette_index_lab(px: np.ndarray, pal_lab: np.ndarray) -> np.ndarray:
    diffs = px[:, :, None, :] - pal_lab[None, None, :, :]
    d2 = np.sum(diffs * diffs, axis=3)
    return np.argmin(d2, axis=2)


# --- Quantization with optional Floyd–Steinberg dithering ---

def quantize_blocks(
    image_rgb: np.ndarray,
    palette: Palette,
    distance: str = "rgb",
    dither: bool = False,
) -> List[List[str]]:
    """Return 2D array (list of rows) of block names for each pixel.
    image_rgb: HxWx3 uint8 array
    palette: dict of block_name -> (R,G,B)
    distance: 'rgb' | 'lab'
    dither: Floyd–Steinberg error diffusion if True
    """
    if image_rgb.dtype != np.uint8:
        image_rgb = image_rgb.astype(np.uint8)

    # Build palette arrays
    block_names = list(palette.keys())
    pal_rgb = np.array([palette[n] for n in block_names], dtype=np.float64)

    if distance == "lab":
        pal_lab = rgb_to_lab(pal_rgb)

    h, w, _ = image_rgb.shape

    if not dither:
        # Vectorized nearest for speed
        if distance == "lab":
            px_lab = rgb_to_lab(image_rgb.reshape(-1, 3)).reshape(h, w, 3)
            idx = nearest_palette_index_lab(px_lab, pal_lab)
        else:
            idx = nearest_palette_index_rgb(image_rgb, pal_rgb)
        return [[block_names[idx[y, x]] for x in range(w)] for y in range(h)]

    # Dithered path (Floyd–Steinberg)
    work = image_rgb.astype(np.float64)
    for y in range(h):
        # Left-to-right pass
        for x in range(w):
            current = work[y, x]
            if distance == "lab":
                curr_lab = rgb_to_lab(current.reshape(1, 3)).reshape(3)
                diffs = curr_lab[None, :] - pal_lab
                d2 = np.sum(diffs * diffs, axis=1)
                i = int(np.argmin(d2))
            else:
                diffs = current[None, :] - pal_rgb
                d2 = np.sum(diffs * diffs, axis=1)
                i = int(np.argmin(d2))
            target = pal_rgb[i]
            err = current - target
            work[y, x] = target
            # Distribute error
            if x + 1 < w:
                work[y, x + 1] += err * (7 / 16)
            if y + 1 < h:
                if x > 0:
                    work[y + 1, x - 1] += err * (3 / 16)
                work[y + 1, x] += err * (5 / 16)
                if x + 1 < w:
                    work[y + 1, x + 1] += err * (1 / 16)
    work = np.clip(work, 0, 255).astype(np.uint8)
    # Final nearest mapping to block names
    if distance == "lab":
        px_lab = rgb_to_lab(work.reshape(-1, 3)).reshape(h, w, 3)
        idx = nearest_palette_index_lab(px_lab, pal_lab)
    else:
        idx = nearest_palette_index_rgb(work, pal_rgb)
    return [[block_names[idx[y, x]] for x in range(w)] for y in range(h)]
