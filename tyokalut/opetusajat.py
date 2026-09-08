# -*- coding: utf-8 -*-
"""Peppin "Opetusajat" -tekstistä luennot.json, jonka sivusto lataa.

Kurssikoodi on avain, koska sivusto lukee sen jo pakan nimestä: "... (BKEM5030)".
Kurssi voi olla jaettu rinnakkaisiin opetusryhmiin, jolloin jokaisella on oma aikataulunsa.

Periodi paatellaan ensimmaisesta opetuskerrasta, ei toteutuksen muodollisesta alkupaivasta:
opetussuunnitelman rastit kertovat vain missa periodeissa kurssi voi olla, toteutus kertoo
missa se oikeasti on."""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

SC = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SC)
SISAAN = os.path.join(SC, "opetusajat.txt")
ULOS = os.path.join(REPO, "luennot.json")

# Turun yliopiston opetusperiodit. (periodi, alku, loppu) kuukausi-paiva -pareina.
PERIODIT = [(1, (8, 1), (10, 25)), (2, (10, 26), (12, 20)),
            (3, (1, 11), (3, 14)), (4, (3, 15), (5, 23)), (5, (5, 24), (7, 31))]

RIVI = re.compile(r"^(ma|ti|ke|to|pe|la|su)\s+(\d{2})\.(\d{2})\.(\d{4})\s+"
                  r"(\d{1,2})[:.](\d{2})\s*-\s*(\d{1,2})[:.](\d{2})\s*(.*)$")
OTSAKE = re.compile(r"^([A-ZÅÄÖ]{2,}\d{3,}[\w-]*)\s+(.+?),\s*([\d,]+)\s*op\s*$")


def periodi(kk, pv):
    for nro, alku, loppu in PERIODIT:
        if alku <= (kk, pv) <= loppu:
            return nro
    return None


def lue(polku):
    lohkot, nyt = [], []
    for rivi in io.open(polku, encoding="utf-8"):
        r = rivi.rstrip()
        if r.startswith("#") and not r.startswith("##"):
            continue
        if not r.strip():
            if nyt:
                lohkot.append(nyt); nyt = []
            continue
        nyt.append(r)
    if nyt:
        lohkot.append(nyt)
    return lohkot


kurssit = {}
for lohko in lue(SISAAN):
    m = OTSAKE.match(lohko[0])
    if not m:
        print("  OHITETTU, otsake ei tunnistu: %s" % lohko[0][:60]); continue
    koodi, nimi, op = m.group(1), m.group(2).strip(), m.group(3).replace(",", ".")
    toteutus = lohko[1].strip() if len(lohko) > 1 else ""
    ryhmat, ryhma = {}, None
    for r in lohko[2:]:
        if r.startswith("##"):
            ryhma = r[2:].strip(); ryhmat.setdefault(ryhma, []); continue
        k = RIVI.match(r.strip())
        if not k:
            print("  %s: rivia ei tunnistettu: %s" % (koodi, r[:60])); continue
        vk, pv, kk, vuosi, h1, m1, h2, m2, loppu = k.groups()
        osat = [o.strip() for o in loppu.split(";") if o.strip()]
        huomiot = [o for o in osat if re.search(r"pakollinen|seminaari|tiimity|tentti", o, re.I)]
        paikat = [o for o in osat if o not in huomiot]
        kerta = {"pvm": "%s-%s-%s" % (vuosi, kk, pv), "vk": vk,
                 "alkaa": "%02d:%s" % (int(h1), m1), "paattyy": "%02d:%s" % (int(h2), m2),
                 "paikka": ", ".join(paikat)}
        if huomiot:
            kerta["huomio"] = "; ".join(huomiot)
        ryhmat.setdefault(ryhma, []).append(kerta)
    kaikki = [k for lista in ryhmat.values() for k in lista]
    if not kaikki:
        print("  %s: ei yhtaan opetusaikaa" % koodi); continue
    eka = min(k["pvm"] for k in kaikki)
    v, kk, pv = (int(x) for x in eka.split("-"))
    kurssit[koodi] = {"nimi": nimi, "op": float(op), "toteutus": toteutus,
                      "periodi": periodi(kk, pv), "alkaa": eka,
                      "paattyy": max(k["pvm"] for k in kaikki)}
    if list(ryhmat) == [None]:
        kurssit[koodi]["luennot"] = ryhmat[None]
    else:
        kurssit[koodi]["ryhmat"] = {r: lista for r, lista in ryhmat.items() if r}

io.open(ULOS, "w", encoding="utf-8", newline="\n").write(
    json.dumps(kurssit, ensure_ascii=False, indent=2) + "\n")

print("\n%-12s %-34s %3s %-9s %-11s %s" % ("koodi", "kurssi", "op", "periodi", "alkaa", "kertoja"))
print("-" * 92)
for koodi, k in sorted(kurssit.items(), key=lambda kv: kv[1]["alkaa"]):
    if "ryhmat" in k:
        maara = " + ".join("%d" % len(v) for v in k["ryhmat"].values()) + " (%d ryhmaa)" % len(k["ryhmat"])
    else:
        maara = str(len(k["luennot"]))
    print("%-12s %-34s %3.0f %-9s %-11s %s" % (koodi, k["nimi"][:34], k["op"],
                                               "%d. periodi" % k["periodi"], k["alkaa"], maara))
print("\nkirjoitettu:", ULOS, os.path.getsize(ULOS), "tavua")
