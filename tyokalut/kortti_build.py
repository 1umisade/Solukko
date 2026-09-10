# -*- coding: utf-8 -*-
"""Rakentaa simulaatiot/kortti.html: Solukon molekyylipopupin kevyt sivu.

simulaatiot/index.html on koko simulaattori (13 000 rivia, 1 MB, Babylon 8 MB CDN:sta). Popup tarvitsee siita
vain jaetun osan (alkuainetaulut, mol2-parseri, shaderit, orbitaalikitti) ja runEditor-funktion. Tama skripti
leikkaa ne index.html:sta, jattaa katselijan (run) ja kayttoliittyman pois ja kirjoittaa kortti.html:n, joka
lataa oman tree-shaken Babylon-paketin (simulaatiot/babylon-kortti.js, ks. tyokalut/babylon_kortti_build.md).

AJA AINA, KUN simulaatiot/index.html MUUTTUU:  python tyokalut/kortti_build.py
kortti.html on generoitu tiedosto - ala muokkaa sita kasin."""
import io, os, re, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'simulaatiot', 'index.html'); OUT = os.path.join(REPO, 'simulaatiot', 'kortti.html')

s = io.open(SRC, encoding='utf-8', newline='').read()
NL = '\r\n' if s.count('\r\n') > 1000 else '\n'
L = s.split(NL)


def find1(pred, label):
    hits = [i for i, l in enumerate(L) if pred(l)]
    assert len(hits) == 1, '%s: %d osumaa' % (label, len(hits))
    return hits[0]


i_script = find1(lambda l: l.strip() == '<script>', '<script>')
i_run = find1(lambda l: l.startswith('async function run(){'), 'run()')
i_editor = find1(lambda l: l.startswith('function runEditor(){'), 'runEditor()')
i_dispatch = find1(lambda l: l.startswith('const startViewer = '), 'dispatch')
i_end = find1(lambda l: l.strip() == '</script>', '</script>')
assert i_script < i_run < i_editor < i_dispatch < i_end

shared = L[i_script + 1:i_run]      # alkuainetaulut, parseMol2, shaderit, mkOrbKit, buildAtomCard ...
editor = L[i_editor:i_dispatch]     # runEditor kokonaan
body = NL.join(shared + editor)

# kortti.html on aina kortti-tila, URL:sta riippumatta
n = body.count("new URLSearchParams(location.search).get('tila') === 'kortti'")
assert n == 1, 'KORTTI-tunnistus: %d osumaa' % n
body = body.replace("new URLSearchParams(location.search).get('tila') === 'kortti'", 'true')
n = body.count("if(new URLSearchParams(location.search).get('tila') !== 'kortti')")
assert n == 1, 'esilataus-ehto: %d osumaa' % n
body = body.replace("if(new URLSearchParams(location.search).get('tila') !== 'kortti')", 'if(false)')

# kanvaasin CSS index.html:sta (osoitinkuva mukaan lukien)
m = re.search(r'^#c\{[^\n]*\}', s.replace('\r', ''), re.M)
css_c = m.group(0) if m else '#c{width:100%;height:100%;display:block;touch-action:none}'

html = NL.join([
    '<!DOCTYPE html>',
    '<html lang="fi">',
    '<head>',
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<title>3D-malli</title>',
    '<!-- GENEROITU TIEDOSTO: tyokalut/kortti_build.py leikkaa taman simulaatiot/index.html:sta. Ala muokkaa kasin - aja skripti. -->',
    '<style>',
    'html,body{margin:0;height:100%;overflow:hidden;background:#f2e6c9}',
    css_c,
    '.stub{display:none !important}',
    '</style>',
    '</head>',
    '<body>',
    '<canvas id="c"></canvas>',
    # runEditor hakee nama id:t; kortti-tilassa ne eivat nay, mutta kuuntelijat kiinnittyvat niihin
    '<div id="overlay" class="stub"></div><div id="lista" class="stub"><div id="lista-items"></div></div><div id="haamu" class="stub"></div>',
    '<div id="valinta" class="stub"></div><div id="valintalaatikko" class="stub"></div>',
    '<button id="mode3d-btn" class="stub"></button><button id="resetview-btn" class="stub"></button><button id="eraser-btn" class="stub"></button>',
    '<input id="editorspeedsld" type="range" class="stub"><span id="editorspeedval" class="stub"></span>',
    '<script src="babylon-kortti.js"></script>',
    '<script>',
    body,
    "document.documentElement.classList.add('editori', 'kortti'); runEditor();",
    '</script>',
    '</body>',
    '</html>',
    ''])
io.open(OUT, 'w', encoding='utf-8', newline='').write(html)

# syntaksitarkistus
chk = os.path.join(tempfile.gettempdir(), 'kortti_chk.js')
io.open(chk, 'w', encoding='utf-8').write(body.replace(NL, '\n') + "\nrunEditor();\n")
r = subprocess.run(['node', '--check', chk], capture_output=True, text=True)
print('node --check:', 'OK' if r.returncode == 0 else r.stderr[:400])
print('kortti.html: %d rivia, %d kB (index.html %d kB)' % (html.count(NL), len(html.encode('utf-8')) // 1024, len(s.encode('utf-8')) // 1024))
