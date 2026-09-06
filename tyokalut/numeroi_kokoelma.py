# -*- coding: utf-8 -*-
"""Every card's question side starts with an order number. It lives in Anki only: the site reads it
as the deck's sort key and strips it before showing anything.

Skipped: Image Occlusion notetypes (field 0 is occlusion data, not a question) and the "Esittely"
cover cards, which are not part of any deck's ordering."""
import zipfile, sqlite3, tempfile, os, shutil, sys, json, re, collections
sys.stdout.reconfigure(encoding="utf-8")

SC = os.path.dirname(os.path.abspath(__file__))
APKG = os.path.join(os.path.dirname(SC), "SOLUKKO.apkg")   # repon juuri
NUMERO = "(1) "
SEP = chr(31)
JN = re.compile(r"^(?:\s|&nbsp;|<[^>]*>)*\(\s*\d+(?:[.,]\d+)?\s*\)")
tk = lambda v: re.sub(r"\s+", " ", re.sub("<[^>]*>", " ", v or "")).strip()

work = tempfile.mkdtemp()
with zipfile.ZipFile(APKG) as z: z.extractall(work)
dbn = "collection.anki21" if os.path.exists(os.path.join(work, "collection.anki21")) else "collection.anki2"
con = sqlite3.connect(os.path.join(work, dbn)); cur = con.cursor()
models = json.loads(cur.execute("select models from col").fetchone()[0])

numeroitavat = {mid for mid, m in models.items()
                if m.get("flds") and m["flds"][0]["name"] in ("Kysymys", "Content")}
print("numeroitavat korttityypit: %s" % [models[m]["name"] for m in numeroitavat])
print("ohitetaan: %s" % [m["name"] for k, m in models.items() if k not in numeroitavat])

lisatty = 0
ohitettu = collections.Counter()
for nid, mid, flds in list(cur.execute("select id, mid, flds from notes")):
    if str(mid) not in numeroitavat:
        ohitettu["vaara korttityyppi"] += 1; continue
    osat = flds.split(SEP)
    if not osat or not osat[0].strip():
        ohitettu["tyhja kysymys"] += 1; continue
    if JN.match(osat[0]):
        ohitettu["numero jo olemassa"] += 1; continue
    if tk(osat[0]).lower() == "esittely":
        ohitettu["kansikortti"] += 1; continue
    osat[0] = NUMERO + osat[0]
    cur.execute("update notes set flds=?, usn=-1 where id=?", (SEP.join(osat), nid))
    lisatty += 1

con.commit()
print("\nnumero lisatty: %d muistiinpanoon" % lisatty)
for syy, n in ohitettu.most_common(): print("   ohitettu (%s): %d" % (syy, n))

ilman = [tk(f)[:60] for f, in cur.execute("select flds from notes")
         if not JN.match(f.split(SEP)[0])]
print("\nilman numeroa jai %d:" % len(ilman))
for q in ilman[:12]: print("   · %s" % q)
print("\neheys:", cur.execute("pragma integrity_check").fetchone()[0])
print("kortteja %d, muistiinpanoja %d" % (
    cur.execute("select count(*) from cards").fetchone()[0],
    cur.execute("select count(*) from notes").fetchone()[0]))
con.close()

with zipfile.ZipFile(APKG, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(work)): z.write(os.path.join(work, f), f)
shutil.rmtree(work, ignore_errors=True)
print("\nkirjoitettu:", APKG, os.path.getsize(APKG), "tavua")
