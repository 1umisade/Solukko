# -*- coding: utf-8 -*-
"""Linkkisanojen taivutus biotekniikan pakoille (kurssit/CLAUDE.md §4: yksikon nom, gen, part, iness, elat, illat
+ monikon nom, gen, part, iness). Paatteen mukaan: -i (ryhmat_3d.taivuta, lisaksi nti -> nn), -io, -ia, -us/-ys,
-uus/-yys, -e, -a/-ä, -nen. Monisanaiset ja poikkeukset annetaan valmiina listana."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ryhmat_3d


def _A(w):
    return 'a' if ryhmat_3d.sointu(w)[0] == 'a' else 'ä'


def taiv(w):
    A = _A(w)
    if w.endswith('nti'):
        S = w[:-1]; W = w[:-3] + 'nn'
        return [w, W+'in', S+'i'+A, W+'iss'+A, W+'ist'+A, S+'iin', W+'iksi', W+'it', S+'ien', S+'ej'+A, W+'eiss'+A]
    if w.endswith('i'):
        return ryhmat_3d.taivuta(w)
    if w.endswith('io') or w.endswith('iö'):
        return [w, w+'n', w+'t'+A, w+'ss'+A, w+'st'+A, w+w[-1]+'n', w+'t', w+'iden', w+'it'+A, w+'iss'+A]
    if w.endswith('ia') or w.endswith('iä'):
        b = w[:-1]
        return [w, w+'n', w+A, w+'ss'+A, w+'st'+A, w+w[-1]+'n', w+'t', b+'oiden', b+'oit'+A, b+'oiss'+A]
    if w.endswith('uus') or w.endswith('yys'):
        b = w[:-1]
        return [w, b+'den', b[:-1]+'tt'+A, b+'dess'+A, b+'dest'+A, b+'teen', b+'det', w+'ien', b+'ksi'+A, b+'ksiss'+A]
    if w.endswith('us') or w.endswith('ys'):
        b = w[:-1] + 'kse'
        return [w, b+'n', w+'t'+A, b+'ss'+A, b+'st'+A, b+'en', b+'t', w+'ten', w[:-1]+'ksi'+A, w[:-1]+'ksiss'+A]
    if w.endswith('nen'):
        b = w[:-3] + 'se'
        return [w, b+'n', w[:-3]+'st'+A, b+'ss'+A, b+'st'+A, b+'en', b+'t', w[:-3]+'sten', w[:-3]+'si'+A, w[:-3]+'siss'+A]
    if w.endswith('luku'):   # massaluku -> massaluvun (k -> v)
        b = w[:-2] + 'v'
        return [w, b+'un', w+'a', b+'ussa', b+'usta', w+'un', b+'ut', w+'jen', w+'ja', b+'uissa']
    if w.endswith('o') or w.endswith('ö'):   # jakso -> jakson, jaksoa, jaksojen
        v = w[-1]
        return [w, w+'n', w+A, w+'ss'+A, w+'st'+A, w+v+'n', w+'t', w+'jen', w+'j'+A, w+'iss'+A]
    if w.endswith('e'):
        b = w + 'e'
        return [w, b+'n', w+'tt'+A, b+'ss'+A, b+'st'+A, b+'seen', b+'t', w+'iden', w+'it'+A, w+'iss'+A]
    if w.endswith('a') or w.endswith('ä'):
        v = w[-1]; b = w[:-1]
        pl = (b+'ojen', b+'oj'+A, b+'oiss'+A) if len(w) <= 6 else (b+'ien', b+'i'+A, b+'iss'+A)
        return [w, w+'n', w+v, w+'ss'+A, w+'st'+A, w+v+'n', w+'t'] + list(pl)
    raise ValueError('taivutusta ei ole: ' + w)


def L(*sanat):
    """linkkisanat-kentta: sanat taivutetaan, listat otetaan sellaisenaan"""
    out = []
    for s in sanat:
        out += s if isinstance(s, list) else taiv(s)
    seen = set(); return ', '.join(x for x in out if not (x in seen or seen.add(x)))
