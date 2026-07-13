#!/usr/bin/env python3
"""Generate bust portrait with tight face crop to minimize background."""
from PIL import Image, ImageEnhance
import sys

CHARS = "@%#*+=-:. "


def generate(input_path, output_path, width=56, gamma=0.66):
    img = Image.open(input_path).convert("RGB")

    # Find face region using luminance profile
    gray = img.convert("L")
    w, h = img.size

    row_lums = [sum(gray.getpixel((x, y)) for x in range(0, w, 10)) / max(1, w // 10) for y in range(h)]
    thr = 40
    face_rows = [y for y, l in enumerate(row_lums) if l > thr]
    if face_rows:
        top = max(0, face_rows[0] - 10)
        bot = min(h, face_rows[-1] + 10)
    else:
        top, bot = 0, h

    col_lums = [sum(gray.getpixel((x, y)) for y in range(top, bot, 5)) / max(1, (bot - top) // 5) for x in range(w)]
    face_cols = [x for x, l in enumerate(col_lums) if l > thr]
    if face_cols:
        left = max(0, face_cols[0] - 10)
        right = min(w, face_cols[-1] + 10)
    else:
        left, right = 0, w

    # Crop tight
    img = img.crop((left, top, right, bot))
    cw, ch = img.size
    print(f"Tight crop: ({left},{top})-({right},{bot}) = {cw}x{ch}")

    target_h = int(width * (ch / cw) * 0.5)
    if target_h < 10:
        target_h = 10
    small = img.resize((width, target_h), Image.LANCZOS)

    enhanced = ImageEnhance.Sharpness(small).enhance(2.0)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.5)
    gray_small = enhanced.convert("L")

    pixels = list(gray_small.getdata())
    lo = min(pixels)
    hi = max(pixels)
    rng = hi - lo if hi != lo else 1

    result = []
    for y in range(target_h):
        row = []
        for x in range(width):
            l = gray_small.getpixel((x, y))
            l = int((l - lo) / rng * 255)
            l = max(0, min(255, l))
            l = int(255 * (l / 255) ** gamma)
            l = max(0, min(255, l))
            idx = l * (len(CHARS) - 1) // 255
            row.append(CHARS[idx])
        line = "".join(row).rstrip()
        result.append(line)

    with open(output_path, "w") as f:
        f.write("\n".join(result))

    print(f"Written: {output_path}")
    print(f"Size: {width}x{target_h}")
    for line in result:
        print(line)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: generate_bust.py <input> <output> [width]")
        sys.exit(1)
    w = int(args[2]) if len(args) > 2 else 56
    generate(args[0], args[1], width=w)
