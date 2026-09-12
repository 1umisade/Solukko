# -*- coding: utf-8 -*-
"""Funktionaalisten ryhmien termikortit (Lehninger kuva 1-16, Solu L1 dia 77) Luento 1 -pakkaan, kortin 1.092 peraan
(numerot 1.0921-1.0945: sivusto lajittelee liukuluvulla, joten ne asettuvat 1.092:n ja 1.093:n valiin eika muita
tarvitse numeroida uudelleen). Jokaisella kortilla on 3D-malli-kentassa mallimolekyylin avain (ryhmat_3d.py), jolloin
sivusto upottaa kortin etupuolelle sen 2D-kaavan ja elavan 3D-mallin, ja laaja vastaus mainitsee molekyylin nimeltä,
joten sana avaa popupin.

Sama kolmen vaiheen kierros kuin tyokalut/litra.py: 1) SOLUKKO.apkg patchataan paikallaan (sivusto nayttaa kortit heti),
2) kurssit/BKEM5030 .../Luento 1 - Funktionaaliset ryhmat (lisays).apkg sisaltaa VAIN nama kortit samoilla guideilla
-> Ankiin tuonti lisaa ne kerran ja paivittaa paikallaan uudella ajolla. Idempotentti: toinen ajo paivittaa, ei monista.
Aja: python tyokalut/ryhmat_kortit.py"""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'SOLUKKO.apkg')
OUT = os.path.join(REPO, 'kurssit', 'BKEM5030 Solu- ja biomolekyylit - teoria', 'Luento 1 - Funktionaaliset ryhmat (lisays).apkg')
SEP = chr(31); MID = 1727391050   # Solukko-korttityyppi
DECK_LOPPU = 'Solu- ja biomolekyylit - teoria (BKEM5030)::Luento 1 - Elämä, perusteet ja periaatteet'
sys.path.insert(0, SC)
import ryhmat_3d


def taivuta(w):
    """Linkkisanat (kurssit/CLAUDE.md §4): i-loppuiset kuten ryhmat_3d, lisaksi -ryhmä, -sidos ja -silta."""
    if w.endswith('ryhmä'):
        v = w[:-1]; return [w, v+'än', v+'ää', v+'ässä', v+'ästä', v+'ään', v+'äksi', v+'ällä', v+'älle', v+'ät', w[:-2]+'ien', w[:-2]+'iä', w[:-2]+'issä']
    if w.endswith('sidos'):
        v = w[:-1] + 'ks'; return [w, v+'en', w+'ta', v+'essa', v+'esta', v+'een', v+'eksi', v+'ella', v+'elle', v+'et', w+'ten', v+'ia', v+'issa']
    if w.endswith('silta'):
        v = w[:-3]; return [w, v+'llan', w+'a', v+'llassa', v+'llasta', w+'an', v+'llaksi', v+'llalla', v+'llalle', v+'llat', v+'ltojen', v+'ltoja', v+'lloissa']
    return ryhmat_3d.taivuta(w)

def K(kys, suppea, laaja, tt, malli, *linkit):
    """linkit: i-loppuiset termit taivutetaan (taivuta), muut (monisanaiset) annetaan valmiina listana"""
    sanat = []
    for l in linkit:
        if isinstance(l, list): sanat += l
        else: sanat += taivuta(l)
    return (kys, suppea, laaja, str(tt), malli, ', '.join(sanat))

