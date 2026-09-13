# -*- coding: utf-8 -*-
"""Sanaston massakierros omistajan muihin kursseihin (13.9.2026): Molekyylibiologia - teoria (L1-L3), Kasvibiokemia - teoria 1,
Biotekniikan harjoitustyo ja Immunologia - teoria. Kortit menevat suoraan niihin pakkoihin, joissa sanat esiintyvat
(LEHTI = pakan viimeinen osa sellaisenaan, URL:t mukaan lukien). TIEDOSTO estaa erillisen apkg:n kirjoittamisen.
Aja: python tyokalut/muut_kortit.py"""
import os, sys
SC = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SC)
from pakka_rakenna import rakenna, REPO
import sanasto_massa

MOLBIO_L1 = 'Luento 1 - Proteiinit (https://www.youtube.com/watch?v=RT-w2xHVl_E&list=PLs7Y2nGwfz4FL4ZJgONHsl1qp-AZPr3tJ)'
MOLBIO = '::Molekyylibiologia - teoria (BKEM5024) (video_molekyylibiologia) (https://moodle.utu.fi/course/view.php?id=30155) (https://opas.peppi.utu.fi/fi/opintojakso/BKEM5024/99258?period=2024-2027)'

def M(lehti, nro, avain):
    return dict(LEHTI=lehti, NRO=nro, ALKU=100, TIEDOSTO='x', KUVAT={}, KORTIT=sanasto_massa.kortit(avain))

if __name__ == '__main__':
    kansio = os.path.join(REPO, 'kurssit')
    rakenna(kansio, MOLBIO, [M(MOLBIO_L1, 1, 'molbio_L1'), M('Luento 2 - Hiilihydraatit', 2, 'molbio_L2'), M('Luento 3 - Lipidit', 3, 'molbio_L3')], 'solukko-molbio')
    rakenna(kansio, '::2. LUKUVUOSI::2.1 SYKSY::1. Periodi', [M('Kasvibiokemia - teoria 1  (BKEM5010) (video_kasvibiokemia)', 1, 'kasvibiokemia')], 'solukko-kasvi')
    rakenna(kansio, '::2. LUKUVUOSI::2.2 KEVÄT::3. Periodi', [M('Biotekniikan harjoitustyö', 1, 'harjoitustyo')], 'solukko-harj')
    rakenna(kansio, '::3. LUKUVUOSI::3.1 SYKSY::1. Periodi', [M('Immunologia - teoria  (BKEM7020) (video_immunologia)', 1, 'immunologia')], 'solukko-immu')
