"""abcheck.py ROM.a78 DUMP.bin [--bank N] [--list] : assert the Alien Brigade builder model on a RAM dump.

Re-runs f8:F56B in Python from the dump's draw list ($227D type / $22FF slot, grouped by zone,
$FF ends a zone, $FE = the zone's tile row) and slot arrays ($2615 x, $25A7 y, $245D flags,
$2381/$23EF script pointer, $24CB script offset), and compares the bytes with both list buffers
($1AB8 and $1CB8).  Prints the match count for each buffer; --list prints the draw list decoded.
"""
import sys

path, dump = sys.argv[1], sys.argv[2]
bank = 1
if "--bank" in sys.argv:
    bank = int(sys.argv[sys.argv.index("--bank") + 1])
rom = open(path, "rb").read()[128:]
ram = open(dump, "rb").read()


def rd(a):
    if a >= 0xC000:
        return rom[8 * 16384 + a - 0xC000]
    if a >= 0x8000:
        return rom[bank * 16384 + a - 0x8000]
    if a >= 0x4000:
        return rom[a - 0x4000]
    return ram[a]


def build():
    out = []
    zone = 0
    lists = [[]]
    for y in range(0x82):
        t = ram[0x227D + y]
        if t == 0xFF:
            lists[-1] += [0, 0]
            zone += 1
            if zone >= 10:
                break
            lists.append([])
            continue
        if t == 0xFE:
            lists[-1] += [ram[0x224E + zone], 0x60, ram[0x2258 + zone], ram[0x2262 + zone], (0xFF - ram[0x2110]) & 255]
            continue
        x = ram[0x22FF + y]
        if t == 0 and ram[0xD6] == 0:
            hx = 0x9F
        else:
            hx = ram[0x2615 + x]
        yy = ram[0x25A7 + x]
        if yy >= 0xA0:
            continue
        fine = yy & 15
        off = ram[0x245D + x] & 0x7F
        p = ((ram[0x2381 + x] + ram[0x24CB + x]) & 0xFFFF) + (ram[0x23EF + x] << 8)
        pw = rd(p)
        if pw < 0x10:
            continue
        lists[-1] += [rd(p + 1), pw, (rd(p + 2) + fine - off) & 255, hx]
    return lists


lists = build()
flat = []
for l in lists:
    flat += l
for base in (0x1AB8, 0x1CB8):
    got = list(ram[base:base + len(flat)])
    same = sum(1 for a, b in zip(got, flat) if a == b)
    print("buffer $%04X: %d of %d bytes match the model" % (base, same, len(flat)))
n = ram[0x2114]
print("draw list entries (ram_2114) %d, slots in use %d, pending spawns %d, scroll col %d fine %d" % (
    n, sum(1 for i in range(0x6E) if ram[0x245D + i] & 0x80), ram[0x211B], ram[0x2100], ram[0x2110]))
if "--list" in sys.argv:
    zone = 0
    for y in range(0x82):
        t = ram[0x227D + y]
        if t == 0xFF:
            print("  -- end of zone %d" % zone)
            zone += 1
            if zone >= 10:
                break
            continue
        if t == 0xFE:
            print("  [%02X] tile row" % y)
            continue
        x = ram[0x22FF + y]
        cls = rd(0xD000 + t) >> 4
        print("  [%02X] type $%02X class %2d slot %02X x %3d y %3d flags %02X script $%02X%02X+%02X hp %02X speed %02X xoff %d count %d" % (
            y, t, cls, x, ram[0x2615 + x], ram[0x25A7 + x], ram[0x245D + x], ram[0x23EF + x], ram[0x2381 + x],
            ram[0x24CB + x], ram[0x275F + x], ram[0x2683 + x], ram[0x26F1 + x], ram[0x2539 + x]))