KORTIT = [
K("Mikä on metyyliryhmä?",
  "Yhden hiilen hiilivetyryhmä –CH<sub>3</sub>, jossa hiileen on sitoutunut kolme vetyä.",
  "Metyyliryhmä on pienin hiilivetyryhmä: yksi hiili ja kolme vetyä, jotka on sitoutunut molekyylin runkoon (R–CH<sub>3</sub>). Se on poolittomana vettä hylkivä ja reagoi huonosti, joten sen tehtävä on usein tilan täyttäminen ja hydrofobisten vuorovaikutusten tuottaminen. Metylaatio eli metyyliryhmän liittäminen DNA:han tai proteiiniin on tärkeä säätelymerkki. Esimerkiksi etaani koostuu kahdesta toisiinsa sitoutuneesta metyyliryhmästä.",
  3, 'ETAANI', 'metyyliryhmä', 'metyyli'),
K("Mikä on etyyliryhmä?",
  "Kahden hiilen hiilivetyryhmä –CH<sub>2</sub>CH<sub>3</sub>.",
  "Etyyliryhmä on kahden hiilen ketju, jossa runkoon sitoutunutta CH<sub>2</sub>-hiiltä seuraa päätemetyyli (R–CH<sub>2</sub>–CH<sub>3</sub>). Kuten metyyli, se on pooliton ja vettä hylkivä eikä osallistu vetysidoksiin. Etyyliryhmä on esimerkiksi etanolin hiilivetyosa, ja pidemmät alkyyliketjut, kuten rasvahappojen hiilivetyhännät, ovat samaa perhettä. Propaani on metyyliryhmään liittynyt etyyliryhmä.",
  2, 'PROPAANI', 'etyyliryhmä', 'etyyli'),
K("Mikä on fenyyliryhmä?",
  "Bentseenirengas substituenttina: kuusi hiiltä tasomaisessa aromaattisessa renkaassa (–C<sub>6</sub>H<sub>5</sub>).",
  "Fenyyliryhmä on bentseenirengas, joka on kiinni molekyylin rungossa yhdestä hiilestään. Rengas on tasomainen ja aromaattinen: sen kuusi p-elektronia jakautuvat tasaisesti koko renkaalle, mikä tekee siitä erityisen vakaan. Fenyyli on pooliton ja hydrofobinen, ja renkaat pinoutuvat mielellään päällekkäin. Aminohapoista fenyylialaniinilla on fenyyliryhmä. Tolueeni on metyyliryhmään sitoutunut fenyyli.",
  2, 'TOLUEENI', 'fenyyliryhmä', 'fenyyli'),
K("Mikä on karbonyyliryhmä?",
  "Hiili, johon happi on sitoutunut kaksoissidoksella (C=O).",
  "Karbonyyliryhmässä hiili ja happi ovat kaksoissidoksessa. Happi vetää sidoselektroneja itselleen, joten ryhmä on poolinen: hiili on osittain positiivinen ja altis nukleofiilien hyökkäykselle, happi osittain negatiivinen ja hyvä vetysidoksen vastaanottaja. Karbonyyli on aldehydien, ketonien, karboksyylihappojen, esterien ja amidien yhteinen ydin, ja sen hiili on useimpien biosynteesireaktioiden kohta. Asetoni on yksinkertainen karbonyyliyhdiste.",
  3, 'ASETONI', 'karbonyyliryhmä', 'karbonyyli'),
K("Mikä on aldehydiryhmä?",
  "Karbonyyli ketjun päässä: hiileen on sitoutunut happi kaksoissidoksella ja yksi vety (–CHO).",
  "Aldehydiryhmässä karbonyylihiili on hiiliketjun päässä ja kantaa yhden vedyn (R–CHO). Se on ketonia reaktiivisempi, koska vety ei suojaa hiiltä eikä työnnä sille elektroneja. Aldehydit hapettuvat helposti karboksyylihapoiksi ja muodostavat alkoholien kanssa puoliasetaaleja, mihin sokerien rengasrakenne perustuu. Glukoosi on aldehydisokeri. Asetaldehydi on etanolin hapettumistuote maksassa ja krapulan pääsyyllinen.",
  3, 'ASETALDEHYDI', 'aldehydiryhmä', 'aldehydi'),
K("Mikä on ketoniryhmä?",
  "Karbonyyli ketjun keskellä: hiileen on sitoutunut happi ja kaksi hiiltä (R–CO–R').",
  "Ketoniryhmässä karbonyylihiili on kahden hiilen välissä (R<sup>1</sup>–CO–R<sup>2</sup>), joten se ei ole ketjun päässä eikä siihen ole sitoutunut vetyä. Ketonit eivät hapetu yhtä helposti kuin aldehydit, mutta karbonyylin poolisuus tekee niistä hyviä vetysidoksen vastaanottajia. Fruktoosi on ketonisokeri, ja aineenvaihdunnan ketoaineet, kuten asetoni, syntyvät rasvahappojen hajotuksesta.",
  3, 'ASETONI', 'ketoniryhmä', 'ketoni'),
K("Mikä on karboksyyliryhmä?",
  "Happoryhmä –COOH, joka luovuttaa protonin ja on solussa yleensä karboksylaattina –COO<sup>−</sup>.",
  "Karboksyyliryhmässä samaan hiileen on sitoutunut karbonyylihappi ja hydroksyyli (–COOH). Ryhmä on happo: se luovuttaa hydroksyylin protonin, ja syntyvässä karboksylaatissa negatiivinen varaus jakautuu tasan kahdelle hapelle, mikä vakauttaa sen. Solun pH:ssa karboksyylit ovat lähes aina karboksylaattimuodossa. Aminohapoissa, rasvahapoissa ja sitruunahappokierron hapoissa on karboksyyliryhmiä. Asetaatti on etikkahapon karboksylaatti.",
  3, 'ASETAATTI', 'karboksyyliryhmä', 'karboksyyli', 'karboksylaatti', 'karboksylaattiryhmä'),
K("Mikä on hydroksyyliryhmä?",
  "Alkoholiryhmä –OH: hiileen sitoutunut happi, jossa on vety.",
  "Hydroksyyliryhmässä hiileen on sitoutunut happi, joka kantaa vetyä (R–OH). O–H-sidos on poolinen, joten ryhmä sekä luovuttaa että vastaanottaa vetysidoksia ja tekee molekyylistä vesiliukoisen. Sokerien runsaat hydroksyylit selittävät niiden liukoisuuden. Hydroksyyli voi hapettua karbonyyliksi ja muodostaa esterisidoksia, ja seriinin, treoniinin ja tyrosiinin hydroksyylit ovat fosforylaation kohteita. Etanoli on yksinkertainen alkoholi.",
  3, 'ETANOLI', 'hydroksyyliryhmä', 'hydroksyyli', 'alkoholiryhmä'),
K("Mikä on enoliryhmä?",
  "Hydroksyyli, joka on kiinni hiili–hiili-kaksoissidoksen hiilessä (C=C–OH).",
  "Enolissa hydroksyyliryhmä on sitoutunut kaksoissidoksen hiileen. Rakenne on yleensä epävakaa ja asettuu tasapainoon keto-muotonsa kanssa: protoni siirtyy hapelta hiilelle ja kaksoissidos muuttuu C=O-sidokseksi (keto–enoli-tautomeria). Glykolyysissä fosfoenolipyruvaatti on enoli, jonka energiarikas fosfaatti siirtyy ADP:lle. Kaikkein yksinkertaisin enoli on etenoli eli vinyylialkoholi, joka muuttuu nopeasti keto-muotoonsa asetaldehydiksi.",
  2, 'ETENOLI', 'enoliryhmä', 'enoli'),
K("Mikä on eetteriryhmä?",
  "Happi kahden hiilen välissä (R–O–R').",
  "Eetterissä happiatomi sitoo kaksi hiiltä toisiinsa (R<sup>1</sup>–O–R<sup>2</sup>). Ryhmä on melko reagoimaton ja heikosti poolinen: happi voi vastaanottaa vetysidoksen, mutta ei luovuttaa, koska siinä ei ole vetyä. Sokerien rengasrakenteen happi on eetterihappi, ja glykosidisidos, joka liittää sokeriyksiköt toisiinsa, on eetterityyppinen. Dimetyylieetteri on yksinkertaisin eetteri.",
  2, 'DME', 'eetteriryhmä', 'eetteri'),
K("Mikä on esteriryhmä?",
  "Karboksyylihapon ja alkoholin liitos: karbonyylihiili sitoutunut happeen, joka jatkuu hiileen (R–CO–O–R').",
  "Esteri syntyy, kun karboksyylihappo ja alkoholi liittyvät yhteen ja vettä irtoaa (R<sup>1</sup>–CO–O–R<sup>2</sup>). Ryhmä on poolinen mutta ei luovuta vetysidoksia. Esterisidokset liittävät rasvahapot glyseroliin triglyserideissä ja kalvojen fosfolipideissä, ja ne katkeavat vesikatkaisulla lipaasien vaikutuksesta. Etyyliasetaatti on etikkahapon ja etanolin esteri, jonka tuoksun tunnistaa kynsilakanpoistoaineesta.",
  3, 'ETYYLIASETAATTI', 'esteriryhmä', 'esteri', 'esterisidos'),
K("Mikä on asetyyliryhmä?",
  "Etikkahaposta peräisin oleva kahden hiilen ryhmä –CO–CH<sub>3</sub>.",
  "Asetyyliryhmä on etikkahapon runko ilman hydroksyyliä: karbonyylihiili, johon on sitoutunut metyyli (–CO–CH<sub>3</sub>). Se siirtyy solussa asetyylikoentsyymi A:n tioesterisidoksesta, jonka katkaisu vapauttaa paljon energiaa. Asetyyliryhmä syöttää hiilet sitruunahappokiertoon, ja histonien lysiinien asetylointi avaa kromatiinia ja säätelee geenien ilmentymistä. Metyyliasetaatissa asetyyliryhmä on sitoutunut metoksihappeen, kuten kuvan esteriesimerkissä.",
  2, 'METYYLIASETAATTI', 'asetyyliryhmä', 'asetyyli'),
K("Mikä on happoanhydridi?",
  "Kaksi karboksyylihappoa liittyneenä hapen kautta vettä menettäen (R–CO–O–CO–R').",
  "Happoanhydridi syntyy, kun kahdesta karboksyylihaposta poistuu yksi vesimolekyyli ja happoryhmät sitoutuvat yhteisen hapen kautta (R<sup>1</sup>–CO–O–CO–R<sup>2</sup>). Sidos on energiarikas ja hajoaa helposti vedessä takaisin hapoiksi, joten anhydridit ovat hyviä asyyliryhmän luovuttajia. Sama periaate toistuu fosfoanhydrideissä, kuten ATP:ssa. Etikkahappoanhydridi on kahden etikkahapon anhydridi.",
  2, 'ETIKKAHAPPOANHYDRIDI', 'happoanhydridi', 'anhydridi', 'anhydridiryhmä'),
K("Mikä on aminoryhmä?",
  "Typpi kahdella vedyllä (–NH<sub>2</sub>), joka emäksenä sitoo protonin muotoon –NH<sub>3</sub><sup>+</sup>.",
  "Aminoryhmässä hiileen on sitoutunut typpi, jolla on kaksi vetyä ja vapaa elektronipari (R–NH<sub>2</sub>). Elektronipari tekee ryhmästä emäksen: solun pH:ssa se on useimmiten protonoitunut positiiviseksi ammoniumryhmäksi (R–NH<sub>3</sub><sup>+</sup>). Aminoryhmä luovuttaa vetysidoksia ja osallistuu suolasiltoihin. Aminohapot, nukleotidien emäkset ja monet välittäjäaineet sisältävät aminoryhmän. Metyyliammoniumioni on metyyliamiinin protonoitunut muoto.",
  3, 'METYYLIAMMONIUM', 'aminoryhmä', 'ammoniumryhmä'),
K("Mikä on amidiryhmä?",
  "Karbonyyli, jonka hiileen on sitoutunut typpi (R–CO–NH<sub>2</sub>).",
  "Amidissa karbonyylihiili on sitoutunut typpeen (R–CO–NH<sub>2</sub>). Typen vapaa elektronipari delokalisoituu karbonyylille, joten amidi ei ole emäs, sidos on osittain kaksoissidoksen luonteinen ja tasomainen, ja se kestää hyvin vesikatkaisua. Proteiinien peptidisidos on amidisidos aminohappojen välillä. Asparagiinilla ja glutamiinilla on sivuketjussaan amidiryhmä. Asetamidi on etikkahapon amidi.",
  3, 'ASETAMIDI', 'amidiryhmä', 'amidoryhmä', 'amidi', 'amidisidos'),
K("Mikä on imiiniryhmä?",
  "Hiili–typpi-kaksoissidos (C=NH), karbonyylin typpivastine.",
  "Imiinissä hiili ja typpi ovat kaksoissidoksessa (R<sup>1</sup>–C(=NH)–R<sup>2</sup>), kuten karbonyylissä hiili ja happi. Imiini syntyy, kun aldehydi tai ketoni reagoi ammoniakin tai amiinin kanssa ja vettä irtoaa. Aineenvaihdunnassa imiinit ovat välituotteita esimerkiksi aminohappojen transaminaatiossa, ja välituote hajoaa helposti vesikatkaisulla takaisin karbonyyliksi ja amiiniksi. Etaani-imiini on asetaldehydin imiini.",
  2, 'ETAANIIMIINI', 'imiiniryhmä', 'imiini'),
K("Mikä on Schiffin emäs?",
  "N-substituoitu imiini: typpeen on sitoutunut hiiliryhmä (R<sup>1</sup>–C(=N–R<sup>3</sup>)–R<sup>2</sup>).",
  "Schiffin emäs on imiini, jonka typessä on vedyn sijasta hiiliryhmä. Se muodostuu, kun aldehydin tai ketonin karbonyyli reagoi primaarisen amiinin kanssa ja vettä irtoaa. Entsyymeissä Schiffin emäs sitoo substraatin tai kofaktorin tilapäisesti lysiinin aminoryhmään: näin toimivat pyridoksaalifosfaatti transaminaasissa ja aldolaasi glykolyysissä. N-metyylietaani-imiini on asetaldehydin ja metyyliamiinin Schiffin emäs.",
  2, 'NMETYYLIETAANIIMIINI', ['Schiffin emäs', 'Schiffin emäksen', 'Schiffin emästä', 'Schiffin emäksessä', 'Schiffin emäksestä', 'Schiffin emäkseen', 'Schiffin emäkseksi', 'Schiffin emäkset', 'Schiffin emästen', 'Schiffin emäksiä', 'N-substituoitu imiini', 'N-substituoidun imiinin', 'N-substituoitua imiiniä']),
K("Mikä on guanidiiniryhmä?",
  "Hiili, johon on sitoutunut kolme typpeä. Vahva emäs, solussa aina positiivinen guanidinium.",
  "Guanidiiniryhmässä yksi hiili on sitoutunut kolmeen typpeen, joista yhteen kaksoissidoksella. Ryhmä on erittäin vahva emäs (pK<sub>a</sub> noin 12,5), koska protonoituneen guanidiniumin positiivinen varaus jakautuu tasan kolmelle typelle. Siksi arginiinin sivuketju on solussa aina positiivinen ja sitoo fosfaatteja ja karboksylaatteja suolasilloilla ja vetysidoksilla. Metyyliguanidiniumioni on pienin guanidinium.",
  2, 'METYYLIGUANIDINIUM', 'guanidiiniryhmä', 'guanidiini', 'guanidiniumryhmä', ['guanidinium', 'guanidiniumin', 'guanidiniumia', 'guanidiniumissa', 'guanidiniumiin']),
K("Mikä on imidatsoliryhmä?",
  "Viisirengas, jossa on kaksi typpeä. Histidiinin sivuketju, pK<sub>a</sub> lähellä 7.",
  "Imidatsoli on aromaattinen viisijäseninen rengas, jossa on kaksi typpeä: toinen kantaa vetyä ja toisella on vapaa elektronipari. Ryhmän pK<sub>a</sub> on noin 6–7, joten solun pH:ssa se voi sekä luovuttaa että vastaanottaa protonin. Siksi histidiini on entsyymien aktiivisten keskusten yleisin happo-emäskatalyytti ja hyvä metalli-ionien, kuten hemin raudan ja sinkin, ligandi. 4-metyyli-imidatsoli on histidiinin sivuketjun malli.",
  2, 'METYYLIIMIDATSOLI', 'imidatsoliryhmä', 'imidatsoli'),
K("Mikä on sulfhydryyliryhmä?",
  "Tioliryhmä –SH: hiileen sitoutunut rikki, jossa on vety.",
  "Sulfhydryyli- eli tioliryhmässä hiileen on sitoutunut rikki, joka kantaa vetyä (R–SH). Se on hydroksyylin rikkivastine mutta happamampi ja hapettuu helpommin: kaksi tiolia voi hapettua disulfidisidokseksi, mikä vakauttaa proteiinien rakennetta. Kysteiinin sulfhydryyli on monien entsyymien aktiivinen nukleofiili, ja koentsyymi A:n tioli sitoo asetyyliryhmän tioesterinä. Metaanitioli on yksinkertaisin tioli.",
  3, 'METAANITIOLI', 'sulfhydryyliryhmä', 'sulfhydryyli', 'tioliryhmä', 'tioli'),
K("Mikä on disulfidisidos?",
  "Kahden rikin välinen kovalenttinen sidos (R–S–S–R'), joka syntyy kahden tiolin hapettuessa.",
  "Disulfidisidos muodostuu, kun kahden sulfhydryyliryhmän rikit hapettuvat ja sitoutuvat toisiinsa (R<sup>1</sup>–S–S–R<sup>2</sup>) ja kaksi vetyä poistuu. Proteiineissa kysteiinien disulfidisillat lukitsevat laskostuneen rakenteen ja ovat yleisiä solun ulkopuolisissa proteiineissa, kuten vasta-aineissa ja insuliinissa, koska solun sisällä pelkistävä ympäristö purkaa ne. Sidos on palautuva: pelkistys palauttaa tiolit. Dimetyylidisulfidi on yksinkertaisin disulfidi.",
  3, 'DMDS', 'disulfidisidos', 'disulfidisilta', 'disulfidi', 'disulfidiryhmä'),
K("Mikä on tioesteri?",
  "Esteri, jossa alkoholin hapen tilalla on rikki (R–CO–S–R'). Energiarikas sidos.",
  "Tioesterissä karbonyylihiili on sitoutunut rikkiin (R<sup>1</sup>–CO–S–R<sup>2</sup>). Toisin kuin tavallisessa esterissä, rikin elektronipari ei vakauta karbonyyliä resonanssilla, joten tioesterisidos on energiarikas ja sen vesikatkaisu vapauttaa lähes yhtä paljon energiaa kuin ATP:n. Asetyylikoentsyymi A on solun tärkein tioesteri: se luovuttaa asetyyliryhmän sitruunahappokiertoon ja rasvahappojen synteesiin. S-metyylitioasetaatti on yksinkertainen tioesteri.",
  3, 'METYYLITIOASETAATTI', 'tioesteri', 'tioesterisidos', 'tioesteriryhmä'),
K("Mikä on fosforyyliryhmä?",
  "Fosfaattiryhmä –OPO<sub>3</sub><sup>2−</sup>, joka on sitoutunut hiileen hapen kautta.",
  "Fosforyyliryhmässä fosfori on sitoutunut neljään happeen, joista yksi liittää sen molekyylin hiileen (R–O–PO<sub>3</sub><sup>2−</sup>). Solun pH:ssa ryhmällä on kaksi negatiivista varausta, joten se tekee molekyylistä vesiliukoisen ja estää sen karkaamisen kalvon läpi. Fosforylaatio eli fosforyylin liittäminen kinaasilla säätelee entsyymejä, ja sokerifosfaatit, kuten glukoosi-6-fosfaatti, ovat aineenvaihdunnan välituotteita. Metyylifosfaatti on pienin fosfaattiesteri.",
  3, 'METYYLIFOSFAATTI', 'fosforyyliryhmä', 'fosforyyli', 'fosfaattiryhmä'),
K("Mikä on fosfoanhydridisidos?",
  "Kahden fosfaattiryhmän välinen sidos (P–O–P), jonka vesikatkaisu vapauttaa paljon energiaa.",
  "Fosfoanhydridi syntyy, kun kaksi fosfaattia liittyy yhteen vettä menettäen, ja fosforit sitoutuvat yhteisen hapen kautta (P–O–P). Sidos on energiarikas, koska vierekkäisten negatiivisten varausten hylkintä purkautuu ja tuotteet vakautuvat resonanssilla ja hydraatiolla. ATP:n kaksi fosfoanhydridisidosta ovat solun energiavaluutta: niiden vesikatkaisu vapauttaa noin 30 kJ/mol. Dimetyylidifosfaatissa on yksi fosfoanhydridisidos.",
  3, 'DIMETYYLIDIFOSFAATTI', 'fosfoanhydridisidos', 'fosfoanhydridi', 'fosfoanhydridiryhmä'),
K("Mikä on asyylifosfaatti?",
  "Karboksyylihapon ja fosforihapon sekoitettu anhydridi (R–CO–O–PO<sub>3</sub><sup>2−</sup>).",
  "Asyylifosfaatissa karboksyylihappo ja fosfaatti ovat liittyneet yhteen vettä menettäen, joten karbonyylihiili on sitoutunut fosfaatin happeen (R–CO–O–PO<sub>3</sub><sup>2−</sup>). Sekoitettu anhydridi on hyvin energiarikas: sen fosforyyli siirtyy helposti ADP:lle. Glykolyysissä 1,3-bisfosfoglyseraatti on asyylifosfaatti, joka tuottaa ATP:n substraattitason fosforylaatiossa. Asetyylifosfaatti on yksinkertaisin asyylifosfaatti. Kutsutaan myös: sekoitettu anhydridi.",
  2, 'ASETYYLIFOSFAATTI', 'asyylifosfaatti', ['sekoitettu anhydridi', 'sekoitetun anhydridin', 'sekoitettua anhydridiä', 'sekoitetut anhydridit']),
]
ALKU = 921   # (1.0921) ... kortin 1.092 peraan


