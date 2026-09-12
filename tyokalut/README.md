# tyokalut/

Pakkojen rakennusskriptit. Nämä olivat aiemmin väliaikaiskansiossa, joka ei siirry koneelta
toiselle — siksi ne ovat nyt repossa.

## Mitä täällä on

| tiedosto | mitä tekee |
|---|---|
| `export_solu_L1_full.py` | rakentaa **Solu ja biomolekyylit, Luento 1** -pakan |
| `export_biotek_L1.py` | rakentaa **Johdatus biotekniikkaan, Luento 1** -pakan |
| `export_solu_L2_vesi.py` | rakentaa **Solu ja biomolekyylit, Luento 2 - Vesi** -pakan tyhjästä; kortit ovat `vesi_L2_kortit*.py`-tiedostoissa |
| `fix_solu_L1_fronts.py` | vanha etupuolten korjausskripti; solu-skripti lukee siitä kysymyskartan, joten **sitä ei saa poistaa** |
| `ryhmat_3d.py` | funktionaalisten ryhmien 24 mallimolekyyliä (etanoli, asetoni, metaanitioli…) simulaattoriin ja popupiin: mol2 RDKitillä SMILESistä, SMALL/NAME_FI/FORMULA-taulut, `smiles.json`, `molekyylit.json` (nimen sijamuodot). Idempotentti. Aja sitten `kaava2d.py` ja `kortti_build.py` |
| `ryhmat_kortit.py` | 25 funktionaalisen ryhmän termikorttia Solu L1:een kortin 1.092 perään (numerot 1.0921–1.0945): patchaa `SOLUKKO.apkg`:n ja kirjoittaa `kurssit/BKEM5030 …/Luento 1 - Funktionaaliset ryhmat (lisays).apkg` (vain nämä kortit, guidit pysyvät). `3D-malli`-kenttä = mallimolekyylin avain |
| `biotek_kortit.py` | **Johdatus biotekniikkaan, Luennot 2 ja 3** (proteiinit biotekniikassa, in vitro -diagnostiikka): kortit `biotek_L2_kortit.py` ja `biotek_L3_kortit.py`, taivutusapuri `biotek_taivutus.py`. Patchaa `SOLUKKO.apkg`:n (luo pakat, lisää kortit ja kuvat) ja kirjoittaa luentopakat kurssin kansioon. Kuvat renderöidään dioista `kuvat/`-kansioon. Idempotentti |
| `kaava2d.py` | piirtää molekyylien 2D-kaavat popupin 2D-asentoon sarjakuvatyylillä (punainen vdW-hehku, värilliset atomipallot, kaikki vedyt) `simulaatiot/kortit/2d/`-kansioon. Lähde `smiles.json` (PubChem), 2D-koordinaatit RDKitillä (`pip install rdkit`) |
| `numeroi_kokoelma.py` | antaa jarjestysnumeron `(1)` kaikille kokoelman korteille, joilta se puuttuu |
| `*.txt` | skriptien lukemaa dataa: laajat vastaukset, linkkisanat, kuvakortit, typokorjaukset, tenttitodennäköisyydet |
| `kuvat/` | luentokalvoilta poimitut kuvat kuvakortteja varten (169 kpl, ~78 MB) |

`kuvat/` on `.gitignore`ssa: se on luentomateriaalia eikä kuulu julkiseen repoon. Kansio siirtyy
silti koneelta toiselle, koska koko repo on OneDrivessa.

## Ajaminen

Vain Pythonin vakiokirjastoa, ei asennettavia paketteja.

```bash
python tyokalut/export_solu_L1_full.py
python tyokalut/export_biotek_L1.py
python tyokalut/export_solu_L2_vesi.py
```

Polut johdetaan skriptin omasta sijainnista, joten mitään ei tarvitse muokata uudella koneella —
kunhan `tyokalut/` pysyy repon juuressa.

## Mistä mihin

Solu-skriptin **lähde on repon juuren `SOLUKKO.apkg`**, eli sinun Anki-vientisi. Se poimii sieltä
oman pakkansa, tekee muutokset ja kirjoittaa tuloksen kurssin kansioon:

```
SOLUKKO.apkg  →  kurssit/BKEM5030 Solu- ja biomolekyylit - teoria/Luento 1 - Elämän perusperiaatteet.apkg
```

Biotek-skripti lukee ja kirjoittaa **oman tulostiedostonsa** kurssin kansiossa, mutta hakee
korttityypin nimen `SOLUKKO.apkg`:sta, jottei tuonti tee Ankiin nimikopiota.

Työjärjestys on aina sama: vie SOLUKKO.apkg Ankista → aja skripti → tuo syntynyt pakka Ankiin →
vie SOLUKKO.apkg uudelleen → committaa se.

Muistiinpanojen guidit säilyvät, joten tuonti **päivittää kortit paikallaan** eikä tee
kaksoiskappaleita.

## Uudella koneella

Repo on OneDrivessa, joten kaikki siirtyy sitä kautta — myös `kurssit/` ja `.claude/`, jotka eivät
ole gitissä. Jos kloonaat pelkän gitin, ne jäävät puuttumaan eivätkä skriptit löydä
kurssimateriaalia.

Tarvitset vain Pythonin. Esikatselupalvelin käynnistyy `.claude/launch.json`in mukaan komennolla
`python -m http.server 8753`.
