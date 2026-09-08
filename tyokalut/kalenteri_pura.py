# -*- coding: utf-8 -*-
"""Kalenterinäkymä on käsin kirjoitettua HTML:ää. Pura sen tapahtumat JSONiksi, jotta näkymä
voidaan jatkossa generoida datasta eikä nykyisiä merkintöjä katoa.

Päiväsolut ovat sisäkkäisiä diveja, joten niitä ei yritetä hahmottaa säännöllisellä lausekkeella.
Jokaiselle tapahtumalle etsitään lähin edeltävä päivänumero, kuukausiotsikko ja päiväsolun luokka."""
import io, json, os, re, sys, collections, datetime
sys.stdout.reconfigure(encoding="utf-8")

SC = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SC)
ULOS = os.path.join(SC, "kalenteri_nykyinen.json")

KUUKAUDET = {"tammikuu": 1, "helmikuu": 2, "maaliskuu": 3, "huhtikuu": 4, "toukokuu": 5,
             "kesäkuu": 6, "heinäkuu": 7, "elokuu": 8, "syyskuu": 9, "lokakuu": 10,
             "marraskuu": 11, "joulukuu": 12}
VIIKONPAIVA = ["ma", "ti", "ke", "to", "pe", "la", "su"]

s = io.open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
alku = s.index('<div id="calendar-view"')
loppu = s.index('<div id="map-view"') if '<div id="map-view"' in s else len(s)
kal = s[alku:loppu]

kurssit = {}
for m in re.finditer(r'data-course="([^"]+)"[^>]*>\s*<span class="cal-swatch" style="background:([^"]+)"></span>'
                     r'<span class="cal-cname">([^<]+)</span>', kal):
    kurssit[m.group(1)] = {"nimi": m.group(3).strip(), "vari": m.group(2).strip()}

# ankkurit: kuukausiotsikot, päivänumerot ja päiväsolujen alut sijainteineen
kuut = [(m.start(), m.group(1)) for m in re.finditer(r'<h3 class="cal-mtitle">([^<]+)</h3>', kal)]
paivat = [(m.start(), int(m.group(1))) for m in re.finditer(r'<div class="cal-num">(\d+)</div>', kal)]
solut = [(m.start(), bool(m.group(1))) for m in re.finditer(r'<div class="cal-day( cal-adj)?">', kal)]


def edellinen(lista, i):
    osuma = None
    for kohta, arvo in lista:
        if kohta < i:
            osuma = arvo
        else:
            break
    return osuma


tapahtumat = collections.defaultdict(list)
ohitettu = 0
for m in re.finditer(r'<div class="cal-ev" data-course="([^"]+)"[^>]*>\s*'
                     r'<span class="cal-ev-t">([^<]+)</span>([^<]*)', kal):
    koodi, aika, teksti = m.group(1), m.group(2), m.group(3)
    if edellinen(solut, m.start()):          # viereisen kuukauden täytesolu: sama tapahtuma on omassa kuukaudessaan
        ohitettu += 1
        continue
    kk_otsikko = edellinen(kuut, m.start())
    pv = edellinen(paivat, m.start())
    if not kk_otsikko or not pv:
        print("  OHITETTU, ankkuria ei löydy: %s %s" % (koodi, aika)); continue
    nimi, vuosi = kk_otsikko.rsplit(" ", 1)
    pvm = datetime.date(int(vuosi), KUUKAUDET[nimi.strip().lower()], pv)
    a = [x.strip() for x in re.split(r"[–—-]", aika) if x.strip()]
    osat = [x.strip() for x in re.split(r"[·•]", teksti) if x.strip()]
    tapahtumat[koodi].append({"pvm": pvm.isoformat(), "vk": VIIKONPAIVA[pvm.weekday()],
                              "alkaa": a[0], "paattyy": a[1] if len(a) > 1 else a[0],
                              "laji": osat[1] if len(osat) > 1 else "",
                              "paikka": " · ".join(osat[2:]) if len(osat) > 2 else ""})

ulos = {}
for koodi, lista in tapahtumat.items():
    lista.sort(key=lambda x: (x["pvm"], x["alkaa"]))
    ulos[koodi] = {"nimi": kurssit.get(koodi, {}).get("nimi", koodi),
                   "vari": kurssit.get(koodi, {}).get("vari", ""),
                   "alkaa": lista[0]["pvm"], "paattyy": lista[-1]["pvm"], "luennot": lista}

io.open(ULOS, "w", encoding="utf-8", newline="\n").write(json.dumps(ulos, ensure_ascii=False, indent=2) + "\n")
print("kuukaudet: %s" % ", ".join(k for _, k in kuut))
print("ohitettu viereisen kuukauden täytesoluista: %d\n" % ohitettu)
print("%-10s %-34s %-9s %-12s %-12s %s" % ("koodi", "kurssi", "väri", "alkaa", "paattyy", "kertoja"))
print("-" * 92)
for koodi, k in sorted(ulos.items(), key=lambda kv: kv[1]["alkaa"]):
    print("%-10s %-34s %-9s %-12s %-12s %d" % (koodi, k["nimi"][:34], k["vari"], k["alkaa"], k["paattyy"], len(k["luennot"])))
print("\nyhteensa %d tapahtumaa" % sum(len(k["luennot"]) for k in ulos.values()))
print("kirjoitettu:", ULOS)
