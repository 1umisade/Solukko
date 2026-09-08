# -*- coding: utf-8 -*-
"""Solu ja biomolekyylit, Luento 2 - Vesi: korttien sisältö.

Yksi kortti = dict: k (Kysymys), s (Suppea), l (Laaja), tt (tenttitodennäköisyys 1-3),
ls (linkkisanat, vain termikorteissa), kuva (tiedosto tyokalut/kuvat/, valinnainen).
Järjestys tässä listassa on pakan järjestys: skripti numeroi kortit (2.001), (2.002), ...
Lähde: 2. Vesi 2026.pdf (51 diaa, Matti Ruuskanen). Transkriptiota ei ole."""

ESITTELY = (
    "Vesi on elämän liuotin ja samalla sen tärkein biomolekyyli. Luento käy läpi, miksi vesi on "
    "niin poikkeuksellinen aine: vesimolekyylin dipoliluonne ja vetysidokset, veden tapa liuottaa "
    "toisia aineita ja pakata hydrofobiset osat yhteen, heikot vuorovaikutukset ja "
    "komplementaarisuus, kolligatiiviset ominaisuudet ja osmoosi, veden ionisoituminen, pH ja "
    "puskurit sekä vesi reaktioiden osallisena kondensaatiossa ja hydrolyysissä."
)

def K(k, s, l, tt, ls="", kuva=""):
    return {"k": k, "s": s, "l": l, "tt": str(tt), "ls": ls, "kuva": kuva}

