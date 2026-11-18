"""xtmerge.py SRCDIR ANNOTATIONS.json LOG [LOG...] : executed addresses (X lines of exectrace logs)
that the listing in SRCDIR does not show as an instruction start are added to the annotations'
"entries" (run-start addresses only: an executed address whose predecessor in the log was also
missing is skipped when it directly follows it, to keep the list short).  Prints counts per space.
"""
import json
import os
import re
import sys

src, ann = sys.argv[1], sys.argv[2]
logs = sys.argv[3:]
code = set()
for fn in os.listdir(src):
    if not fn.endswith(".asm"):
        continue
    sp = fn[:-4]
    for l in open(os.path.join(src, fn), encoding="utf-8", errors="replace"):
        m = re.search(r"; ([0-9A-F]{4}): ([0-9A-F]{2})( [0-9A-F]{2})*", l)
        if m and not l.lstrip().startswith(".byte"):
            code.add("%s:%s" % (sp, m.group(1)))
xs = set()
for lg in logs:
    for l in open(lg):
        if l.startswith("X "):
            xs.add(l.split()[1])
missing = sorted(x for x in xs if x not in code and not x.startswith("ram"))
per = {}
for m in missing:
    per[m[:2]] = per.get(m[:2], 0) + 1
print("executed %d, in listing %d, missing %d %s" % (len(xs), len(xs) - len(missing), len(missing), per))
a = json.load(open(ann))
ent = a.setdefault("entries", [])
have = set(ent)
added = 0
for m in missing:
    if m not in have:
        ent.append(m)
        added += 1
json.dump(a, open(ann, "w"), indent=2)
print("added %d entries" % added)
