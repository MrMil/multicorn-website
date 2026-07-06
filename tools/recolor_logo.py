#!/usr/bin/env python3
"""Recolor the Multicorn logo: purple unicorn, magenta horns, transparent background.

Takes the original black-on-white line art ("Multicorn Logo.png") and produces:
  assets/logo.png     - recolored, cropped, transparent background
  assets/favicon.png  - 256x256 square version for the browser tab

How it works
------------
1. The artwork is black on white, so darkness (inverted luminance) becomes the
   alpha channel. This preserves the anti-aliased edges of the original.
2. The black pixels are split into connected components (scipy.ndimage.label).
   Conveniently, the five spiral horns are drawn as many small separate
   segments, while the head and mane are two large blobs.
3. Components are classified as "body" (purple) or "horn" (magenta):
   - the two largest components are the mane and the head
   - three small components are facial details (inner ear, eye, nostril),
     identified by their label ids (see PURPLE_LABELS below)
   - everything else is a horn segment
4. Semi-transparent edge pixels (which are not part of any component) take the
   color of the nearest component, via a distance transform.
5. The result is cropped to the artwork plus padding.

Usage:
    python3 -m venv venv && venv/bin/pip install -r tools/requirements.txt
    venv/bin/python3 tools/recolor_logo.py

Pass --debug to also write debug_components.png showing the classification.

NOTE: PURPLE_LABELS contains component ids specific to the current
"Multicorn Logo.png". If the source image changes, re-run with --debug,
inspect the output, and update the ids (components are also printed with
their sizes and centroids to help identify them).
"""

import argparse
import os

import numpy as np
from PIL import Image
from scipy import ndimage

MAGENTA = np.array([255, 46, 185], float)   # #FF2EB9 - horns
PURPLE = np.array([160, 107, 255], float)   # #A06BFF - body

# Component ids in the source image that must stay purple even though they are
# small: 14=mane, 21=head (the two big blobs), 20=inner ear, 26=eye, 27=nostril.
PURPLE_LABELS = {14, 21, 20, 26, 27}

DARK_THRESHOLD = 128  # luminance below this counts as artwork
CROP_PADDING = 30     # transparent pixels kept around the artwork


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", default="Multicorn Logo.png")
    parser.add_argument("--out-dir", default="assets")
    parser.add_argument("--debug", action="store_true",
                        help="write debug_components.png and print component info")
    args = parser.parse_args()

    img = Image.open(args.source).convert("RGBA")
    a = np.array(img)
    lum = a[..., :3].mean(axis=2)

    # 1. alpha from darkness (keeps anti-aliased edges)
    alpha = np.clip(255 - lum, 0, 255).astype(np.uint8)

    # 2. split the artwork into connected components
    dark = lum < DARK_THRESHOLD
    labels, n = ndimage.label(dark)

    if args.debug:
        sizes = ndimage.sum(dark, labels, range(1, n + 1))
        cents = ndimage.center_of_mass(dark, labels, range(1, n + 1))
        print(f"{n} components:")
        for lab in range(1, n + 1):
            cy, cx = cents[lab - 1]
            tag = "PURPLE" if lab in PURPLE_LABELS else "magenta"
            print(f"  label {lab:2d} size={int(sizes[lab - 1]):6d} "
                  f"centroid=({int(cx)},{int(cy)}) -> {tag}")

    # 3+4. classify components; edge pixels take the nearest component's color
    _, (iy, ix) = ndimage.distance_transform_edt(~dark, return_indices=True)
    nearest = labels[iy, ix]
    is_purple = np.isin(nearest, list(PURPLE_LABELS))

    rgb = np.where(is_purple[..., None], PURPLE, MAGENTA)
    out = np.dstack([rgb, alpha[..., None]]).astype(np.uint8)

    if args.debug:
        dbg = np.full((*dark.shape, 3), 255, np.uint8)
        dbg[dark] = np.where(is_purple[dark, None],
                             PURPLE.astype(np.uint8), MAGENTA.astype(np.uint8))
        Image.fromarray(dbg).save("debug_components.png")
        print("wrote debug_components.png")

    # 5. crop to content + padding
    ys, xs = np.where(alpha > 8)
    y0, y1 = max(ys.min() - CROP_PADDING, 0), min(ys.max() + CROP_PADDING, out.shape[0])
    x0, x1 = max(xs.min() - CROP_PADDING, 0), min(xs.max() + CROP_PADDING, out.shape[1])
    out = out[y0:y1, x0:x1]

    os.makedirs(args.out_dir, exist_ok=True)
    im = Image.fromarray(out)
    logo_path = os.path.join(args.out_dir, "logo.png")
    im.save(logo_path)
    print(f"wrote {logo_path} {im.size}")

    # favicon: pad to a square, then downscale
    w, h = im.size
    side = max(w, h)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(im, ((side - w) // 2, (side - h) // 2))
    favicon_path = os.path.join(args.out_dir, "favicon.png")
    sq.resize((256, 256), Image.LANCZOS).save(favicon_path)
    print(f"wrote {favicon_path} (256x256)")


if __name__ == "__main__":
    main()
