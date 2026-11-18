"""sheet.py OUT.png img1 img2 ... : contact sheet of snapshots (4 across), labelled by file name."""
import sys, os
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert("RGB") for f in files]
w, h = ims[0].size
cols = 4
rows = (len(ims) + cols - 1) // cols
sh = Image.new("RGB", (cols * w, rows * (h + 12)), (40, 40, 40))
d = ImageDraw.Draw(sh)
for i, (im, f) in enumerate(zip(ims, files)):
    x, y = (i % cols) * w, (i // cols) * (h + 12)
    sh.paste(im, (x, y + 12))
    d.text((x + 2, y), os.path.basename(f), fill=(255, 255, 0))
sh.save(out)