KORTIT = [
# ── A. Miksi vesi ─────────────────────────────────────────────────────────────
K("Miksi vettä sanotaan tärkeimmäksi biomolekyyliksi?",
  "Kaikki elämän kemia tapahtuu vedessä, ja veden poikkeukselliset ominaisuudet mahdollistavat sen.",
  "Vesi on solun yleisin molekyyli ja liuotin, jossa lähes kaikki biokemialliset reaktiot tapahtuvat. Sen ominaisuudet ovat nesteeksi hyvin poikkeukselliset, ja ne johtuvat lähinnä kahdesta asiasta: vesimolekyylien välisistä vetysidoksista ja vesimolekyylin dipoliluonteesta. Näistä seuraavat veden korkea kiehumispiste, jään keveys, kyky liuottaa polaarisia aineita ja taipumus pakata hydrofobiset aineet yhteen. Ilman näitä tuntemamme elämä ei olisi mahdollista.",
  3),
K("Mistä veden poikkeukselliset ominaisuudet johtuvat?",
  "Vesimolekyylien välisistä vetysidoksista ja vesimolekyylin dipoliluonteesta.",
  "Kaksi rakenteellista syytä selittää lähes kaiken. Ensinnäkin vesimolekyyli on dipoli: happi vetää sidoselektroneja puoleensa, joten happi on osittain negatiivinen ja vedyt osittain positiivisia. Toiseksi dipoliluonteen ansiosta vesimolekyylit muodostavat keskenään vetysidoksia, ja jokainen molekyyli voi sitoa jopa neljä naapuria. Näin nesteeseen syntyy jatkuvasti uusiutuva verkosto, joka antaa vedelle korkean kiehumispisteen, suuren lämpökapasiteetin ja hyvän liuotuskyvyn.",
  3),
# ── B. Vesimolekyyli ──────────────────────────────────────────────────────────
K("Mikä on dipoli?",
  "Molekyyli, jonka toinen pää on osittain positiivinen ja toinen osittain negatiivinen.",
  "Dipoli syntyy, kun sidoselektronit jakautuvat epätasaisesti eri elektronegatiivisuuden atomien välille eivätkä varauspainopisteet osu yhteen. Vesimolekyyli on dipoli: happi on osittain negatiivinen ja kaksi vetyä osittain positiivisia, ja molekyylin taipunut muoto estää varausten kumoutumisen. Dipolit vetävät toisiaan puoleensa vastakkaisilla päillään, mikä on dipoli-dipolisidoksen ja vetysidoksen perusta. Kutsutaan myös: polaarinen molekyyli.",
  3, "dipoli, dipolin, dipolia, dipolissa, dipolista, dipoliin, dipolit, dipolien, dipoleja, dipoleissa, polaarinen molekyyli, polaarisen molekyylin, polaarista molekyyliä, polaarisessa molekyylissä, polaariset molekyylit, polaarisia molekyylejä"),
K("Miksi vesimolekyyli on dipoli?",
  "Happi on vetyä elektronegatiivisempi ja molekyyli on taipunut, joten varaukset eivät kumoudu.",
  "Happiatomi vetää O–H-sidosten elektroneja itseensä voimakkaammin kuin vety, joten hapen ympärille kertyy osittainen negatiivinen varaus ja vetyjen päihin osittainen positiivinen varaus. Koska molekyyli on taipunut noin 104,5° kulmaan eikä suora, kahden sidoksen varaukset eivät kumoa toisiaan vaan molekyylille jää selvä positiivinen ja negatiivinen pää. Kuvassa näkyy myös, että vetysidos (0,177 nm) on selvästi kovalenttista O–H-sidosta (0,0965 nm) pidempi ja siten heikompi.",
  2, kuva="vesi_d04_38.jpeg"),
K("Mikä on elektronegatiivisuus?",
  "Atomin kyky vetää sidoselektroneja puoleensa.",
  "Elektronegatiivisuus kuvaa, kuinka voimakkaasti atomi vetää yhteisiä sidoselektroneja itseensä kovalenttisessa sidoksessa. Happi, typpi ja fluori ovat hyvin elektronegatiivisia, hiili ja vety selvästi vähemmän. Kun sidoksen osapuolten elektronegatiivisuus eroaa paljon, sidos on polaarinen ja molekyylistä voi tulla dipoli. Biokemiassa tämä ratkaisee, mihin atomeihin vetysidokset syntyvät: vetysidoksen osapuoliksi kelpaavat käytännössä vain happeen tai typpeen sitoutuneet vedyt.",
  2, "elektronegatiivisuus, elektronegatiivisuuden, elektronegatiivisuutta, elektronegatiivisuudessa, elektronegatiivisuudesta, elektronegatiivisuuteen, elektronegatiivinen, elektronegatiivisen, elektronegatiivista, elektronegatiivisessa, elektronegatiiviseen, elektronegatiiviset, elektronegatiivisten, elektronegatiivisia, elektronegatiivisempi"),
# ── C. Vetysidos ──────────────────────────────────────────────────────────────
K("Mikä on vetysidos?",
  "Heikko sidos elektronegatiiviseen atomiin sitoutuneen vedyn ja toisen elektronegatiivisen atomin välillä.",
  "Vetysidos syntyy, kun happeen tai typpeen kovalenttisesti sitoutunut, osittain positiivinen vety tulee lähelle toista elektronegatiivista atomia, jolla on vapaa elektronipari. Vedyn puoleista atomia kutsutaan vetysidoksen luovuttajaksi ja toista vastaanottajaksi. Vetysidos on erikoistapaus dipoli-dipolisidoksesta ja tavallisin sellainen biomolekyyleissä. Se on noin kahdeskymmenesosa kovalenttisen sidoksen voimakkuudesta, mutta lukumääränsä vuoksi vetysidokset pitävät koossa veden rakenteen, DNA:n kaksoiskierteen ja proteiinien laskokset.",
  3, "vetysidos, vetysidoksen, vetysidosta, vetysidoksessa, vetysidoksesta, vetysidokseen, vetysidokset, vetysidosten, vetysidoksia, vetysidoksissa, vetysidoksilla, vetysidoksiin, vetysidosverkosto, vetysidosverkoston"),
K("Kuinka vahva vetysidos on kovalenttiseen sidokseen verrattuna?",
  "Noin kahdeskymmenesosa kovalenttisen sidoksen voimakkuudesta.",
  "Tyypillinen vetysidos on voimakkuudeltaan noin 1/20 kovalenttisesta sidoksesta, eli noin 20 kJ/mol verrattuna kovalenttisen sidoksen satoihin kilojouleihin moolilta. Heikkous on biologisesti hyödyllistä: vetysidos syntyy ja katkeaa helposti lämpöliikkeen voimin, joten vetysidosten varaan rakennetut rakenteet, kuten DNA:n kaksoiskierre, voidaan avata ja sulkea tarvittaessa. Yksittäinen vetysidos ei pidä mitään koossa, mutta monta yhdessä pitää.",
  2),
K("Miksi vetysidoksella on voimakas suuntavaikutus?",
  "Sidos on vahvin, kun luovuttaja, vety ja vastaanottaja ovat samalla suoralla.",
  "Vetysidoksen voimakkuus riippuu geometriasta: sidos on vahvin, kun elektronegatiivinen luovuttaja-atomi, vety ja vastaanottaja-atomi (esimerkiksi O, H ja O) ovat suorassa linjassa. Kun kulma taipuu, vety ei enää osoita suoraan vastaanottajan vapaata elektroniparia kohti ja sidos heikkenee selvästi. Suuntavaikutuksen ansiosta vetysidokset eivät ole pelkkää tarttumista vaan määräävät rakenteiden tarkan muodon, kuten jään kidehilan ja DNA:n emäsparien asennon.",
  2, kuva="vesi_d10_55.jpeg"),
K("Mitkä ovat vetysidoksen luovuttaja ja vastaanottaja?",
  "Luovuttaja on vedyn sitonut elektronegatiivinen atomi, vastaanottaja atomi, jolla on vapaa elektronipari.",
  "Vetysidoksessa on aina kaksi osapuolta. Luovuttaja on happi tai typpi, johon vety on kovalenttisesti sitoutunut ja joka luovuttaa vedyn sidokseen, kuten alkoholin O–H tai amidin N–H. Vastaanottaja on toinen happi tai typpi, jonka vapaa elektronipari vetää vetyä puoleensa, kuten karbonyylin C=O tai amiinin typpi. Kuvassa näkyvät tavallisimmat yhdistelmät: vety voi sitoa hapen happeen, hapen typpeen tai typen typpeen.",
  2, kuva="vesi_d07_46.jpeg"),
K("Millaisia vetysidoksia biologisissa makromolekyyleissä on?",
  "Happi- ja typpiatomien välisiä, kun toiseen niistä on kovalenttisesti sitoutunut vety.",
  "Makromolekyyleissä vetysidoksia syntyy happi- ja typpiatomien välille aina, kun jompaankumpaan on kovalenttisesti sitoutunut vety. Tavallisia esimerkkejä ovat alkoholin hydroksyyliryhmän ja veden välinen sidos, ketonin karbonyylihapen ja veden välinen sidos, polypeptidin peptidiryhmien N–H- ja C=O-ryhmien väliset sidokset, jotka pitävät proteiinin laskokset koossa, sekä DNA:n komplementaaristen emästen, kuten tymiinin ja adeniinin, väliset sidokset, jotka pitävät kaksoiskierteen yhdessä.",
  2, kuva="vesi_d08_49.jpeg"),
K("Miksi vedellä on nesteeksi epätavallisen paljon sisäistä rakennetta?",
  "Vesimolekyylit muodostavat keskenään jatkuvasti vaihtuvan vetysidosverkoston.",
  "Jokainen vesimolekyyli voi toimia kahdesti vetysidoksen luovuttajana (kaksi vetyä) ja kahdesti vastaanottajana (hapen kaksi vapaata elektroniparia), joten se voi sitoutua jopa neljään naapuriin. Nestemäisessä vedessä sidokset katkeavat ja syntyvät uudelleen pikosekunneissa, mutta joka hetkellä suurin osa molekyyleistä on sitoutunut naapureihinsa. Tästä väreilevästä verkostosta johtuu, että vesi käyttäytyy kuin sillä olisi kiteen kaltaista rakennetta: sen kiehumispiste, sulamispiste ja höyrystymislämpö ovat muihin pieniin molekyyleihin nähden hyvin korkeita.",
  2),
K("Miksi jää on vettä kevyempää?",
  "Jäätyessään vesi järjestyy kidehilaksi, joka vie enemmän tilaa kuin neste.",
  "Jäässä jokainen vesimolekyyli on sitoutunut neljään naapuriinsa vetysidoksilla säännölliseen, avoimeen hilaan. Suuntautuneet vetysidokset pitävät molekyylit kauempana toisistaan kuin nestemäisessä vedessä, jossa verkosto on epäsäännöllinen ja molekyylit pakkautuvat tiiviimmin. Siksi jään tiheys on pienempi kuin veden ja jää kelluu. Seuraus on ekologisesti ratkaiseva: vesistöt jäätyvät pinnalta eivätkä pohjaa myöten, joten vesieliöt selviävät talven jään alla.",
  2, kuva="vesi_d09_52.jpeg"),
# ── D. Vesi liuottimena ───────────────────────────────────────────────────────
K("Mikä on hydrofiilinen yhdiste?",
  "Veteen hyvin liukeneva yhdiste, jossa on polaarisia tai varattuja ryhmiä.",
  "Hydrofiiliset yhdisteet liukenevat veteen hyvin, koska niiden polaariset tai varatut ryhmät pystyvät muodostamaan vetysidoksia tai ioni-dipoli-vuorovaikutuksia vesimolekyylien kanssa ja siten osallistumaan veden rakenteeseen. Tällaisia ovat sokerit hydroksyyliryhmiensä ansiosta, suolat, aminohapot ja useimmat proteiinien pinnalla olevat ryhmät. Vesi ympäröi hydrofiilisen molekyylin hydraatiokuoreksi. Kutsutaan myös: vesihakuinen, polaarinen yhdiste.",
  3, "hydrofiilinen, hydrofiilisen, hydrofiilistä, hydrofiilisessä, hydrofiilisestä, hydrofiiliseen, hydrofiiliset, hydrofiilisten, hydrofiilisiä, hydrofiilisissä, hydrofiilisyys, hydrofiilisyyden, hydrofiilisyyttä, vesihakuinen, vesihakuisen, vesihakuista, vesihakuiset"),
K("Mikä on hydrofobinen yhdiste?",
  "Ei-polaarinen yhdiste, joka ei liukene veteen vaan häiritsee sen rakennetta.",
  "Hydrofobiset yhdisteet ovat ei-polaarisia, joten ne eivät voi muodostaa vetysidoksia vesimolekyylien kanssa. Vesi joutuu järjestäytymään niiden ympärille häkkimäiseksi kuoreksi, mikä vähentää veden vapautta eli entropiaa ja on epäedullista. Siksi rasvat ja muut hiilivetyketjuiset aineet liukenevat veteen huonosti ja vesi ikään kuin pakottaa ne yhteen. Kutsutaan myös: vettä hylkivä, ei-polaarinen yhdiste.",
  3, "hydrofobinen, hydrofobisen, hydrofobista, hydrofobisessa, hydrofobisesta, hydrofobiseen, hydrofobiset, hydrofobisten, hydrofobisia, hydrofobisissa, hydrofobisuus, hydrofobisuuden, hydrofobisuutta, vettä hylkivä, vettä hylkivän, vettä hylkivät, vettä hylkiviä, vettähylkivä, vettähylkivien"),
K("Mikä on amfipaattinen yhdiste?",
  "Molekyyli, jossa on sekä hydrofiilinen että hydrofobinen osa.",
  "Amfipaattisessa molekyylissä on samassa rakenteessa polaarinen tai varattu, vettä hakeva osa ja ei-polaarinen, vettä hylkivä osa. Tyypillinen esimerkki on fosfolipidi, jossa varattu fosfaattipää on hydrofiilinen ja kaksi rasvahappoketjua hydrofobisia, tai aminohappo fenyylialaniini, jonka aminoryhmä on polaarinen ja bentseenirengas ei-polaarinen. Vedessä amfipaattiset molekyylit järjestyvät niin, että hydrofobiset osat kääntyvät pois vedestä ja hydrofiiliset sitä kohti, ja syntyy misellejä ja kaksoiskalvoja. Kutsutaan myös: amfifiilinen.",
  3, "amfipaattinen, amfipaattisen, amfipaattista, amfipaattisessa, amfipaattisesta, amfipaattiseen, amfipaattiset, amfipaattisten, amfipaattisia, amfipaattisissa, amfifiilinen, amfifiilisen, amfifiilistä, amfifiiliset, amfifiilisiä"),
K("Anna esimerkkejä polaarisista, ei-polaarisista ja amfipaattisista biomolekyyleistä.",
  "Polaarisia: glukoosi, glysiini, laktaatti, glyseroli. Ei-polaarinen: vaha. Amfipaattisia: fenyylialaniini, fosfolipidit.",
  "Polaarisia biomolekyylejä ovat glukoosi hydroksyyliryhmiensä vuoksi, aminohapot glysiini ja aspartaatti varattujen amino- ja karboksylaattiryhmiensä vuoksi, laktaatti ja glyseroli. Ne liukenevat veteen hyvin. Ei-polaarinen on esimerkiksi vaha, pitkä hiilivetyketju ilman polaarisia ryhmiä. Amfipaattisia ovat fenyylialaniini, jossa on polaarinen aminohappo-osa ja ei-polaarinen bentseenirengas, sekä fosfatidyylikoliinin kaltaiset fosfolipidit, joissa varattu pää ja rasvahappoketjut ovat samassa molekyylissä. Solukalvot rakentuvat amfipaattisista molekyyleistä.",
  2),
K("Mitä suolalle tapahtuu, kun se liukenee veteen?",
  "Suola hajoaa ioneiksi, ja vesimolekyylit ympäröivät eli hydratoivat ne.",
  "Kiteisessä natriumkloridissa Na<sup>+</sup>- ja Cl<sup>−</sup>-ionit pitävät toisiaan paikoillaan sähköisillä vetovoimilla. Vedessä ionit dissosioituvat eli irtoavat toisistaan, koska vesimolekyylit kääntyvät ionien ympärille niin, että negatiivinen happipää osoittaa natriumiin ja positiiviset vetypäät kloridiin. Syntyvä hydraatiokuori heikentää ionien keskinäisen vetovoiman ja pitää ne erillään liuoksessa. Sama hydratoituminen tekee kaikista varatuista ryhmistä vesiliukoisia.",
  3, kuva="vesi_d13_68.jpeg"),
K("Mitä dissosiaatio tarkoittaa?",
  "Yhdisteen hajoamista ioneiksi liuoksessa.",
  "Dissosiaatiossa yhdiste hajoaa vedessä ioneiksi, kuten NaCl natrium- ja kloridi-ioneiksi tai happo protoniksi ja vastinemäkseksi. Suolat ja vahvat hapot dissosioituvat käytännössä kokonaan, heikot hapot vain osittain, ja niiden dissosiaation astetta kuvaa happovakio. Dissosiaatio kertaa liuenneiden hiukkasten määrän, joten se vaikuttaa suoraan kolligatiivisiin ominaisuuksiin: mooli NaCl:a tuottaa kaksi moolia hiukkasia. Kutsutaan myös: ionisoituminen, hajoaminen ioneiksi.",
  2, "dissosiaatio, dissosiaation, dissosiaatiota, dissosiaatiossa, dissosiaatiosta, dissosiaatioon, dissosioituminen, dissosioitumisen, dissosioitumista, dissosioituu, dissosioituvat, dissosioitua, dissosioituva, dissosioituvan, dissosioitunut, dissosioituneita"),
K("Mitä hydratoituminen tarkoittaa?",
  "Vesimolekyylien järjestäytymistä liuenneen ionin tai molekyylin ympärille.",
  "Hydratoitumisessa vesimolekyylit ympäröivät liuenneen hiukkasen ja kääntyvät sitä kohti sopivalla päällään: happipää kohti positiivista ionia, vetypäät kohti negatiivista ionia tai polaarisen ryhmän elektronegatiivista atomia. Syntyvä hydraatiokuori eristää hiukkaset toisistaan ja pitää ne liuoksessa. Hydratoituminen selittää, miksi ionit ja polaariset ryhmät ovat hydrofiilisiä, ja sen purkaminen entsyymin ja substraatin kohtaamisessa vapauttaa vesimolekyylejä ja lisää entropiaa. Kutsutaan myös: hydraatio, solvataatio.",
  2, "hydratoituminen, hydratoitumisen, hydratoitumista, hydratoituu, hydratoituvat, hydratoitunut, hydratoida, hydratoivat, hydratoitua, hydraatio, hydraation, hydraatiota, hydraatiokuori, hydraatiokuoren, hydraatiokuorta, hydraatiokuoressa, hydraatiokuoreksi"),
K("Miksi rasvat liukenevat veteen huonosti?",
  "Rasvat ovat ei-polaarisia eivätkä voi muodostaa vetysidoksia veden kanssa.",
  "Rasvojen hiilivetyketjuissa hiili ja vety ovat lähes yhtä elektronegatiivisia, joten sidokset ovat polaarittomia eikä molekyylissä ole vetysidoksen luovuttajia tai vastaanottajia. Vesi ei voi sitoa tällaista molekyyliä rakenteeseensa, vaan joutuu järjestäytymään sen ympärille tiukaksi kuoreksi, mikä vähentää veden entropiaa. Järjestelmä minimoi häiriön pakkaamalla rasvamolekyylit yhteen, jolloin vettä koskettava pinta pienenee. Siksi öljy ja vesi erottuvat kerroksiksi.",
  3),
K("Miksi vesi pakottaa hydrofobiset aineet yhteen?",
  "Yhteen pakkautuminen vapauttaa järjestäytynyttä vettä ja kasvattaa entropiaa.",
  "Hydrofobisen molekyylin ympärillä vesimolekyylit eivät voi muodostaa vetysidoksia molekyyliin päin, joten ne järjestyvät toistensa kanssa häkkimäiseksi, tavallista jäykemmäksi kuoreksi. Tämä on entropian kannalta epäedullista. Kun kaksi hydrofobista molekyyliä painautuu yhteen, niiden yhteinen vettä koskettava pinta pienenee ja osa häkkivedestä vapautuu takaisin nesteen väreilevään verkostoon. Entropia kasvaa, joten yhteen pakkautuminen tapahtuu itsestään, vaikka molekyylien välillä ei ole varsinaista vetovoimaa.",
  2, kuva="vesi_d14_71.jpeg"),
K("Mikä on miselli?",
  "Amfipaattisten molekyylien pallomainen ryväs, jossa hydrofobiset osat ovat sisällä.",
  "Miselli syntyy, kun amfipaattiset molekyylit, esimerkiksi yksiketjuiset rasvahapot tai pesuaineet, järjestyvät vedessä palloksi: hydrofobiset hiilivetyketjut kääntyvät sisään pois vedestä ja hydrofiiliset päät muodostavat vettä koskettavan pinnan. Näin kaikki hydrofobiset ryhmät on kätketty vedeltä ja järjestäytyneen veden määrä on pienimmillään, mikä maksimoi entropian. Misellin muodostuminen on sama ilmiö, joka saa kahden rasvahappoketjun fosfolipidit muodostamaan kaksoiskalvon.",
  2, "miselli, misellin, miselliä, misellissä, misellistä, miselliin, misellit, misellien, misellejä, miselleissä, miselleiksi", kuva="vesi_d17_80.jpeg"),
K("Miten amfipaattiset molekyylit järjestyvät vedessä?",
  "Ryppäiksi, miselleiksi tai kaksoiskalvoiksi, joissa hydrofobiset osat ovat kätkössä vedeltä.",
  "Yksittäinen amfipaattinen molekyyli vedessä pakottaa ympärilleen paljon järjestäytynyttä vettä. Kun molekyylit kerääntyvät ryppäiksi, vain rypään reunan lipidiosat koskettavat vettä, joten järjestäytyneen veden määrä vähenee ja entropia kasvaa. Järjestäytyminen etenee siihen asti, että kaikki hydrofobiset osat ovat piilossa: yksiketjuiset molekyylit muodostavat misellejä ja kaksiketjuiset fosfolipidit kaksoiskalvoja. Solukalvon rakenne perustuu juuri tähän hydrofobiseen vuorovaikutukseen.",
  2, kuva="vesi_d16_77.jpeg"),
K("Miten vesi auttaa entsyymin ja substraatin sitoutumisessa?",
  "Sitoutuminen vapauttaa järjestäytynyttä vettä molempien pinnalta, mikä kasvattaa entropiaa.",
  "Vapaassa liuoksessa sekä entsyymi että substraatti ovat hydraatiokuoren peitossa: vesimolekyylit ovat järjestäytyneet niiden pinnan ryhmiin. Kun substraatti asettuu entsyymin sitoutumiskohtaan, pintojen vesi syrjäytyy ja vapautuu nesteen väreilevään verkostoon. Vapautuvan veden entropian kasvu on osa sitoutumisen ajavaa voimaa yhdessä vetysidosten, ionisten ja hydrofobisten vuorovaikutusten kanssa, jotka pinnat muodostavat toistensa kanssa suoraan.",
  2, kuva="vesi_d18_83.jpeg"),
]
