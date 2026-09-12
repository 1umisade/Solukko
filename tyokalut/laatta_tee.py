# -*- coding: utf-8 -*-
"""Laatan (kaukotason) kuva omistajan omasta kuvasta - mitaan ei generoida (omistaja 12.9.2026).
  python tyokalut/laatta_tee.py green_membrane_slab.png simulaatiot/laatta_vihrea.jpg
  -> rajaa kuvan neliöksi, skaalaa 1024 px:iin ja ristihaivyttaa reunat (12 % kaista) niin etta laatta toistuu saumatta.
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

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit('kaytto: python tyokalut/laatta_tee.py kuva.png simulaatiot/laatta_vihrea.jpg')
    saumaton(sys.argv[1], sys.argv[2])
