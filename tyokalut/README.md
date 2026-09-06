# tyokalut/

Pakkojen rakennusskriptit. Nämä olivat aiemmin väliaikaiskansiossa, joka ei siirry koneelta
toiselle — siksi ne ovat nyt repossa.

## Mitä täällä on

| tiedosto | mitä tekee |
|---|---|
| `export_solu_L1_full.py` | rakentaa **Solu ja biomolekyylit, Luento 1** -pakan |
| `export_biotek_L1.py` | rakentaa **Johdatus biotekniikkaan, Luento 1** -pakan |
| `fix_solu_L1_fronts.py` | vanha etupuolten korjausskripti; solu-skripti lukee siitä kysymyskartan, joten **sitä ei saa poistaa** |
| `*.txt` | skriptien lukemaa dataa: laajat vastaukset, linkkisanat, kuvakortit, typokorjaukset, tenttitodennäköisyydet |
| `kuvat/` | luentokalvoilta poimitut kuvat kuvakortteja varten (169 kpl, ~78 MB) |

`kuvat/` on `.gitignore`ssa: se on luentomateriaalia eikä kuulu julkiseen repoon. Kansio siirtyy
silti koneelta toiselle, koska koko repo on OneDrivessa.

## Ajaminen

Vain Pythonin vakiokirjastoa, ei asennettavia paketteja.

```bash
python tyokalut/export_solu_L1_full.py
python tyokalut/export_biotek_L1.py
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
