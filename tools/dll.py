"""dll.py DUMP.bin [--dll ADDR] [--brief] : decode the display list list and lists in a RAM dump.

DUMP.bin is RAM $0000-$27FF as probe.lua writes it; the DLL address comes from the sidecar
.txt (reg 2C = DPPH, reg 30 = DPPL) unless --dll is given.  Each zone: first line, height, DLI,
holey bits, list address, then each header (gfx address, palette, width in bytes, x, 4/5 byte,
write mode, indirect).  --brief prints one line per zone with the object count and list bytes.
"""
import sys


def decode(ram, dll, out=print, brief=False, maxzones=64):
    line = 0
    a = dll
    stats = []
    for z in range(maxzones):
        b0, hi, lo = ram[a], ram[a + 1], ram[a + 2]
        h = (b0 & 15) + 1
        dl = hi << 8 | lo
        ents = []
        p = dl
        n = 0
        while p < len(ram) - 5 and n < 64:
            b1 = ram[p + 1]
            if b1 == 0:
                break
            if b1 & 0x1F == 0:
                g = ram[p + 2] << 8 | ram[p]
                pal = ram[p + 3] >> 5
                w = 32 - (ram[p + 3] & 31)
                x = ram[p + 4]
                ents.append((p, g, pal, w, x, 5, b1 >> 7, (b1 >> 5) & 1))
                p += 5
            else:
                g = ram[p + 2] << 8 | ram[p]
                pal = b1 >> 5
                w = 32 - (b1 & 31)
                x = ram[p + 3]
                ents.append((p, g, pal, w, x, 4, None, 0))
                p += 4
            n += 1
        nbytes = p + 2 - dl
        flags = ("DLI " if b0 & 0x80 else "") + ("H16 " if b0 & 0x40 else "") + ("H8 " if b0 & 0x20 else "")
        if brief:
            out("z%02d line %3d h%2d %-8s dl $%04X  %2d objs %3d bytes, gfx bytes %d" % (
                z, line, h, flags, dl, len(ents), nbytes, sum(e[3] for e in ents)))
        else:
            out("zone %2d  line %3d  h %2d  %s dl $%04X (DLL entry $%04X)" % (z, line, h, flags, dl, a))
            for (p, g, pal, w, x, n5, wm, ind) in ents:
                out("    $%04X: gfx $%04X pal %d w %2d x %3d  %d-byte%s%s" % (
                    p, g, pal, w, x, n5, "" if wm is None else " wm%d" % wm, " IND" if ind else ""))
        stats.append((z, line, h, b0, dl, ents))
        line += h
        a += 3
        if line >= 243:
            break
    return stats


def main():
    path = sys.argv[1]
    ram = open(path, "rb").read()
    dll = None
    brief = "--brief" in sys.argv
    if "--dll" in sys.argv:
        dll = int(sys.argv[sys.argv.index("--dll") + 1], 16)
    else:
        regs = {}
        for l in open(path[:-4] + ".txt"):
            if l.startswith("reg"):
                p = l.split()
                regs[int(p[1], 16)] = int(p[3], 16)
        dll = regs[0x2C] << 8 | regs[0x30]
    print("DLL at $%04X" % dll)
    decode(ram, dll, brief=brief)


if __name__ == "__main__":
    main()
