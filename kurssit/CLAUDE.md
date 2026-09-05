# Korttien teko-ohjeet (kurssit/)

Ohjeet Anki-korttien tekemiseen Solukkoon. Noudata näitä aina, kun rakennat tai päivität kurssipakkoja.

---

## 1. Lähde: aina käyttäjän nykyiset kortit

**Älä koskaan rakenna vanhasta build-skriptistä.** Käyttäjä muokkaa ja lisää kortteja Ankissa, joten
skriptistä rakentaminen hukkaa hänen työnsä.

1. Pura pakan nykyiset kortit repon juuren `SOLUKKO.apkg`:sta (käyttäjän Anki-export).
2. Muokkaa niitä.
3. **Säilytä jokaisen muistiinpanon `guid`** → tuonti *päivittää kortit paikallaan*: ei duplikaatteja,
   kertaushistoria säilyy.

Turvallisin tapa tuottaa päivitetty pakka: kopioi `SOLUKKO.apkg`, muokkaa `collection.anki21`-tietokantaa
suoraan (SQL), poista muut pakat ja pakkaa uudelleen. Näin korttityypit, guidit, aikataulut ja media
säilyvät bitilleen — eikä Anki ohita kortteja tyyppiristiriidan takia.

> Jos rakennat genankilla, **korttityypin on vastattava käyttäjän kokoelmaa täsmälleen**
> (sama id, nimi, kenttien nimet ja järjestys, sama css). Muuten Anki ohittaa kaikki kortit.
> Kentän tai tyypin uudelleennimeäminen tehdään Ankissa käsin, ei tuonnin kautta.

---

## 2. Korttityyppi: yksi ainoa, **ilman ääkkösiä kenttänimissä**

Nimi: **`Solukko`**

| # | Kenttä | Sisältö |
|---|--------|---------|
| 1 | `Kysymys` | Kortin etupuoli — **aina kysymysmuodossa** |
| 2 | `Suppea vastaus` | Yksi lyhyt lause (ydin, ≤ ~15 sanaa) |
| 3 | `Laaja vastaus` | Täysi, tenttikelpoinen vastaus |
| 4 | `tenttitodennakoisyys` | **`1`, `2` tai `3`** — pelkkä numero, ei tähtimerkkejä |
| 5 | `3D-malli` | Valinnainen mallin nimi (upotetaan kortin etupuolelle) |
| 6 | `linkkisanat` | Sanalinkkien laukaisijat — **vain termikorteissa** |

Kortin malli (template):
- etupuoli: `{{Kysymys}}`
- takapuoli: `{{FrontSide}}<hr id="answer">{{Laaja vastaus}}<hr>{{Suppea vastaus}}`

Sivusto paljastaa vastauksen kaksivaiheisesti: **Kysymys → (väli) Suppea → (väli) Laaja** (toggle).

---

## 3. Etupuoli on aina kysymys

Termikortinkin etupuoli on kysymys, ei paljas termi. Termi elää `linkkisanat`-kentässä.

| ❌ Väärin | ✅ Oikein |
|---|---|
| `ribosomi` | `Mikä on ribosomi?` |
| `evoluutio` | `Mitä on evoluutio?` |
| `endosymbioosi` | `Mitä endosymbioosi tarkoittaa?` |
| `termodynamiikan toinen pääsääntö` | `Mitä sanoo termodynamiikan toinen pääsääntö?` |

Valitse luonteva muoto: **"Mikä on X?"** konkreettisille (solu, entsyymi, ATP),
**"Mitä on X?" / "Mitä X tarkoittaa?"** abstrakteille ja prosesseille (evoluutio, transkriptio, entropia).

---

## 4. linkkisanat: kaikki suomen sijamuodot

Sivuston sanalinkitys osuu vain **täsmälleen samaan sanaan** — "ribosomi" ei osu sanaan "ribosomissa".
Siksi jokaisesta suomenkielisestä termistä luetellaan taivutusmuodot. Malli:

```
ribosomi, ribosomin, ribosomia, ribosomissa, ribosomista, ribosomiin,
ribosomit, ribosomien, ribosomeja, ribosomeissa
```

Eli yksikön **nominatiivi, genetiivi, partitiivi, inessiivi, elatiivi, illatiivi**
+ monikon **nominatiivi, genetiivi, partitiivi, inessiivi**.

- Huomioi vokaalisointu (`entsyymiä/entsyymissä` vs. `solua/solussa`), astevaihtelu
  (`soluseinä → soluseinän`) ja vartalonmuutokset (`ribosomi → ribosomeja`).
