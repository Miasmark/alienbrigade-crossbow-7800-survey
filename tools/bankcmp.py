import sys, hashlib
d = open(sys.argv[1], 'rb').read()[128:]
bs = [d[i*16384:(i+1)*16384] for i in range(9)]
for i, b in enumerate(bs):
    print(i, hashlib.md5(b).hexdigest()[:8], [j for j in range(9) if j != i and bs[j] == b],
          'diff vs others:', [(j, sum(1 for x, y in zip(b, bs[j]) if x != y)) for j in range(9) if j != i and sum(1 for x, y in zip(b, bs[j]) if x != y) < 8000])
