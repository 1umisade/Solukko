# babylon-kortti.js - popupin Babylon-paketti

`simulaatiot/babylon-kortti.js` on tree-shaken Babylon.js 9.26.0, jossa on vain popupin (`simulaatiot/kortti.html`)
kayttamat osat: 1,2 MB (300 kB gzip) CDN:n 8,3 MB:n (1,8 MB gzip) sijaan. Se paljastaa `window.BABYLON`-olion,
jossa on tasmalleen ne luokat, joita `runEditor` ja jaettu koodi kayttavat (`tyokalut/babylon_kortti_entry.js`).

## Rakentaminen (vain kun entry muuttuu tai Babylon paivitetaan)

```bash
mkdir -p /tmp/bb && cd /tmp/bb
npm init -y >/dev/null && npm i @babylonjs/core@9.26.0 esbuild
cp <repo>/tyokalut/babylon_kortti_entry.js entry.js
npx esbuild entry.js --bundle --minify --format=iife --target=es2020 --outfile=<repo>/simulaatiot/babylon-kortti.js
```

Version on oltava sama kuin `simulaatiot/index.html`:n CDN-Babylon (tarkista `BABYLON.Engine.Version` konsolista),
muuten editori ja popup voivat kayttaytya eri tavoin.

## Kun editori alkaa kayttaa uutta BABYLON.-luokkaa

Tarkista: `grep -o "BABYLON\.[A-Za-z]*" simulaatiot/index.html | sort -u` (jaettu osa + runEditor) ja lisaa puuttuva
import ja `window.BABYLON`-kentta entryyn. Puuttuva luokka nakyy popupissa virheena `BABYLON.X is not a constructor`.
Sivuvaikutus-importit (thinInstanceMesh, Culling/ray, Animations/animatable, engine.*-laajennukset) ovat
tarpeen, koska tree-shaken Babylon ei lataa niita itsestaan.
