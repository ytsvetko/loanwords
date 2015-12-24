#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import phone_transducer as pt
import collections

class Morphemes(object):
  def __init__(self):
   # Arabic.
    # disclaimer: Arabic affixes below exclude short vowels, while the Swahili prefixes below include them.
    self.AR_PREFIXES = set(['ʔl', 'ʔl', 'nuʕ', 'bʔ', 'taʕ', 'fʔ', 'ʔ', 'ʕ', 'liʔ', 'ja', 'na', 'la', 'kʔ', 'ja', 'naʕ', 'biʔ', 'tuʕ', 'ta', 'mu', 'lima', 'mʔt', 'b', 'tu', 'ka', 'θ', 'wʔ', 'sʔ', 'lʔ', 'w', 't', 'n', 'fj', 'bi', 'bj', 'fa', 'wʔ']) 
    self.AR_SUFFIXES = set(["a", "ʔ", "i", "n", "u", "ij", "ki", "na", "ni", "tu", "ja", "j"])

    
    # Swahili.
    self.SW_PREFIXES = set(["ku", "ɑl", "wɑnɑ", "ki", "wɑ", "u", "tɑ", "ɑki", "wɑli", "ɑnɑ", "wɑki", "ɑi", "mɑ", "wɑliɔ", "imɛ", "m", "unɑ", "inɑ"])
    self.SW_SUFFIXES = set(["u", "i", "fu", "wɑ", "iɑ", "ziɑ", "ti" ])

morphemes = Morphemes()

def strip_transducer(morpheme_set, operation_weight, add_meta_arc, rule_name):
  """Transducer that removes strings. Used for AR suffixes and prefixes"""
  t = pt.Transducer()
  t[0].final = True
  for w in morpheme_set:
    out_str = []
    if add_meta_arc:
      out_str = [rule_name]
    t.set_union(pt.linear_chain(w, out_str, operation_weight))
  return t

def append_transducer(morpheme_set, operation_weight, add_meta_arc, rule_name, add_closure=False):
  """Transducer that appends strings. Used for SW suffixes and prefixes"""
  t = pt.Transducer()
  t[0].final = True
  for w in morpheme_set:
    if add_meta_arc:
      w = list(w)
      w.append(rule_name)
    t.set_union(pt.linear_chain("", w, operation_weight))
  if add_closure:
    t.set_closure()
  return t

def ar_morphology_transducer(add_meta_arc=True, with_syllabification=False):
  """Removes one AR prefix and one suffix (optionally)."""
  rule_name = "<<IT_MORPH>>"
  if add_meta_arc:
    operation_weight = None
  else:
    operation_weight = pt.abc.OT_CONSTRAINTS[rule_name]
  t = strip_transducer(morphemes.AR_PREFIXES, operation_weight, add_meta_arc, rule_name)
  t.concatenate(pt.accept_all_transducer())
  t.concatenate(strip_transducer(morphemes.AR_SUFFIXES, operation_weight, add_meta_arc, rule_name))
  if add_meta_arc:
    pt.AddPassThroughArcs(t)
  if with_syllabification:
    pt.AddSyllabificationArcs(t)
  #t.arc_sort_input()
  return t

def sw_morphology_transducer(add_meta_arc=True, with_syllabification=False):
  """Appends SW prefixes and suffixes (optionally)."""
  rule_name = "<<MT_MORPH>>"
  if add_meta_arc:
    operation_weight = None
  else:
    operation_weight = pt.abc.OT_CONSTRAINTS[rule_name]
  t = append_transducer(morphemes.SW_PREFIXES, operation_weight, add_meta_arc, rule_name)
  #t.concatenate(append_transducer(morphemes.SW_PREFIXES, operation_weight, add_meta_arc, rule_name))
  t.concatenate(pt.accept_all_transducer())
  t.concatenate(append_transducer(morphemes.SW_SUFFIXES, operation_weight, add_meta_arc, rule_name))
  if add_meta_arc:
    pt.AddPassThroughArcs(t)
  if with_syllabification:
    pt.AddSyllabificationArcs(t)
  #t.arc_sort_output()
  return t

