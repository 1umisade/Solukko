# CLAUDE.md

1. Ask, don't assume. If something is unclear, ask before writing a single line. Never make silent assumptions about intent, architecture, or requirements.

2. Simplest solution first. Always implement the simplest thing that could work. Do not add abstractions or flexibility that weren't explicitly requested.

3. Don't touch unrelated code. If a file or function is not directly part of the current task, do not modify it, even if you think it could be improved.

4. Flag uncertainty explicitly. If you are not confident about an approach or technical detail, say so before proceeding. Confidence without certainty causes more damage than admitting a 
   gap.

---

**Perehdytys projektiin: lue [PROJEKTI.md](PROJEKTI.md) ensin.** Se kertoo mikä Solukko on, miten kortit kulkevat Ankista sivustolle, mitkä sopimukset korteissa on ja mihin sudenkuoppiin täällä on jo kompastuttu. Korttien sisältösäännöt ovat [kurssit/CLAUDE.md](kurssit/CLAUDE.md):ssä.

---

**Rinnakkaiset agentit (omistaja 13.9.2026).** Tässä työhakemistossa voi olla useampi agentti töissä yhtä aikaa. Työnjako on tiedostotasolla: yksi agentti `simulaatiot/`-puolella, toinen `index.html` + `tyokalut/` + apkg-puolella. Jos tehtäväsi vaatii toisen puolen tiedostoa, sano se omistajalle äläkä muokkaa sitä ohi hänen. Säännöt:

1. Committaa vain omat, nimetyt tiedostosi – ei `git add .` eikä hakemistoja. Tarkista `git status` ennen committia: vieras muutos jää työhakemistoon.
2. Ei `git checkout --`, `stash`, `reset` tai `restore` tiedostolle, jota et itse muuttanut tässä sessiossa.
3. `git pull --rebase` ennen pushia. `SOLUKKO.apkg`:ta patchaa vain yksi agentti kerrallaan.
4. Jos `index.html`:ää pitää muokata molemmilta puolilta, tehdään peräkkäin, ei rinnakkain.

