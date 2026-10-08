"""Profile photo processing with Pillow.

Photos are centre-cropped to a square, resized, given a circular alpha mask
and returned as a base64 ``data:`` URI so they can be embedded directly in
standalone HTML and PDF output.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from cvforge.models import CVForgeError

DEFAULT_PHOTO_SIZE = 256


class PhotoError(CVForgeError):
    """Raised when a profile photo cannot be read or processed."""


def circular_photo_data_uri(
    path: str | Path, size: int = DEFAULT_PHOTO_SIZE, fmt: str = "PNG"
) -> str:
    """Load an image, apply a circular crop, and return a base64 data URI.

    Args:
        path: Path to the source image (any Pillow-supported format).
        size: Target width/height of the square output in pixels.
        fmt: Output image format (``PNG`` keeps the transparent corners).

    Returns:
        A ``data:image/png;base64,...`` URI string.

    Raises:
        PhotoError: If the file is missing or not a readable image.
    """
    image_path = Path(path)
    if not image_path.is_file():
        raise PhotoError(f"Photo not found: '{image_path}'.")

    try:
        with Image.open(image_path) as src:
            img: Image.Image = ImageOps.exif_transpose(src).convert("RGBA")
            side = min(img.size)
            left = (img.width - side) // 2
            top = (img.height - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            mask = Image.new("L", (size * 4, size * 4), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
            mask = mask.resize((size, size), Image.Resampling.LANCZOS)
            img.putalpha(mask)

            buffer = io.BytesIO()
            img.save(buffer, format=fmt)
    except OSError as exc:
        raise PhotoError(f"Could not read photo '{image_path}': {exc}") from exc

    mime = f"image/{fmt.lower()}"
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
