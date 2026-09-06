# Solukko — mistä tässä on kyse

Perehdytys uudelle agentille. Lue tämä ennen kuin kosket mihinkään.
Työskentelytavat ovat `CLAUDE.md`:ssä, korttien sisältösäännöt `kurssit/CLAUDE.md`:ssä.

---

## Mikä tämä on

Suomenkielinen biokemian korttisivusto **solukko.com**. Käyttäjä on biokemian opiskelija Turun
yliopistossa ja tekee sivustoa omaan opiskeluunsa. Julkaisu tapahtuu GitHub Pagesista repostaan
`1umisade/Solukko`, haarasta `main` — **push mainiin julkaisee sivuston**.

Kortit tulevat käyttäjän omasta Ankista. Sivusto ei ole erillinen tietokanta: se lataa ja jäsentää
selaimessa repon juuressa olevan `SOLUKKO.apkg`:n, joka on suora vienti käyttäjän Anki-kokoelmasta.

---

## Tiedostot

| polku | mitä |
|---|---|
| `index.html` | **koko sivusto**, ~6800 riviä: HTML, CSS ja JS samassa tiedostossa. Ei build-vaihetta, ei riippuvuuksia npm:stä. |
| `SOLUKKO.apkg` | ~34 MB, 653 korttia / 649 muistiinpanoa. Sivuston ainoa tietolähde. |
| `tyokalut/` | pakkojen rakennusskriptit, oma `README.md`. |
| `kurssit/` | luentomateriaali (PDF, tallenteet, transkriptiot) ja valmiit pakkatiedostot. **Ei gitissä**, siirtyy OneDrivessa. |
| `kurssit/CLAUDE.md` | korttien teko-ohjeet: kenttärakenne, linkkisanat, termisanasto. Ainoa tiedosto, joka on `kurssit/`:sta gitissä. |
| `.claude/launch.json` | esikatselupalvelin (`python -m http.server 8753`). Ei gitissä. |

Repo on OneDrive-kansiossa, joten myös gitin ulkopuoliset osat siirtyvät koneelta toiselle. Pelkkä
`git clone` **ei** riitä: `kurssit/`, `tyokalut/kuvat/` ja `.claude/` jäisivät puuttumaan.

---

## Tekninen pohja

- Vanilla JS ja CSS, ei kehystä eikä käännöstä. Muutokset menevät suoraan `index.html`:ään.
- **JSZip + sql.js**: `.apkg` on zip, jonka sisällä `collection.anki21` on SQLite-kanta. Sivusto
  purkaa ja lukee sen selaimessa (`parseAnkiDB`).
- **Firebase** (compat-SDK, projekti `solukko`, anonyymi kirjautuminen). Firestore-kokoelmat:
  `userCards`, `comments`, `gamestate`, `chat`, `kuvaajat`, `joukkueet`, `prizes`, `presence`,
  `buzzers`. Säännöt `firestore.rules`.
- **Jäsennysvälimuisti**: jäsennetyt kortit tallennetaan IndexedDB:hen (`solukko-apkg`).
  Avain on `.apkg`:n etag + koko **+ jäsennysversio** `_JASENNYS`. Jos muutat `parseAnkiDB`:tä niin,
  että korttien sisältö muuttuu, **nosta `_JASENNYS`** — muuten paluukävijä jää vanhaan
  jäsennykseen. Tähän on jo kompastuttu kerran.

---

## Korttien sopimukset

Korttityyppi on **`Solukko`**, id `1727391050`, kuusi kenttää:

`Kysymys` · `Suppea vastaus` · `Laaja vastaus` · `tenttitodennäköisyys` · `3D-malli` · `linkkisanat`

- **Kaksivaiheinen paljastus:** kysymys → suppea → laaja. Laaja aukeaa *Laajenna*-napista tai
  välilyönnillä, ja teksti paljastuu animoituna ylhäältä alas.
- **Tenttitodennäköisyys** on numero: `3` perusasia, `2` syventävä tieto, `1` nippelitieto. Ei
  tähtiä, ei tageja.
- **linkkisanat** ovat sanalinkkien laukaisijat, kaikki taivutusmuodot. Vain termikorteissa, ja
  **vain yhdellä kortilla per termi** — muuten linkitys menee sekaisin. Linkit toimivat pakkojen ja
  kurssien välillä.
- **Kysymys alkaa järjestysnumerolla** `(1.007)`. Se on korttien järjestys pakassa ja näkyy vain
  Ankissa: sivusto lukee sen lajitteluavaimeksi ja riisuu sen sekä näytettävästä kysymyksestä että
  itse kentästä. Numeroimattomat kortit menevät numeroitujen jälkeen entisessä järjestyksessään.
- **Kansikortti** on kortti, jonka Kysymys on `Esittely`. Se on pakan kansiteksti, ei ruudukossa
  eikä järjestyksessä, eikä sille anneta numeroa eikä linkkisanoja.
- **`Kutsutaan myös: ...`** laajan vastauksen lopussa kertoo termin rinnakkaiset nimitykset. Ne
  eivät kuulu leipätekstiin.
- Mitat: suppea ≤ 15 sanaa, laaja 45–65 sanaa. Ei puolipisteitä, käytä pistettä.
- Termistö on lyöty lukkoon (`lähetti-RNA` ei `mRNA`, `tuma` ei `nucleus`, `solulima` ei
  `sytoplasma`, `genomi` ei `perimä`, …). Koko taulukko on `kurssit/CLAUDE.md` §10.

