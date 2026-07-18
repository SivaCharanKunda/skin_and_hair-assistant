"""
Lightweight, EXPLAINABLE heuristic image analysis for the demo.

IMPORTANT (say this out loud in your internship demo too):
This does NOT perform real medical image diagnosis. There is no trained
dermatology model here. It only computes simple colour/texture statistics
with PIL + numpy so the pipeline has something concrete to reason about.

In a production version this function would be swapped for a real
computer-vision / dermatology model (e.g. a fine-tuned vision model served
behind an API). The rest of the graph (risk assessment, routines, product
recommendation, booking) does not need to change -- it only depends on the
dict shape returned below, which is the whole point of keeping this as an
isolated, swappable service.
"""

from typing import Dict, Any
import numpy as np
from PIL import Image


def analyze_image(image_path: str, concern_type: str) -> Dict[str, Any]:
    """
    Returns a dict of simple, explainable heuristics:
      - redness_score      (0-1)  higher = more red/inflamed tone
      - brightness_score   (0-1)  higher = shinier / oilier looking
      - texture_variance   (0-1)  higher = more patchy / uneven texture
      - dark_spot_flag     (bool) unusually dark, high-contrast patch found
      - confidence         (0-1)  always modest -- this is a heuristic, not a model
    """
    try:
        img = Image.open(image_path).convert("RGB").resize((256, 256))
    except Exception as e:
        return {
            "error": f"Could not read image: {e}",
            "redness_score": 0.0,
            "brightness_score": 0.0,
            "texture_variance": 0.0,
            "dark_spot_flag": False,
            "confidence": 0.0,
        }

    arr = np.asarray(img).astype("float32") / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

    # Redness: how much red channel dominates green/blue (rough inflammation proxy)
    redness_score = float(np.clip(np.mean(r - (g + b) / 2) * 3 + 0.5, 0, 1))

    # Brightness: overall luminance (rough oiliness/shine proxy)
    brightness_score = float(np.mean((r + g + b) / 3))

    # Texture variance: local std-dev as a proxy for unevenness/patchiness
    gray = (r + g + b) / 3
    texture_variance = float(np.clip(np.std(gray) * 4, 0, 1))

    # Dark spot flag: any small region much darker than the surrounding mean
    mean_lum = np.mean(gray)
    dark_mask = gray < (mean_lum - 0.35)
    dark_spot_flag = bool(np.sum(dark_mask) > (gray.size * 0.01))  # >1% of pixels

    return {
        "redness_score": round(redness_score, 2),
        "brightness_score": round(brightness_score, 2),
        "texture_variance": round(texture_variance, 2),
        "dark_spot_flag": dark_spot_flag,
        "confidence": 0.4,  # deliberately modest -- heuristic, not a real model
        "concern_type": concern_type,
    }
