# -*- coding: utf-8 -*-
"""Johdatus biotekniikkaan, luennot 2 ja 3 (omistaja 12.9.2026: 'tee kortit myos muista biotekniikka luennoista').
Kortit ovat biotek_L2_kortit.py:ssa ja biotek_L3_kortit.py:ssa, luentokalvot kurssit/Johdatus biotekniikkaan/.
Rakentaja on yhteinen pakka_rakenna.rakenna: SOLUKKO.apkg patchataan paikallaan (pakka Luento 1:n rinnalle, kortit
guidin mukaan, kuvat mediaan) ja kurssin kansioon kirjoitetaan luennon oma apkg Ankiin tuotavaksi. Idempotentti.
Aja: python tyokalut/biotek_kortit.py"""
import os, sys
SC = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SC)
from pakka_rakenna import rakenna, REPO
import biotek_L2_kortit, biotek_L3_kortit

if __name__ == '__main__':
    rakenna(os.path.join(REPO, 'kurssit', 'Johdatus biotekniikkaan'), '::Johdatus biotekniikkaan', [biotek_L2_kortit, biotek_L3_kortit],
            'solukko-biotek', sisar_loppu='::Johdatus biotekniikkaan::Luento 1 - Mitä biotekniikka on')
