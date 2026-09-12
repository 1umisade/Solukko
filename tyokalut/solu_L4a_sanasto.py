# -*- coding: utf-8 -*-
"""Solu- ja biomolekyylit, Luento 4a: sanaston taydennys (numerot 4.101-). Rakentaa tyokalut/solu_kortit.py."""
from biotek_taivutus import L
from pakka_rakenna import K

LEHTI = 'Luento 4a - Biologinen tiedonsiirto ja evoluutio'
TIEDOSTO = 'Luento 4a - Sanasto (lisays)'
NRO = 4
ALKU = 100
KUVAT = {}

KORTIT = [
K("Mikä on nukleoemäs?",
  "Nukleotidin typpipitoinen rengasrakenteinen osa: adeniini, guaniini, sytosiini, tymiini tai urasiili.",
  "Nukleoemäs on nukleotidin informaatiota kantava osa, aromaattinen heterorengas, jossa on hiilen lisäksi typpeä. Puriinit adeniini ja guaniini ovat kaksirenkaisia, pyrimidiinit sytosiini, tymiini ja urasiili yksirenkaisia. Emäkset pariutuvat vetysidoksin komplementaarisesti, ja niiden järjestys DNA:ssa on geneettinen tieto. Nimi emäs tulee siitä, että renkaan typet voivat vastaanottaa protonin. Kutsutaan myös: emäs, typpiemäs.",
  3, L(['nukleoemäs', 'nukleoemäksen', 'nukleoemästä', 'nukleoemäksessä', 'nukleoemäksestä', 'nukleoemäkseen', 'nukleoemäkset', 'nukleoemästen', 'nukleoemäksiä', 'nukleoemäksissä', 'typpiemäs', 'typpiemäksen', 'typpiemästä', 'typpiemäkset', 'typpiemästen', 'typpiemäksiä'])),
K("Mikä on nukleoemäsjärjestys?",
  "Nukleotidien emästen järjestys DNA- tai RNA-ketjussa, jota luetaan 5'-päästä 3'-päähän.",
  "Nukleoemäsjärjestys on nukleiinihapon primaarirakenne ja sen sisältämä tieto: kirjaimien A, C, G ja T tai U jono. Se ilmoitetaan aina 5'→3'-suunnassa koodaavan juosteen mukaan. Kolme peräkkäistä emästä muodostaa kodonin, ja järjestys määrää proteiinin aminohappojärjestyksen. Sekvensointi lukee tämän järjestyksen, ja mutaatio on sen muutos. Kutsutaan myös: emäsjärjestys, nukleotidijärjestys, DNA-sekvenssi.",
  3, L('nukleoemäsjärjestys', ['emäsjärjestys', 'emäsjärjestyksen', 'emäsjärjestystä', 'emäsjärjestyksessä', 'emäsjärjestyksestä', 'nukleotidijärjestys', 'nukleotidijärjestyksen', 'nukleotidijärjestystä', 'nukleotidijärjestyksessä', 'DNA-sekvenssi', 'DNA-sekvenssin', 'DNA-sekvenssiä', 'DNA-sekvenssit'])),
K("Mikä on pentoosi?",
  "Viisihiilinen sokeri, kuten nukleotidien riboosi ja deoksiriboosi.",
  "",
  2, L('pentoosi', ['pentoosisokeri', 'pentoosisokerin', 'pentoosisokeria'])),
K("Mitä rekombinaatio tarkoittaa?",
  "DNA-jaksojen vaihtoa kahden molekyylin välillä, jolloin syntyy uusia geeniyhdistelmiä.",
  "Rekombinaatiossa kaksi DNA-molekyyliä katkeaa ja liittyy ristiin, jolloin jaksot vaihtavat paikkaa. Meioosissa vastinkromosomit rekombinoituvat, ja jälkeläinen saa vanhempiensa geeneistä uusia yhdistelmiä, mikä on evoluution vaihtelun lähde. Koska katkos osuu todennäköisimmin pitkään introniin, ehjät eksonit siirtyvät kokonaisina ja voivat yhdistyä uusiksi geeneiksi. Rekombinaatio korjaa myös DNA-vaurioita, ja bakteerit vaihtavat sillä geenejä.",
  3, L('rekombinaatio', ['rekombinoitua', 'rekombinoituu', 'rekombinoituvat', 'tekijäinvaihdunta', 'tekijäinvaihdunnan'])),
K("Mikä on lysotsyymi?",
  "Pieni entsyymi, joka pilkkoo bakteerien soluseinän peptidoglykaania. Syljen ja kyynelten puolustusentsyymi.",
  "",
  1, L('lysotsyymi')),
K("Mikä on säätelyalue?",
  "Geenin DNA-jakso, johon säätelyproteiinit ja RNA-polymeraasi sitoutuvat ja joka määrää transkription käynnistymisen.",
  "Säätelyalue sijaitsee geenin edessä ja sisältää promoottorin sekä operaattorin tai muita sitoutumiskohtia. Siihen sitoutuvat säätelyproteiinit, aktivaattorit ja repressorit, jotka helpottavat tai estävät polymeraasin sitoutumista solun tarpeiden mukaan. Eukaryooteilla säätelyalueita on myös kaukana geenistä, ja DNA taipuu tuomaan ne promoottorin viereen. Säätelyalueen mutaatio muuttaa geenin ilmentymistä, ei sen tuotetta. Kutsutaan myös: säätelysekvenssi.",
  2, L('säätelyalue', ['säätelysekvenssi', 'säätelysekvenssin', 'säätelysekvenssiä', 'säätelysekvenssit', 'säätelysekvenssejä', 'säätelyproteiini', 'säätelyproteiinin', 'säätelyproteiinit', 'säätelyproteiineja', 'aktivaattori', 'aktivaattorin', 'aktivaattorit'])),
K("Mikä on nukleotiditrifosfaatti?",
  "Nukleotidi, jossa on kolme fosfaattia, kuten ATP tai GTP. Nukleiinihappojen rakennusaine ja energian kantaja.",
  "Nukleotiditrifosfaatissa sokerin 5'-hiileen on liittynyt kolme fosfaattia peräkkäin, ja niiden väliset fosfoanhydridisidokset ovat energiarikkaita. RNA-polymeraasi ja DNA-polymeraasi käyttävät trifosfaatteja rakennusaineina: liittäminen ketjuun vapauttaa kaksi fosfaattia pyrofosfaattina, ja sen energia ajaa reaktion. ATP ja GTP ovat lisäksi solun yleiskäyttöisiä energian kantajia, ja sykliset nukleotidit toimivat viestimolekyyleinä. Kutsutaan myös: NTP, dNTP.",
  2, L('nukleotiditrifosfaatti', ['trifosfaatti', 'trifosfaatin', 'trifosfaattia', 'trifosfaatit', 'NTP', 'dNTP', 'GTP', 'GTP:n', 'GTP:tä', 'pyrofosfaatti', 'pyrofosfaatin', 'pyrofosfaattia'])),
]
