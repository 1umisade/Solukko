# -*- coding: utf-8 -*-
"""Laatan (kaukotason) pilkkutekstuurit. Kaksi kayttoa:
  python tyokalut/laatta_tee.py                       -> generoi saumattomat vara-tekstuurit laatta_keltainen.jpg ja laatta_vihrea.jpg
  python tyokalut/laatta_tee.py kuva.png laatta_vihrea.jpg   -> tekee omistajan ruutukaappauksesta saumattoman 1024 px laatan (JPEG - PNG-pilkkukuva olisi 1.8 MB)
Pilkkutiheys: noin 180 pilkkua laatan sivulla (yksi pilkku = yksi lipidi, shaderin laatta() olettaa 180).
"""
import os, sys
import numpy as np
from PIL import Image
SC = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(SC), 'simulaatiot')

def saumaton(src, dst, size=1024, band=0.12):
    im = Image.open(src).convert('RGB')
    w, h = im.size; n = min(w, h); im = im.crop(((w-n)//2, (h-n)//2, (w-n)//2+n, (h-n)//2+n)).resize((size, size), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32); b = int(size*band)
    r = np.linspace(0, 1, b, dtype=np.float32)   # crossfade the right edge over the left and the bottom over the top
    out = a.copy()
    out[:, :b] = a[:, :b]*r[None, :, None] + a[:, size-b:]*(1-r[None, :, None])
    out[:, size-b:] = out[:, :b][:, ::-1] if False else a[:, size-b:]*r[None, ::-1, None] + a[:, :b]*(1-r[None, ::-1, None])
    a2 = out.copy(); out[:b] = a2[:b]*r[:, None, None] + a2[size-b:]*(1-r[:, None, None])
    out[size-b:] = a2[size-b:]*r[::-1, None, None] + a2[:b]*(1-r[::-1, None, None])
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst, quality=88, optimize=True); print('kirjoitettu', dst)

def generoi(dst, base, dots, dark, n=180, size=1024, seed=1):
    rng = np.random.default_rng(seed); S = size*2   # render at 2x, then downsample for soft edges
    img = np.zeros((S, S, 3), np.float32); img[:] = base
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); pitch = S/n
    cx = (np.arange(n)+0.5)*pitch; cy = (np.arange(n)+0.5)*pitch
    for j in range(n):
        for i in range(n):
            x = cx[i] + rng.uniform(-0.35, 0.35)*pitch; y = cy[j] + rng.uniform(-0.35, 0.35)*pitch
            if rng.random() < 0.42: continue   # not every cell has a dark dot: the picture is mostly base tone
            rad = pitch*rng.uniform(0.28, 0.5); col = dots[rng.integers(len(dots))]
            x0, x1 = int(x-rad-2), int(x+rad+3); y0, y1 = int(y-rad-2), int(y+rad+3)
            for oy in (0, S, -S):
                for ox in (0, S, -S):   # wraparound -> seamless
                    ys, xs = slice(max(0, y0+oy), min(S, y1+oy)), slice(max(0, x0+ox), min(S, x1+ox))
                    if ys.start >= ys.stop or xs.start >= xs.stop: continue
                    d = np.hypot(xx[ys, xs]-(x+ox), yy[ys, xs]-(y+oy))
                    m = np.clip(rad+0.5-d, 0, 1)[..., None]; e = np.clip(1.2-np.abs(d-rad), 0, 1)[..., None]*0.55   # disc, then a thin dark rim
                    img[ys, xs] = img[ys, xs]*(1-m) + np.array(col, np.float32)*m
                    img[ys, xs] = img[ys, xs]*(1-e) + np.array(dark, np.float32)*e
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
    im.save(dst, quality=88, optimize=True); print('kirjoitettu', dst)

if __name__ == '__main__':
    if len(sys.argv) == 3: saumaton(sys.argv[1], sys.argv[2])
    else:
        generoi(os.path.join(OUT, 'laatta_keltainen.jpg'), (232, 183, 52), [(208, 138, 34), (199, 122, 26), (222, 160, 44)], (90, 60, 12), seed=1)
        generoi(os.path.join(OUT, 'laatta_vihrea.jpg'), (91, 178, 72), [(75, 127, 46), (62, 106, 40), (84, 150, 60)], (46, 74, 26), seed=2)
