#!/usr/bin/env python3
"""Export the PS5 tile art: icon0.png and the 4K background, BC7 checked by decoding.

Needs Pillow, etcpak and texture2ddecoder. Reads port/ps5/art/icon.png and
background.png (16:9), writes port/ps5/sce_sys/icon0.png 512x512, pic0.dds and
pic1.dds 3840x2160 BC7, pic1.png 1920x1080, and port/ps5/art/presentation.json.
"""
from pathlib import Path
import hashlib
import json
import struct

import etcpak
import texture2ddecoder
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT/'port/ps5/art'
OUT = ROOT/'port/ps5/sce_sys'
W, H = 3840, 2160


def dds_header():
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000
    pixel_format = struct.pack('<2I4s5I', 32, 4, b'DX10', 0, 0, 0, 0, 0)
    header = struct.pack('<4s7I44x', b'DDS ', 124, flags, H, W, W * H, 1, 1)
    header += pixel_format + struct.pack('<5I', 0x1000, 0, 0, 0, 0)
    return header + struct.pack('<5I', 98, 3, 0, 1, 1)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    icon, background = ASSETS/'icon.png', ASSETS/'background.png'
    with Image.open(icon) as art:
        if abs(art.width - art.height) > 2:
            raise SystemExit('The icon must be square')
        art.convert('RGB').resize((512, 512), Image.Resampling.LANCZOS).save(OUT/'icon0.png')
    with Image.open(background) as source:
        if abs(source.width / source.height - W / H) > 0.02:
            raise SystemExit('The background must be 16:9')
        source_size = source.size
        picture = source.convert('RGBA').resize((W, H), Image.Resampling.LANCZOS)
    picture.putalpha(255)
    params = etcpak.BC7CompressBlockParams()
    params.m_mode_mask = 1 << 1  # implicit opaque alpha; mode 6 can round it to 254
    params.m_uber_level = 2
    blocks = etcpak.compress_bc7(picture.tobytes(), W, H, params)
    if len(blocks) != W * H:
        raise SystemExit('Incorrect BC7 surface length')
    decoded = Image.frombytes('RGBA', (W, H), texture2ddecoder.decode_bc7(blocks, W, H), 'raw', 'BGRA')
    if decoded.getchannel('A').getextrema() != (255, 255):
        raise SystemExit('Unexpected background transparency')
    error = sum(ImageStat.Stat(ImageChops.difference(decoded.convert('RGB'), picture.convert('RGB'))).mean) / 3
    if error > 5:
        raise SystemExit('The BC7 decode differs too much from the source')
    payload = dds_header() + blocks
    for name in ('pic0.dds', 'pic1.dds'):
        (OUT/name).write_bytes(payload)
        if (OUT/name).read_bytes() != payload:
            raise SystemExit('DDS write check failed: ' + name)
    picture.convert('RGB').resize((1920, 1080), Image.Resampling.LANCZOS).save(OUT/'pic1.png')
    preview = ROOT/'build/presentation'
    preview.mkdir(parents=True, exist_ok=True)
    decoded.convert('RGB').resize((1920, 1080), Image.Resampling.LANCZOS).save(preview/'background-dds-preview.png')
    report = {
        'generator': 'built-in image_gen (codex exec)',
        'icon_source': {'file': icon.name, 'sha256': sha(icon)},
        'background_source': {'file': background.name, 'sha256': sha(background), 'size': list(source_size)},
        'background_output': {'size': [W, H], 'format': 'DX10 DDS BC7_UNORM, mode 1, opaque, one mip',
                              'decoder': 'texture2ddecoder', 'mean_absolute_rgb_error_255': round(error, 4)},
        'outputs': {n: {'size': (OUT/n).stat().st_size, 'sha256': sha(OUT/n)}
                    for n in ('icon0.png', 'pic0.dds', 'pic1.dds', 'pic1.png')},
    }
    (ASSETS/'presentation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