- **Älä taivuta**: englanninkieliset termit, lajinimet (*Escherichia coli*), henkilönnimet.
- Lyhenteet kaksoispisteellä: `ATP, ATP:n, ATP:ta, ATP:ssa, ATP:sta, ATP:hen`.
- Monisanaiset termit: 4–6 luontevaa muotoa, molemmat osat taipuvat
  (`kovalenttinen sidos, kovalenttisen sidoksen, kovalenttista sidosta…`).
- Synonyymit mukaan, kukin omine muotoineen.
- **Vain termikorteissa** — kysymyskorteissa `linkkisanat` on tyhjä.

---

## 5. Kattavuus

- **Määrittelykortti jokaisesta termistä** — myös helpoimmista.
- **Kysymyskortti jokaisesta dian asiasta.**
- Ohita puhtaasti hallinnolliset diat (kurssin tavoitteet, Moodle, tenttiajat, opiskeluvinkit).
- **Ristiinlinkitys pakkojen välillä:** yleiset termit (solu, DNA, proteiini, entsyymi…) määritellään
  **kerran** perustavassa pakassa (Solu ja biomolekyylit) — muissa pakoissa niitä ei toisteta, vaan ne
  linkittyvät sinne. Älä siis anna samoja linkkisanoja kahdelle kortille.
- **Jokaisella kortilla on tenttitodennäköisyys.** Arvo on numero, ja asteikko on:
  | arvo | mitä | esimerkki |
  |---|---|---|
  | `3` | **perusasia** — ydinkäsite tai keskeinen määritelmä, joka on osattava | *Mikä on soluelin?*, *Mikä on entsyymi?*, keskusdogma |
  | `2` | **syventävä tieto** — mekanismi, vertailu, luokittelu tai perustelu | *Miten X toimii?*, *Mitä eroa on X:llä ja Y:llä?* |
  | `1` | **nippelitieto** — yksityiskohta: lukuarvot, vuosiluvut, henkilönnimet, anekdootit, lajinimet | *Kuka käytti termiä ensimmäisenä?*, Nobel-vuodet |

  Sivusto piirtää arvosta tähdet; numero on selvempi lukea ja muokata Ankissa.
  Peruskäsitteiden määrittelykortit ovat lähtökohtaisesti `3`, eivät `1` — pelkkä "helppo" kortti ei ole nippelitietoa.
- **Älä ylikirjoita käyttäjän omia arvioita.** Jos kortilla on jo arvo kentässä **tai** tagissa, jätä se rauhaan.
- **Korttityypit joissa ei ole tähtikenttää** (Enhanced Cloze, Image Occlusion): arvo tallennetaan tagina
  `tt1` / `tt2` / `tt3`. index.html lukee sen. **Älä lisää kenttää vieraaseen korttityyppiin** — kenttien
  muuttaminen rikkoo tuonnin (ks. §1).

---

## 6. Esittely-kortti = pakan kansi

Jokaisessa kurssipakassa on kortti, jonka `Kysymys` on **`Esittely`**. Sen `Laaja vastaus` näkyy
sivustolla pakan kansitekstinä, eikä kortti näy korttiruudukossa. Älä anna sille linkkisanoja.

---

## 7. Pakan nimi ja tiedostonimi

**Pakannimi = koko hierarkiapolku**, jotta tuonti osuu suoraan oikeaan kohtaan Ankissa:

```
SOLUKKO::1. LUKUVUOSI::1.1 SYKSY::1. Periodi::Solu- ja biomolekyylit - teoria (BKEM5030)::Luento 1 - Elämä, perusteet ja periaatteet
```

- Periodi-taso (`1. Periodi`) on mukana syksyn kursseilla; keväällä sitä ei ole. Sivusto lukee periodin
  suoraan polusta.
- Kurssin nimi kirjoitetaan **täsmälleen** kuten käyttäjän Ankissa (esim. kurssikoodi mukaan:
  `Solu- ja biomolekyylit - teoria (BKEM5030)`). Yksikin merkkiero luo rinnakkaisen pakan.

**Yksi apkg = yksi luento.** Tiedosto tallennetaan kurssin omaan kansioon tähän `kurssit/`-hakemistoon,
nimellä joka vastaa pakan lehteä:

```
kurssit/BKEM5030 Solu- ja biomolekyylit - teoria/Luento 1 - Elämä, perusteet ja periaatteet.apkg
```

Käytä pilkkua, älä kaksoispistettä (`:` ei kelpaa Windows-tiedostonimeen).

---

## 8. Muuta huomioitavaa

- Escapetä `<` ja `>` muotoon `&lt;` / `&gt;`, muuten genanki tulkitsee ne HTML-tageiksi.
- Älä jätä pakkaan kahta korttia samalla etupuolella — poista duplikaatit.
- Media (kuvat) kulkee apkg:n mukana; ota mukaan vain kortteihin oikeasti viitatut tiedostot.
- Kurssimateriaaleja (PDF-diat, videot, oppikirjat) **ei committata** GitHubiin — vain sivuston
  tarvitsemat tiedostot ja `SOLUKKO.apkg` kuuluvat repoon.

