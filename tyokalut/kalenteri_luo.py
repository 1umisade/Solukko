# -*- coding: utf-8 -*-
"""Rakentaa kalenterinäkymän index.html:ään datasta.

Lähteet:
  luennot.json                  Pepistä poimitut opetusajat (opetusajat.py)
  tyokalut/kalenteri_nykyinen.json  vanhasta käsin kirjoitetusta näkymästä puretut merkinnät

Kurssivalitsin ryhmitellään lukuvuoden ja periodin mukaan. Kurssille, jolla on rinnakkaisia
opetusryhmiä, tulee pudotusvalikko: vain valitun ryhmän kerrat näkyvät kalenterissa."""
import io, json, os, re, sys, datetime, collections
sys.stdout.reconfigure(encoding="utf-8")

SC = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SC)
HTML = os.path.join(REPO, "index.html")

KUUKAUSI = ["tammikuu", "helmikuu", "maaliskuu", "huhtikuu", "toukokuu", "kesäkuu",
            "heinäkuu", "elokuu", "syyskuu", "lokakuu", "marraskuu", "joulukuu"]
VIIKONPAIVAT = ["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]

EI_AIKOJA = "Opetusaikoja ei vielä julkaistu."


def _avain(nimi):
    """Nimi vertailumuodossa: pienet kirjaimet, ajatusviiva yhdysmerkiksi, yksi välilyönti."""
    return re.sub(r"\s+", " ", (nimi or "").lower().replace("–", "-").replace("—", "-")).strip()


# Opetussuunnitelma (tyokalut/opetussuunnitelma.txt): vuosi, periodit, koodi, nimi.
# Antaa jokaiselle kurssille lukuvuoden ja periodin ja tuo listaan myos kurssit, joilla ei ole aikoja.
OPS = []
for rivi in io.open(os.path.join(SC, "opetussuunnitelma.txt"), encoding="utf-8"):
    rivi = rivi.rstrip("\n")
    if not rivi.strip() or rivi.startswith("#"):
        continue
    vuosi, periodit, koodi, nimi = rivi.split("\t")
    OPS.append({"vuosi": int(vuosi), "periodit": [int(p) for p in periodit.split(",")],
                "koodi": None if koodi.strip() == "-" else koodi.strip(), "nimi": nimi.strip()})

VARIT = ["#FFF2CC", "#DDEBF7", "#FCE4D6", "#E4DFEC", "#E2EFDA", "#FFE699", "#BDD7EE",
         "#F8CBAD", "#CCC0DA", "#C6E0B4", "#FBE2D5", "#DEEAF6", "#EDEDED", "#FFF0B3", "#D9E2F3"]

PERIODIT = [(1, (8, 1), (10, 25)), (2, (10, 26), (12, 20)),
            (3, (1, 11), (3, 14)), (4, (3, 15), (5, 23)), (5, (5, 24), (7, 31))]


def periodi(pvm):
    kk, pv = pvm.month, pvm.day
    for nro, a, b in PERIODIT:
        if a <= (kk, pv) <= b:
            return nro
    return 0


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---- lue lähteet -------------------------------------------------------------
kurssit = {}
vanha = json.load(io.open(os.path.join(SC, "kalenteri_nykyinen.json"), encoding="utf-8"))
for koodi, k in vanha.items():
    kurssit[koodi] = {"nimi": k["nimi"], "vari": k.get("vari") or "", "ryhmat": {None: k["luennot"]}}

uusi = json.load(io.open(os.path.join(REPO, "luennot.json"), encoding="utf-8"))
for koodi, k in uusi.items():
    ryhmat = k["ryhmat"] if "ryhmat" in k else {None: k["luennot"]}
    if koodi in kurssit:
        kurssit[koodi]["ryhmat"] = ryhmat          # tuoreempi data voittaa
    else:
        kurssit[koodi] = {"nimi": k["nimi"], "vari": "", "ryhmat": ryhmat}

# opetussuunnitelma: lukuvuosi ja periodi kurssille, ja listaan myos kurssit ilman aikoja
nimella = {_avain(k["nimi"]): koodi for koodi, k in kurssit.items()}
for o in OPS:
    koodi = o["koodi"] if o["koodi"] in kurssit else nimella.get(_avain(o["nimi"]))
    if koodi is None:
        koodi = o["koodi"] or "OPS:" + _avain(o["nimi"]).replace(" ", "_")
        kurssit[koodi] = {"nimi": o["nimi"], "vari": "", "ryhmat": {}}
    kurssit[koodi]["vuosi"] = o["vuosi"]
    kurssit[koodi]["periodi"] = o["periodit"][0]

# värit: vanhat säilyvät, uusille seuraava vapaa. Kurssi ilman aikoja ei tarvitse väriä.
kaytetyt = {k["vari"] for k in kurssit.values() if k["vari"]}
vapaat = [v for v in VARIT if v not in kaytetyt]
for koodi in sorted(kurssit):
    if not kurssit[koodi]["vari"] and kurssit[koodi]["ryhmat"]:
        kurssit[koodi]["vari"] = vapaat.pop(0) if vapaat else "#EDEDED"

# ---- tapahtumat päivittäin ---------------------------------------------------
paivat = collections.defaultdict(list)
for koodi, k in kurssit.items():
    for ryhma, lista in k["ryhmat"].items():
        for e in lista:
            pvm = datetime.date(*[int(x) for x in e["pvm"].split("-")])
            paivat[pvm].append((koodi, ryhma, e))
    if k["ryhmat"]:
        k.setdefault("alkaa", min(x["pvm"] for lista2 in k["ryhmat"].values() for x in lista2))
for lista in paivat.values():
    lista.sort(key=lambda t: (t[2]["alkaa"], t[0]))

# kurssit, jotka eivat ole opetussuunnitelmassa: periodi ensimmaisen kerran paivasta, lukuvuosi "Muut"
for koodi, k in kurssit.items():
    k.setdefault("periodi", periodi(datetime.date(*[int(x) for x in k["alkaa"].split("-")])) if k.get("alkaa") else 0)
    k.setdefault("vuosi", 0)

# ---- kurssivalitsin ----------------------------------------------------------
osat = ['<div class="cal-layout"><div class="cal-courses"><div class="cal-courses-title">Näytä kursseja</div>']
ryhmitelty = collections.defaultdict(lambda: collections.defaultdict(list))
for koodi, k in kurssit.items():
    ryhmitelty[k["vuosi"]][k["periodi"]].append(koodi)
for vuosi in sorted(ryhmitelty, key=lambda v: v or 99):
    osat.append('<div class="cal-year-block">')
    osat.append('<label class="cal-year"><input type="checkbox" class="cal-cb-all" '
                'onchange="calValitseKaikki(this)"><span>%s</span></label>'
                % (("%d. lukuvuosi" % vuosi) if vuosi else "Muut"))
    for per in sorted(ryhmitelty[vuosi], key=lambda p: p or 99):
        osat.append('<div class="cal-period-block">')
        otsikko = ("%d. periodi" % per) if per else "ajankohta auki"
        if any(kurssit[c]["ryhmat"] for c in ryhmitelty[vuosi][per]):
            osat.append('<label class="cal-period"><input type="checkbox" class="cal-cb-all" '
                        'onchange="calValitseKaikki(this)"><span>%s</span></label>' % otsikko)
        else:   # pelkkia kursseja ilman aikoja: otsikko ilman valintaruutua
            osat.append('<div class="cal-period cal-period-tyhja"><span>%s</span></div>' % otsikko)
        for koodi in sorted(ryhmitelty[vuosi][per], key=lambda c: kurssit[c]["nimi"]):
            k = kurssit[koodi]
            if not k["ryhmat"]:   # opetussuunnitelmassa, mutta aikoja ei ole: nakyy, ei valittavissa
                osat.append('<div class="cal-course cal-tyhja"><span class="cal-swatch"></span>'
                            '<span class="cal-cname">%s<span class="cal-note">%s</span></span></div>' % (esc(k["nimi"]), EI_AIKOJA))
                continue
            osat.append('<label class="cal-course"><input type="checkbox" class="cal-cb" data-course="%s" '
                        'onchange="updateCalHighlight()"><span class="cal-swatch" style="background:%s"></span>'
                        '<span class="cal-cname">%s</span></label>' % (koodi, k["vari"], esc(k["nimi"])))
            if list(k["ryhmat"]) != [None]:
                valinnat = "".join('<option value="%s">%s</option>' % (esc(r), esc(r)) for r in sorted(k["ryhmat"]))
                osat.append('<select class="cal-group" data-course="%s" onchange="updateCalHighlight()">%s</select>'
                            % (koodi, valinnat))
        osat.append('</div>')
    osat.append('</div>')
osat.append('</div><div class="cal-body">')

# ---- kuukausiruudukot --------------------------------------------------------
eka, vika = min(paivat), max(paivat)
kk = datetime.date(eka.year, eka.month, 1)
while kk <= vika:
    lead = kk.weekday()
    viimeinen = (datetime.date(kk.year + (kk.month == 12), kk.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    osat.append('<div class="cal-month">\n<h3 class="cal-mtitle">%s %d</h3>\n<div class="cal-grid">'
                % (KUUKAUSI[kk.month - 1].capitalize(), kk.year))
    osat += ['<div class="cal-wd">%s</div>' % v for v in VIIKONPAIVAT]
    for i in range(42):
        pv = i - lead + 1
        if pv < 1 or pv > viimeinen:
            osat.append('<div class="cal-day cal-empty"></div>')
            continue
        pvm = datetime.date(kk.year, kk.month, pv)
        evs = []
        for koodi, ryhma, e in paivat.get(pvm, []):
            k = kurssit[koodi]
            osatek = [k["nimi"]] + [x for x in (e.get("laji"), e.get("paikka"), e.get("huomio")) if x]
            teksti = " &middot; ".join(esc(x) for x in osatek)
            aika = "%s&ndash;%s" % (e["alkaa"], e["paattyy"])
            evs.append('<div class="cal-ev" data-course="%s"%s style="background:%s" title="%s %s">'
                       '<span class="cal-ev-t">%s</span> %s</div>'
                       % (koodi, ' data-group="%s"' % esc(ryhma) if ryhma else "", k["vari"],
                          aika.replace("&ndash;", "-"), esc(" ".join(osatek)), aika, teksti))
        osat.append('<div class="cal-day">\n<div class="cal-num">%d</div>\n<div class="cal-evs">\n%s</div>\n</div>'
                    % (pv, "\n".join(evs) + ("\n" if evs else "")))
    osat.append('</div>\n</div>')
    kk = datetime.date(kk.year + (kk.month == 12), kk.month % 12 + 1, 1)
osat.append('</div></div>')

uusi_html = "\n".join(osat)

s = io.open(HTML, encoding="utf-8").read()
alku = s.index('<div id="calendar-view" style="display:none;">') + len('<div id="calendar-view" style="display:none;">')
loppu_ankkuri = s.index('<div id="map-view"')
paate = s.rindex("</div>", alku, loppu_ankkuri)          # calendar-view'n oma sulkeva tagi
io.open(HTML, "w", encoding="utf-8", newline="\n").write(s[:alku] + "\n" + uusi_html + "\n  " + s[paate:])

print("kursseja %d, tapahtumapaivia %d, kuukausia %d"
      % (len(kurssit), len(paivat), uusi_html.count('class="cal-month"')))
print("tapahtumia %d\n" % uusi_html.count('<div class="cal-ev"'))
print("%-10s %-34s %-6s %-9s %-8s %s" % ("koodi", "kurssi", "vuosi", "periodi", "vari", "kertoja"))
print("-" * 92)
for koodi in sorted(kurssit, key=lambda c: (kurssit[c]["vuosi"] or 99, kurssit[c]["periodi"], kurssit[c]["nimi"])):
    k = kurssit[koodi]
    maara = " + ".join(str(len(v)) for v in k["ryhmat"].values()) or "ei aikoja"
    print("%-10s %-34s %-6s %-9s %-8s %s" % (koodi[:10], k["nimi"][:34], k["vuosi"] or "?",
                                             "%d. periodi" % k["periodi"], k["vari"] or "-", maara))
