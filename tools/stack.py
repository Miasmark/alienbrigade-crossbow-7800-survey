import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f) for f in files]
w = max(i.size[0] for i in ims); h = sum(i.size[1] + 12 for i in ims)
s = Image.new("RGB", (w, h), (0, 60, 0)); d = ImageDraw.Draw(s); y = 0
for im, f in zip(ims, files):
    d.text((2, y), f.replace("\\", "/").split("/")[-1], fill=(255, 255, 0)); s.paste(im, (0, y + 12)); y += im.size[1] + 12
s.save(out)
