"""abtypes.py ROM.a78 [--bank N] [--type T ...] [--all] : Alien Brigade object types and their scripts.

Type tables in the fixed bank (file bank 8, $C000-$FFFF), indexed by type id T (code: f8:F687):
  $D000,T  bits 0-1 cells-1 (1..3 cells of 16 lines, stacked downward)
           bit 2 "one zone only", bit 3 "one zone when y is on the 16-line grid"
           bits 4-7 draw class (higher = later in a zone's list = in front)
  $D100,T  low nibble: hit box half-width class (f8:F2F1)   $D200,T  -> $275F,slot (primary flag / hit points)
  $D300,T  $D400,T  $D500,T  $D600,T  hit/score parameters (see FINDINGS)
  $D700+2T (word)  script of cell 0     $D900+2T  script of cell 1 (hi 0 = none)    $DB00+2T  cell 2
A script is a byte stream (interpreter f8:FB10 / f8:FBFE).  First byte >= $10: a frame record
  [palette<<5 | (32-width)&31, gfx lo, gfx hi, dx, dy]   (dx, dy signed, applied when the frame is left)
First byte < $10: a command (see OPS below).
Pointers below $C000 are read from --bank (default 1: level 1's bank).
"""
import sys

OPS = {
    0x00: ("nop", 0), 0x01: ("mark", 0), 0x02: ("loop", 0), 0x03: ("repeat", 1), 0x04: ("restart", 0),
    0x05: ("fx", 2), 0x06: ("setcount", 1), 0x07: ("inc", 1), 0x08: ("clr", 1), 0x09: ("killtype", 1),
    0x0A: ("xoff", 1), 0x0B: ("randskip", 2), 0x0C: ("spawn", 4), 0x0D: ("become", 4),
    0x0E: ("die_all", 0), 0x0F: ("die", 0),
}


def s8(v):
    return v - 256 if v >= 128 else v


class Rom:
    def __init__(self, path, bank):
        self.d = open(path, "rb").read()[128:]
        self.bank = bank

    def rd(self, a):
        if a >= 0xC000:
            return self.d[8 * 16384 + a - 0xC000]
        if a >= 0x8000:
            return self.d[self.bank * 16384 + a - 0x8000]
        if a >= 0x4000:
            return self.d[a - 0x4000]
        return 0


def script(rom, ptr, maxlen=256):
    out = []
    i = 0
    frames = 0
    while i < maxlen:
        b = rom.rd(ptr + i)
        if b >= 0x10:
            pw, lo, hi, dx, dy = [rom.rd(ptr + i + k) for k in range(5)]
            out.append("%02X: frame gfx $%02X%02X w%-2d pal %d  dx %+d dy %+d" % (
                i, hi, lo, 32 - (pw & 31), pw >> 5, s8(dx), s8(dy)))
            i += 5
            frames += 1
            continue
        name, n = OPS[b]
        args = [rom.rd(ptr + i + 1 + k) for k in range(n)]
        if b == 0x0B:
            out.append("%02X: randskip mask[%d] +%d -> %02X" % (i, args[0], args[1], i + 2 + args[1] + 1))
        elif b in (0x0C, 0x0D):
            out.append("%02X: %s type $%02X at %+d,%+d speed %d" % (i, name, args[0], s8(args[1]), s8(args[2]), args[3]))
        else:
            out.append("%02X: %s %s" % (i, name, " ".join("%02X" % a for a in args)))
        i += 1 + n
        if b in (0x02, 0x04, 0x0D, 0x0E, 0x0F):
            # an unconditional end of flow; stop unless something can skip past it
            nxt = rom.rd(ptr + i)
            if not any("randskip" in l or "repeat" in l for l in out[-12:]):
                break
            if nxt == 0 and rom.rd(ptr + i + 1) == 0:
                break
    return out, i


def main():
    args = sys.argv[1:]
    bank = 1
    types = []
    allt = False
    path = args[0]
    i = 1
    while i < len(args):
        if args[i] == "--bank":
            bank = int(args[i + 1]); i += 2
        elif args[i] == "--type":
            types.append(int(args[i + 1], 16)); i += 2
        elif args[i] == "--all":
            allt = True; i += 1
        else:
            i += 1
    rom = Rom(path, bank)
    if allt:
        types = list(range(256))
    print("bank %d" % bank)
    for t in types:
        f = rom.rd(0xD000 + t)
        ptrs = [rom.rd(0xD700 + 2 * t) | rom.rd(0xD701 + 2 * t) << 8,
                rom.rd(0xD900 + 2 * t) | rom.rd(0xD901 + 2 * t) << 8,
                rom.rd(0xDB00 + 2 * t) | rom.rd(0xDC00 - 0x100 + 0x100 + 2 * t - 0x100 + 0x101) << 8]
        ptrs[2] = rom.rd(0xDB00 + 2 * t) | rom.rd(0xDB01 + 2 * t) << 8
        print("type $%02X  cells %d  zoneflags %d  class %d  D100 %02X D200 %02X D300 %02X D400 %02X D500 %02X D600 %02X  scripts %s" % (
            t, (f & 3) + 1, (f >> 2) & 3, f >> 4, rom.rd(0xD100 + t), rom.rd(0xD200 + t), rom.rd(0xD300 + t),
            rom.rd(0xD400 + t), rom.rd(0xD500 + t), rom.rd(0xD600 + t), " ".join("$%04X" % p for p in ptrs)))
        if not allt or "--scripts" in args:
            for c in range((f & 3) + 1):
                if ptrs[c] >> 8 == 0:
                    continue
                lines, n = script(rom, ptrs[c])
                print("  cell %d script $%04X (%d bytes)" % (c, ptrs[c], n))
                for l in lines:
                    print("    " + l)


if __name__ == "__main__":
    main()
