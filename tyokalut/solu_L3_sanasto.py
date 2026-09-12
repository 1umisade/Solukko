# -*- coding: utf-8 -*-
"""Solu- ja biomolekyylit, Luento 3: sanaston taydennys (numerot 3.101-). Rakentaa tyokalut/solu_kortit.py."""
from biotek_taivutus import L
from pakka_rakenna import K

LEHTI = 'Luento 3 - Eukaryoottisolujen rakenteen perusteet'
TIEDOSTO = 'Luento 3 - Sanasto (lisays)'
NRO = 3
ALKU = 100
KUVAT = {}

KORTIT = [
K("Mikä on konsentraatiogradientti?",
  "Aineen pitoisuusero kahden paikan välillä, esimerkiksi kalvon eri puolilla.",
  "Konsentraatiogradientti on pitoisuuden muutos matkan funktiona: aine on toisella puolella kalvoa väkevämpänä kuin toisella. Aineet pyrkivät diffuusiolla gradientin suuntaan, väkevästä laimeaan, kunnes pitoisuudet tasoittuvat, ja tämä ajaa passiivisen kuljetuksen. Gradientti on myös varastoitua energiaa: solu ylläpitää ionigradientteja pumpuilla ja käyttää niiden purkautumista hermoimpulsseihin ja ATP:n valmistukseen.",
  3, L('konsentraatiogradientti', ['pitoisuusero', 'pitoisuuseron', 'pitoisuuseroa', 'gradientti', 'gradientin', 'gradienttia', 'gradientit'])),
K("Mitä passiivinen kuljetus tarkoittaa?",
  "Aineen siirtymistä kalvon läpi konsentraatiogradientin suuntaan ilman energiaa, kanavan tai kuljettajan kautta.",
  "Passiivisessa kuljetuksessa aine kulkee kalvon läpi väkevästä laimeaan ilman, että solu käyttää energiaa. Pienet poolittomat molekyylit diffundoituvat suoraan lipidikerroksen läpi. Ionit ja poolisemmat molekyylit tarvitsevat kanavan tai kuljettajaproteiinin, jolloin puhutaan helpotetusta diffuusiosta: kuljetus on valikoivaa mutta kulkee vain gradientin suuntaan. Vesi kulkee akvaporiinikanavien kautta osmoosissa. Kutsutaan myös: helpotettu diffuusio.",
  3, L(['passiivinen kuljetus', 'passiivisen kuljetuksen', 'passiivista kuljetusta', 'passiivisessa kuljetuksessa', 'helpotettu diffuusio', 'helpotetun diffuusion', 'helpotettua diffuusiota'])),
K("Mitä aktiivinen kuljetus tarkoittaa?",
  "Aineen pumppaamista kalvon läpi konsentraatiogradienttia vastaan energialla, tavallisesti ATP:lla.",
  "Aktiivisessa kuljetuksessa pumppuproteiini siirtää ainetta laimeasta väkevään ja käyttää siihen energiaa. Primaarisessa aktiivisessa kuljetuksessa energia tulee suoraan ATP:n vesikatkaisusta, kuten natrium-kaliumpumpussa, joka pitää solun sisällä paljon kaliumia ja vähän natriumia. Sekundaarisessa kuljetuksessa yhden aineen gradientin purkautuminen vetää toista ainetta gradienttia vastaan, kuten glukoosin otossa suolen soluihin natriumin mukana.",
  3, L(['aktiivinen kuljetus', 'aktiivisen kuljetuksen', 'aktiivista kuljetusta', 'aktiivisessa kuljetuksessa', 'natrium-kaliumpumppu', 'natrium-kaliumpumpun', 'natrium-kaliumpumppua'])),
K("Mikä on ionikanava?",
  "Kalvoproteiini, jonka huokosen läpi tietyt ionit pääsevät kulkemaan gradienttinsa suuntaan.",
  "Ionikanava on kalvon läpäisevä proteiini, jonka keskellä on vedellä täyttynyt huokonen. Kanava on valikoiva: kaliumkanava päästää läpi kaliumia mutta ei pienempää natriumia, koska huokosen ryhmät korvaavat juuri kaliumin hydraatiokuoren. Useimmat kanavat avautuvat ja sulkeutuvat signaalista, kuten jännitteestä tai välittäjäaineesta, ja niiden läpi kulkee miljoonia ioneja sekunnissa. Hermoimpulssi on kanavien avautumisen aalto.",
  3, L('ionikanava')),
K("Mikä on kalvoproteiini?",
  "Solukalvoon tai soluelimen kalvoon sitoutunut proteiini, joka kuljettaa, välittää viestejä tai kiinnittää.",
  "Kalvoproteiinit hoitavat kalvon tehtävät, koska lipidikerros itse on läpäisemätön ja passiivinen. Kalvon läpäisevät proteiinit, kuten kanavat, pumput ja reseptorit, ankkuroituvat kalvoon hydrofobisilla alfakierteillään. Perifeeriset proteiinit ovat kiinni kalvon pinnassa. Kalvoproteiinit ovat noin puolet kalvon massasta ja lähes puolet lääkkeiden kohteista. Ne valmistetaan karkeassa endoplasmisessa kalvostossa ja kuljetetaan rakkuloissa paikoilleen.",
  3, L('kalvoproteiini')),
K("Mikä on kalvorakkula?",
  "Pieni kalvon rajaama pussi, joka kuljettaa aineita soluelinten välillä ja solukalvolle.",
  "Kalvorakkula kuroutuu irti yhdestä kalvosta ja sulautuu toiseen, ja kuljettaa sisällään ja kalvossaan proteiineja ja lipidejä: endoplasmisesta kalvostosta Golgin laitteeseen, sieltä lysosomeihin tai solukalvolle, ja endosytoosissa solukalvolta sisään. Rakkulan kuori, kuten klatriini, ja sen pinnan tunnistusproteiinit määräävät, mihin se sulautuu. Hermosolun välittäjäaine varastoidaan rakkuloihin, jotka tyhjenevät eksosytoosilla. Kutsutaan myös: vesikkeli, rakkula.",
  3, L('kalvorakkula', ['vesikkeli', 'vesikkelin', 'vesikkeliä', 'vesikkelissä', 'vesikkelit', 'vesikkelien', 'vesikkeleitä', 'rakkula', 'rakkulan', 'rakkulaa', 'rakkulassa', 'rakkulat', 'rakkuloiden', 'rakkuloita', 'rakkuloissa'])),
None,   # 3.107 oli kromosomi-kaksoiskortti (poistettu 12.9.2026, kromosomi on L1:n 1.033); numero pysyy varattuna
K("Mikä on sukusolu?",
  "Haploidi solu, munasolu tai siittiö, jossa on vain yksi kromosomi kustakin parista.",
  "Sukusolut syntyvät meioosissa, jossa kromosomiluku puolittuu: ihmisen sukusolussa on 23 kromosomia. Munasolu on suuri ja liikkumaton, siittiö pieni ja siimallinen. Hedelmöityksessä kaksi sukusolua yhtyy diploidiksi tsygootiksi, jonka 46 kromosomista puolet on äidiltä ja puolet isältä. Meioosin rekombinaatio sekoittaa vanhempien geenejä, mikä tuottaa jälkeläisiin vaihtelua. Kutsutaan myös: gameetti.",
  2, L('sukusolu', ['gameetti', 'gameetin', 'gameetit', 'meioosi', 'meioosin', 'meioosia', 'meioosissa'])),
K("Mitä fotosynteesi on?",
  "Prosessi, jossa kasvit ja syanobakteerit sitovat valon energialla hiilidioksidia sokereiksi ja vapauttavat happea.",
  "Fotosynteesissä klorofylli absorboi valon, ja sen energialla vesi halkaistaan hapeksi, protoneiksi ja elektroneiksi. Valoreaktiot tylakoidikalvolla tuottavat ATP:ta ja NADPH:ta, joilla strooman Calvinin kierto pelkistää hiilidioksidin sokereiksi. Kokonaisreaktiossa hiilidioksidi ja vesi muuttuvat glukoosiksi ja hapeksi. Fotosynteesi on lähes kaiken ravinnon ja ilmakehän hapen lähde, ja se tapahtuu kasveilla kloroplasteissa. Kutsutaan myös: yhteyttäminen.",
  3, L('fotosynteesi', ['yhteyttäminen', 'yhteyttämisen', 'yhteyttämistä', 'yhteyttää', 'yhteyttävät', 'valoreaktio', 'valoreaktion', 'valoreaktiot', 'valoreaktioiden', 'Calvinin kierto', 'Calvinin kierron', 'Calvinin kiertoa'])),
K("Mikä on pigmentti?",
  "Valoa absorboiva väriaine, kuten klorofylli tai kukkien antosyaanit.",
  "Pigmentti absorboi tiettyjä valon aallonpituuksia ja heijastaa muut, mistä sen väri syntyy: klorofylli absorboi punaista ja sinistä ja näyttää vihreältä. Fotosynteesin pigmentit, klorofyllit ja karotenoidit, keräävät valon energian. Kukkien ja hedelmien antosyaanit vakuolissa houkuttelevat pölyttäjiä. Melaniini suojaa ihoa ultraviolettivalolta, ja hemoglobiinin hemi tekee verestä punaista. Pigmentit ovat usein konjugoituneita rengasrakenteita.",
  2, L('pigmentti', ['karotenoidi', 'karotenoidin', 'karotenoidit', 'karotenoideja'])),
K("Mikä on hermovälittäjäaine?",
  "Hermosolun eksosytoosilla vapauttama viestimolekyyli, joka siirtää signaalin seuraavaan soluun synapsissa.",
  "Hermoimpulssin saapuessa hermopäätteeseen kalsium laukaisee välittäjäainerakkuloiden eksosytoosin synapsirakoon. Välittäjäaine, kuten asetyylikoliini, glutamaatti tai dopamiini, sitoutuu vastaanottavan solun reseptoreihin, jotka ovat usein ionikanavia, ja avaa tai sulkee ne. Viesti päättyy, kun välittäjäaine hajotetaan tai otetaan takaisin. Monet lääkkeet ja huumeet vaikuttavat välittäjäaineiden vapautukseen tai takaisinottoon. Kutsutaan myös: neurotransmitteri.",
  2, L('hermovälittäjäaine', 'välittäjäaine', ['neurotransmitteri', 'neurotransmitterin', 'neurotransmitterit', 'synapsi', 'synapsin', 'synapsia', 'synapsissa', 'synapsit'])),
K("Mikä on makrofagi?",
  "Valkosolu, joka syö fagosytoosilla bakteereja, kuolleita soluja ja roskaa.",
  "Makrofagi on kudoksissa vaeltava suuri valkosolu, joka tunnistaa vieraat rakenteet ja ottaa ne sisäänsä fagosytoosilla, jolloin fagosomi fuusioituu lysosomiin ja sisältö hajotetaan. Se esittelee pilkkomansa antigeenin osia muille immuunisoluille ja erittää sytokiineja, jotka käynnistävät tulehduksen. Makrofagit siivoavat myös kuolleet solut ja kuluneet punasolut. Kutsutaan myös: syöjäsolu.",
  2, L('makrofagi', ['valkosolu', 'valkosolun', 'valkosolua', 'valkosolut', 'valkosolujen', 'valkosoluja', 'syöjäsolu', 'syöjäsolun', 'syöjäsolut', 'fagosyytti', 'fagosyytin', 'fagosyytit'])),
K("Mikä on vetyperoksidi?",
  "Reaktiivinen hapetin H<sub>2</sub>O<sub>2</sub>, jota syntyy hajotusreaktioissa ja jonka katalaasi hajottaa vedeksi ja hapeksi.",
  "",
  2, L('vetyperoksidi')),
]
