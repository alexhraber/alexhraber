#!/usr/bin/env python3
"""
Generate ASCII portrait with edge-enhanced facial features.

Usage:
    nix-shell -p python313Packages.pillow --run "python3 generate_ascii.py <input> <output> [width]"
"""
import sys
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageChops

# Full character set for facial rendering
CHARS = "@%#*+=-:. "


def generate(input_path, output_path, width=64):
    img = Image.open(input_path).convert("RGB")
    w, h = img.size

    # --- Auto-crop to face ---
    step = max(1, w // 20)
    row_lums = []
    for y in range(h):
        samples = [img.getpixel((x, y)) for x in range(step, w - step, step)]
        avg = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in samples) / len(samples)
        row_lums.append(avg)

    thr = 25
    face_rows = [y for y, l in enumerate(row_lums) if l > thr]
    top = max(0, face_rows[0] - 5) if face_rows else 0
    bottom = min(h, face_rows[-1] + 5) if face_rows else h

    col_lums = []
    for x in range(w):
        samples = [img.getpixel((x, y)) for y in range(top, bottom, max(1, (bottom - top) // 15))]
        avg = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in samples) / len(samples)
        col_lums.append(avg)

    face_cols = [x for x, l in enumerate(col_lums) if l > thr]
    left = max(0, face_cols[0] - 5) if face_cols else 0
    right = min(w, face_cols[-1] + 5) if face_cols else w

    img = img.crop((left, top, right, bottom))

    # --- Resize ---
    cw, ch = img.size
    aspect = ch / cw
    target_h = int(width * aspect * 0.5)
    small = img.resize((width, target_h), Image.LANCZOS)

    # --- Edge detection for feature emphasis ---
    gray = small.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(2.0)

    # Blend original luminance with edges
    gray_f = gray.filter(ImageFilter.SMOOTH)
    # Invert edges so bright areas are features
    edges_inv = ImageChops.invert(edges)
    # Composite: mostly original, with edge emphasis
    blended = Image.blend(gray_f, edges_inv, 0.15)

    # --- Manual contrast stretch ---
    pixels = list(blended.getdata())
    lo = min(pixels)
    hi = max(pixels)
    rng = hi - lo if hi != lo else 1

    result = []
    for y in range(target_h):
        row = []
        for x in range(width):
            l = blended.getpixel((x, y))
            l = int((l - lo) / rng * 255)
            l = max(0, min(255, l))
            # Gamma correction for mid-tone detail
            l = int(255 * (l / 255) ** 0.7)
            l = max(0, min(255, l))
            idx = l * (len(CHARS) - 1) // 255
            row.append(CHARS[idx])
        result.append("".join(row))

    ascii_art = "\n".join(result)

    with open(output_path, "w") as f:
        f.write(ascii_art)

    print(f"Written: {output_path}")
    print(f"Size: {width}x{target_h}")
    print(f"Crop: ({left},{top})-({right},{bottom})")

    # Preview
    for line in result:
        print(line)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate_ascii.py <input> <output> [width]")
        sys.exit(1)
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    generate(sys.argv[1], sys.argv[2], w)
