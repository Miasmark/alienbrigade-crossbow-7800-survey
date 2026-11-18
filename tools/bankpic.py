"""bankpic.py ROM.a78 OUTDIR [zoneheight=16] : one picture per 16K file bank, drawn as MARIA would
read it in zones of the given height: each block of <zoneheight> pages is one strip, the block's
highest page at the top (the zone offset counts down), 256 bytes across = 1024 160A pixels
(drawn 2 px wide each? no: 1 px per 160A pixel, so 1024 wide).  Grey 4-level palette.
Code shows as noise; art shows as pictures.  A second picture <bank>_w.png draws 160B-style
(4bpp) pairs to help spot 160B art.
"""
import os
import sys
from PIL import Image

rom = open(sys.argv[1], "rb").read()[128:]
out = sys.argv[2]
zh = int(sys.argv[3]) if len(sys.argv) > 3 else 16
os.makedirs(out, exist_ok=True)
PAL = [(0, 0, 0), (90, 90, 200), (220, 120, 60), (255, 255, 255)]
nb = len(rom) // 16384
for b in range(nb):
    d = rom[b * 16384:(b + 1) * 16384]
    pages = 64
    blocks = pages // zh
    im = Image.new("RGB", (1024, blocks * (zh + 2)), (60, 0, 60))
    px = im.load()
    for blk in range(blocks):
        for ln in range(zh):
            page = blk * zh + (zh - 1 - ln)
            y = blk * (zh + 2) + ln
            row = d[page * 256:(page + 1) * 256]
            for i, v in enumerate(row):
                for k in range(4):
                    c = (v >> (6 - 2 * k)) & 3
                    px[i * 4 + k, y] = PAL[c]
    im = im.resize((1024, im.size[1] * 2), Image.NEAREST)
    im.save(os.path.join(out, "bank%d_h%d.png" % (b, zh)))
print("wrote", nb, "pictures to", out)
