"""xbcols.py ROM: Crossbow: for each scene bank, how far its columns $A0-$FF of pages $80-$9F and
$A0-$BF match the other scene banks (shared sprite columns), and the raw DLL bytes of a dump."""
import sys
rom = open(sys.argv[1], "rb").read()[128:]
def bank(b): return rom[b*16384:(b+1)*16384]
ref = bank(5)
for b in range(1, 9):
    d = bank(b)
    same = [0, 0, 0, 0]; tot = [0, 0, 0, 0]
    for page in range(64):
        for lo in range(256):
            q = (0 if page < 32 else 2) + (0 if lo < 0xA0 else 1)
            tot[q] += 1
            if d[page*256+lo] == ref[page*256+lo]: same[q] += 1
    print("bank %d vs bank 5: $80-$9F lo<$A0 %5.1f%%  lo>=$A0 %5.1f%% | $A0-$BF lo<$A0 %5.1f%%  lo>=$A0 %5.1f%%" % (
        b, *[100.0*s/t for s, t in zip(same, tot)]))
if len(sys.argv) > 2:
    ram = open(sys.argv[2], "rb").read()
    a = 0x23E0
    print(" ".join("%02X%02X%02X" % (ram[a+3*i], ram[a+3*i+1], ram[a+3*i+2]) for i in range(16)))
