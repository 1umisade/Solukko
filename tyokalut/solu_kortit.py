# -*- coding: utf-8 -*-
"""Solu- ja biomolekyylit - teoria, luennot 3 ja 4a (omistaja 12.9.2026: 'tee kortit myos uusista solu ja biomolekyylit
luennoista'). Kortit solu_L3_kortit.py ja solu_L4a_kortit.py, kalvot kurssit/BKEM5030 Solu- ja biomolekyylit - teoria/.
Rakentaja pakka_rakenna.rakenna: SOLUKKO.apkg patchataan (pakat Luento 2:n rinnalle, kortit guidin mukaan, kuvat
mediaan) ja kurssin kansioon kirjoitetaan luentopakat Ankiin tuotavaksi. Idempotentti. Aja: python tyokalut/solu_kortit.py"""
import os, sys
SC = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SC)
from pakka_rakenna import rakenna, REPO
import solu_L3_kortit, solu_L4a_kortit, solu_L1_sanasto, solu_L2_sanasto, solu_L3_sanasto, solu_L4a_sanasto

if __name__ == '__main__':
    rakenna(os.path.join(REPO, 'kurssit', 'BKEM5030 Solu- ja biomolekyylit - teoria'), '::Solu- ja biomolekyylit - teoria (BKEM5030)',
            [solu_L3_kortit, solu_L4a_kortit, solu_L1_sanasto, solu_L2_sanasto, solu_L3_sanasto, solu_L4a_sanasto], 'solukko-solu', sisar_loppu='::Solu- ja biomolekyylit - teoria (BKEM5030)::Luento 2 - Vesi')
