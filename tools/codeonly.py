"""codeonly.py FILE.asm [FROM TO]: print only instruction/label lines (no .byte rows), compact;
data runs are summarised as one line with their address range."""
import sys, re
f = sys.argv[1]
lo = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0
hi = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0xFFFF
cur = 0; dstart = None; dlast = None
def flush():
    global dstart
    if dstart is not None and lo <= dstart <= hi:
        print("    ; data %04X-%04X" % (dstart, dlast))
    dstart = None
for l in open(f, encoding="utf-8", errors="replace"):
    l = l.rstrip("\n")
    m = re.search(r"; ([0-9A-F]{4})[: ]", l)
    if l.lstrip().startswith(".byte") or l.lstrip().startswith(".word"):
        if m:
            a = int(m.group(1), 16); cur = a
            if dstart is None: dstart = a
            dlast = a + 15
        continue
    if m: cur = int(m.group(1), 16)
    if l.startswith("; xrefs") or not l.strip(): 
        if lo <= cur <= hi and l.strip(): pass
        else: continue
    flush()
    if lo <= cur <= hi:
        l = re.sub(r"\s+;\s+([0-9A-F]{4}): [0-9A-F ]+?\s+(\d\+?)(\s|$)", r"  ; \1 ", l)
        l = re.sub(r"^    (\w+)\s+", r"    \1 ", l)
        print(l[:130])
flush()