---

## 9. Jos laaja ja suppea sanoisivat saman

Älä kirjoita laajaa vastausta vain muotoilun vuoksi. **Jos laaja vastaus ei tuo suppeaan mitään
olennaista lisää, täytä vain `Suppea vastaus` ja jätä `Laaja vastaus` tyhjäksi.**

Sivusto tunnistaa tällaisen kortin ja:
- näyttää sen ainoan vastauksen normaalisti,
- **harmaannuttaa** "Suppea vastaus" -napin merkiksi ettei siitä ole mihin vaihtaa,
- laittaa Monan sanomaan *"Tähän kysymykseen ei ole laajempaa vastausta."*

Laaja vastaus kannattaa kirjoittaa vain kun se oikeasti syventää: lisää mekanismin, esimerkin,
poikkeuksen tai lukuarvot.

**Mitta laajalle vastaukselle: 45–65 sanaa, 3–4 virkettä.** Pelkkä suhdeluku suppeaan ei riitä
kriteeriksi — suppea on usein niin lyhyt, että kaksinkertainenkin laaja jää parin rivin mittaiseksi.
Toteutuneet tasot: Solu L1 mediaani 51 sanaa, Biotekniikka L1 mediaani 53.

---

## 10. Termisanasto — mitä sanoja käytetään

Sama asia sanotaan pakassa **aina samalla sanalla**. Vieraskieliset ja rinnakkaiset nimitykset eivät
kuulu kortin leipätekstiin: ne mainitaan **vain sen termin omalla kortilla** rivillä
`Muut nimet: ...` laajan vastauksen lopussa.

### Käytä näitä

| käytä | älä käytä | huom |
|---|---|---|
| **lähetti-RNA**, lähetti-RNA-ketju | mRNA, messenger RNA | myös yhdyssanoissa: *lähetti-RNA-rokote* |
| **tuma** | nucleus | |
| **endoplasminen kalvosto** | solulimakalvosto | |
| **proteiini** | valkuaisaine | |
| **solukalvo** | plasmakalvo | |
| **soluseinä** | soluseinämä | |

`Muut nimet` -rivit tällä hetkellä: *Mikä on tuma?* → nucleus, *Mikä on lähetti-RNA?* → mRNA,
messenger RNA.

### Vielä päättämättä

Näissä pakassa esiintyy molempia muotoja. Kun linja on valittu, se merkitään yllä olevaan
taulukkoon ja yhdenmukaistetaan koko pakkaan:

| vaihtoehto | esiintymiä | vaihtoehto | esiintymiä |
|---|---|---|---|
| solulima | 9 | sytoplasma | 12 |
| perimä | 19 | genomi | 22 |
| soluelin | 8 | organelli | 1 |
| tumakotelo | 8 | tumakalvo | 2 |
| emäsjärjestys | 5 | nukleotidijärjestys | 1 |

### Lyhenteiden taivutus

Lyhennepäätteet ovat **takavokaalisia**, koska lyhenne luetaan koko sanana
(*adenosiinitrifosfaattia* → ATP:ta): `ATP:ta`, `ADP:sta`, `DNA:ta`, `RNA:ta`, `NADH:ta`.
Ei `ATP:tä` eikä `ADP:stä`.

---

## 11. Kuvakortit

Osa dioista opettaa jotain, mitä pelkkä teksti ei opeta: rakennekaaviot, prosessikaaviot,
fylogeneettiset puut, rakennekaavat, vertailukuvat, graafit. Niistä tehdään kortit näin:

- **Kuva tulee vastauspuolelle**, `Laaja vastaus` -kentän loppuun: `<br><img src="tiedosto.png">`.
- **`Kysymys` on tekstiä ja siihen pitää pystyä vastaamaan ilman kuvaa** — kuva havainnollistaa vastausta,
  ei ole arvoitus.
- `Laaja vastaus` **selittää kuvan**: mitä siinä näkyy, mitä osat tarkoittavat, mitä siitä pitää oppia.
- Ota mukaan vain kuvat, joita ilman kortti olisi selvästi huonompi. **Hylkää** valokuvat ihmisistä,
  laitteista ja tuotteista, logot, kuvituskuvat, taustat ja kuvakaappaukset tekstistä.
- Kuvatiedostot poimitaan dioista (PyMuPDF `page.get_images`), ja ne on lisättävä apkg:n `media`-karttaan.
  Duplikaatit karsiutuvat md5-tiivisteellä; useammalla sivulla toistuva kuva on tausta tai logo.
