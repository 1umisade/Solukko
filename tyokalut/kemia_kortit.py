# -*- coding: utf-8 -*-
"""Kemian peruskurssi I (omistaja 12.9.2026: 'tee kortit myos kemian peruskurssi I'): luentokalvot kurssit/Kemian peruskurssi I/,
kortit kemia1_kortit.py:ssa (viisi lukua: 1, 2.1, 2.2, 3.1, 3.2 -> korttinumerot 1.xxx, 21.xxx, 22.xxx, 31.xxx, 32.xxx,
koska sivusto lukee numeron liukulukuna). Sama kierros kuin biotek_kortit.py (pakka_rakenna.rakenna).
Aja: python tyokalut/kemia_kortit.py"""
import os, sys
SC = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SC)
from pakka_rakenna import rakenna, REPO
import kemia1_kortit

if __name__ == '__main__':
    rakenna(os.path.join(REPO, 'kurssit', 'Kemian peruskurssi I'), '::Kemian peruskurssi I', kemia1_kortit.LUENNOT, 'solukko-kemia1')
