#!/usr/bin/env python
# -*- coding: utf-8 -*-

import phone_transducer as pt

def syllabification_transducer(add_meta_arc=True):
  """Appends CONSONANT_DOTs and VOWEL_DOTs symbols."""
  t = pt.Transducer()

  for l in pt.abc.CONSONANTS:
    t.add_arc(0, 1, l, l)
    t.add_arc(1, 1, l, l)
    t.add_arc(2, 1, l, l)
  t.add_arc(1, 0, pt.abc.EPSILON, pt.abc.CONSONANT_DOT)

  for l in pt.abc.VOWELS:
    t.add_arc(0, 2, l, l)
    t.add_arc(1, 2, l, l)
    t.add_arc(2, 2, l, l)
  t.add_arc(2, 0, pt.abc.EPSILON, pt.abc.VOWEL_DOT)

  t[0].final = True
  return t

def unsyllabification_transducer(add_meta_arc=True):
  """Removes the CONSONANT_DOT and VOWEL_DOT symbols from the output."""
  t = pt.Transducer()
  for l in pt.abc.ALL_SYMS:
    if l in pt.abc.SYLLABLE_BOUNDARIES:
      t.add_arc(0, 0, l, pt.abc.EPSILON)
    else:
      t.add_arc(0, 0, l, l)
  t[0].final = pt.abc.OT_CONSTRAINTS["<<BIAS>>"]
  return t