**Pakkapuu koodaa lukuvuoden, lukukauden ja periodin:**

```
SOLUKKO::1. LUKUVUOSI::1.1 SYKSY::1. Periodi::Solu- ja biomolekyylit - teoria (BKEM5030)::Luento 1 - Elämä, perusteet ja periaatteet
```

Sivusto lukee vuoden, lukukauden ja periodin suoraan tästä polusta. Periodi on se, **jossa kurssi
alkaa** (syksy 1–2, kevät 3–5).

---

## Työjärjestys

Kaikki sisältömuutokset kulkevat Ankin kautta. Järjestys on aina sama:

1. Käyttäjä vie `SOLUKKO.apkg`:n Ankista repon juureen
2. Aja rakennusskripti → syntyy pakkatiedosto `kurssit/<kurssi>/`-kansioon
3. Käyttäjä tuo sen Ankiin
4. Käyttäjä vie `SOLUKKO.apkg`:n uudelleen
5. Committaa ja pushaa → sivusto päivittyy

**Tarkista aina exportin aikaleima** ennen kuin rakennat. Jos rakennat vanhentuneesta lähteestä,
tuonti kumoaa käyttäjän sen jälkeen tekemät muokkaukset.

Pienet korjaukset voi tehdä myös suoraan `SOLUKKO.apkg`:hen, mutta ne katoavat seuraavassa
viennissä Ankista. Pysyvä muutos vaatii aina kierroksen Ankin kautta.

---

## Anki-tuonnin lainalaisuudet

Nämä on opittu kantapään kautta. Älä oleta muuta:

- **Tuonti ei koskaan poista mitään.** Kortin poisto tapahtuu vain Ankissa käsin.
- **Muistiinpanot tunnistetaan guidista.** Guid säilyy → tuonti päivittää kortin paikallaan, ei
  tee kaksoiskappaletta. Tämän takia skriptit muokkaavat käyttäjän omaa kantaa eivätkä rakenna
  kortteja tyhjästä.
- **Tuonti ei nimeä pakkoja uudelleen.** Olemassa olevan kortin pakka ei muutu.
- **Tuonti ei muuta korttitunnuksia.** Siksi ruudukon järjestystä ei voi muuttaa tunnuksia
  numeroimalla — siihen on järjestysnumero kysymyksen alussa.
- **Korttityyppi tunnistetaan tunnuksesta, ei nimestä.** Jos tuotavan tiedoston nimi eroaa
  kokoelman nimestä samalla tunnuksella, Anki tekee kopion `+`-päätteellä. Näin syntyivät aikanaan
  `Solukko+` ja `Solukko++`. **Älä koskaan nimeä korttityyppiä uudelleen exportissa** — ota nimi
  käyttäjän kokoelmasta.
- **Image Occlusion -korttityypeissä ensimmäinen kenttä ei ole kysymys** vaan peittodataa. Älä
  koskaan kirjoita sen alkuun mitään.

---

## Sudenkuopat skripteissä

- **Kysymystekstiin perustuvat vertailut on riisuttava järjestysnumerosta.** Skripteissä on apuri
  `_kys()`, joka poistaa sekä tagit että numeron. Kun tämä unohtui, kaksoiskappaletarkistus lakkasi
  tunnistamasta pakassa jo olevia kortteja ja lisäsi 14 korttia uudestaan.
- **Biotek-skripti lukee oman edellisen tulostiedostonsa.** Lähde ja kohde ovat sama tiedosto, joten
  virheellinen ajo jää elämään. Solu-skripti lukee `SOLUKKO.apkg`:n eli on turvallisempi.
- **Bash-työkalu sotkee kenoviivat heredocissa.** Jos patch-skriptissä on `\n`, `\t` tai `\x1f`,
  kirjoita se Write-työkalulla tiedostoon äläkä putkita heredocilla.
- Kirjoita skriptit **idempotenteiksi** ja aja ne kahdesti peräkkäin: toisen ajon pitää olla no-op.

---

## Muutoksen todentaminen

- Käynnistä esikatselu `.claude/launch.json`in nimellä `solukko` ja aja tarkistukset selaimessa.
- **Tyhjennä IndexedDB** (`solukko-apkg`) ennen kuin uskot näkeväsi uuden jäsennyksen.
- Selainpaneelin ollessa piilotettuna Chrome kuristaa ruudunpiirron: CSS-siirtymien kello ei etene
  eivätkä animaatiot näy mittauksissa. Todenna animaatio siirtymäobjektista
  (`element.getAnimations()`), älä näytteistämällä.
- Tuotannon voi tarkistaa `curl -sI https://solukko.com/SOLUKKO.apkg` — `content-length` kertoo,
  onko livenä sama tiedosto kuin paikallisesti.

---

## Vakiintuneet tavat

- **Ei selaimen `prompt()`, `confirm()` tai `alert()` -ikkunoita.** Kaikki vuorovaikutus tehdään
  sivun omalla käyttöliittymällä.
- Uudet kuva- ja äänitiedostot on **lisättävä gittiin**, tai ne toimivat paikallisesti mutta
  antavat 404:n solukko.comissa.
- Käyttöliittymän tekstit ja korttisisältö ovat suomeksi, koodin kommentit englanniksi.
- Käyttäjä lukee vastaukset suomeksi.