def guid_for(q):
    h = hashlib.sha1(('solukko-ryhmat|' + q.lower()).encode('utf-8')).digest()
    abc = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(abc[b % len(abc)] for b in h[:10])


def sanoja(html): return len(re.sub('<[^>]*>', ' ', html).split())


if __name__ == '__main__':
    for k in KORTIT:
        n = sanoja(k[2]); s = sanoja(k[1])
        if not 45 <= n <= 65 or s > 16: print('  HUOM pituus: %s laaja %d suppea %d' % (k[0], n, s))
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(SRC) as z: z.extractall(work)
    db = os.path.join(work, 'collection.anki21'); con = sqlite3.connect(db); cur = con.cursor()
    decks = json.loads(cur.execute("select decks from col").fetchone()[0])
    did = [int(k) for k, v in decks.items() if v['name'].endswith(DECK_LOPPU)]; assert len(did) == 1, did; did = did[0]
    now = int(time.time()); uudet = paivitetyt = 0; nids = []
    # linkkisanat eivat saa osua toiselle kortille (kurssit/CLAUDE.md §4)
    omat = {}; muut = {}
    for nid, guid, flds in cur.execute("select id, guid, flds from notes").fetchall():
        f = flds.split(SEP)
        if len(f) > 5 and f[5].strip():
            for w in f[5].split(','):
                w = w.strip().lower()
                if w: muut.setdefault(w, guid)
    for i, k in enumerate(KORTIT):
        guid = guid_for(k[0])
        for w in k[5].split(', '):
            w = w.strip().lower()
            if w in omat and omat[w] != guid: print('  HUOM linkkisana kahdella uudella kortilla:', w)
            omat[w] = guid
            if w in muut and muut[w] != guid: print('  HUOM linkkisana on jo kortilla', muut[w], ':', w)
        fields = ['(1.0%d) %s' % (ALKU + i, k[0]), k[1], k[2], k[3], k[4], k[5]]
        sfld = re.sub('<[^>]*>', '', fields[0]).strip(); csum = int(hashlib.sha1(sfld.encode('utf-8')).hexdigest()[:8], 16)
        row = cur.execute("select id, flds from notes where guid=?", (guid,)).fetchone()
        if row:
            nid = row[0]
            if row[1] != SEP.join(fields):
                cur.execute("update notes set flds=?, sfld=?, csum=?, mod=?, usn=-1 where id=?", (SEP.join(fields), sfld, csum, now, nid)); paivitetyt += 1
        else:
            nid = now * 1000 + i * 2
            cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)", (nid, guid, MID, now, -1, '', SEP.join(fields), sfld, csum, 0, ''))
            cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (nid + 1, nid, did, 0, now, -1, 0, 0, 100000 + i, 0, 0, 0, 0, 0, 0, 0, 0, ''))
            uudet += 1
        nids.append(nid)
    con.commit(); con.close()
    print('SOLUKKO.apkg: %d uutta, %d paivitettya korttia' % (uudet, paivitetyt))
    if uudet or paivitetyt:
        tmp = SRC + '.uusi'
        with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for it in zin.infolist():
                if it.filename == 'collection.anki21': zout.write(db, 'collection.anki21')
                else: zout.writestr(it, zin.read(it.filename))
        os.replace(tmp, SRC)
    # ── lisayspaketti: vain nama kortit ──────────────────────────────────────────────
    con = sqlite3.connect(db); cur = con.cursor()
    q = ','.join(str(n) for n in nids)
    cur.execute("update notes set mod=?, usn=-1 where id in (%s)" % q, (now,))
    cur.execute("delete from cards where nid not in (%s)" % q); cur.execute("delete from notes where id not in (%s)" % q)
    cur.execute("delete from revlog"); cur.execute("delete from graves")
    cur.execute("update cards set mod=?, usn=-1" , (now,)); con.commit(); con.close()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.exists(OUT): os.remove(OUT)
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(db, 'collection.anki21'); z.writestr('media', '{}')
    print('kirjoitettu', os.path.relpath(OUT, REPO), '-', len(nids), 'korttia')
    shutil.rmtree(work, ignore_errors=True)
