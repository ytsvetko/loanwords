# -*- coding: utf-8 -*-

import phone_transducer as pt

"""
We add disambiguating metadata arcs related to OT constraints
only if OT constraints are violated in the final form before 
un-syllabication

Additional OT constraints are added in operations.py"""

def nocoda_transducer(add_meta_arc=True):
  """Syllables are open."""
  t = pt.Transducer()
  for l in pt.abc.ALL_LETTERS:
    t.add_arc(0, 0, l, l)

  for l in pt.abc.CONSONANTS:
    t.add_arc(0, 1, l, l)  
  t.add_arc(1, 2, pt.abc.CONSONANT_DOT, pt.abc.CONSONANT_DOT)
  t.add_arc(1, 2, pt.abc.VOWEL_DOT, pt.abc.VOWEL_DOT)
  rule_name = "<<NOCODA>>"
  if add_meta_arc:
    t.add_arc(2, 0, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(2, 0, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])

  for l in pt.abc.VOWELS | pt.abc.SYLLABLE_BOUNDARIES:
    t.add_arc(0, 3, l, l)  
  t.add_arc(3, 0, pt.abc.CONSONANT_DOT, pt.abc.CONSONANT_DOT)
  t.add_arc(3, 0, pt.abc.VOWEL_DOT, pt.abc.VOWEL_DOT)

  t[0].final = True
  return t

def no_complex_margin_transducer(add_meta_arc=True):
  """No consonants around syllable boundaries. E.g. 'c.b'"""
  t = pt.Transducer()
  for l in pt.abc.VOWELS:
    t.add_arc(0, 0, l, l)
    t.add_arc(1, 0, l, l)
    t.add_arc(2, 0, l, l)

  for l in pt.abc.SYLLABLE_BOUNDARIES:
    t.add_arc(0, 0, l, l)
    t.add_arc(1, 2, l, l)
    t.add_arc(2, 0, l, l)

  for l in pt.abc.ALL_LETTERS - pt.abc.VOWELS:
    t.add_arc(0, 1, l, l)
    t.add_arc(1, 1, l, l)
    t.add_arc(2, 3, l, l)

  rule_name = "<<*COMPLEX-margin>>"
  if add_meta_arc:
    t.add_arc(3, 1, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(3, 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])

  t[0].final = True
  t[1].final = True
  t[2].final = True
  return t


def no_complex_transducer(add_meta_arc=True):
  """No consonant clusters."""
  t = pt.Transducer()
  for l in pt.abc.VOWELS:
    t.add_arc(0, 0, l, l)
    t.add_arc(1, 0, l, l)

  for l in pt.abc.SYLLABLE_BOUNDARIES:
    t.add_arc(0, 0, l, l)
    t.add_arc(1, 0, l, l)

  for l in pt.abc.ALL_LETTERS - pt.abc.VOWELS:
    t.add_arc(0, 1, l, l)
    t.add_arc(1, 2, l, l)
    
  rule_name = "<<*COMPLEX>>"
  if add_meta_arc:
    t.add_arc(2, 1, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(2, 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])

  t[0].final = True
  t[1].final = True
  return t


def peak_transducer(add_meta_arc=True):
  """In a syllable sonority goes up then down (bell shaped)."""
  t = pt.Transducer()
  # Exact Peak implementation is replaced by its approxiamtion: 
  # fire the Peak constraint if there is more than one vowel/semivowel/nasal in a sylable

  peaks = pt.abc.VOWELS - pt.abc.SEMIVOWELS
  not_peaks = pt.abc.ALL_SYMS - peaks

  for l in not_peaks:
    t.add_arc(0, 0, l, l)
    t.add_arc(1, 1, l, l)
  
  for l in peaks:
    t.add_arc(0, 1, l, l)
    t.add_arc(1, 2, l, l)

  for l in pt.abc.SYLLABLE_BOUNDARIES:
    t.add_arc(1, 0, l, l)
    t.add_arc(0, 0, l, l)

  # if more than one peak -- violation 
  rule_name = "<<PEAK>>"
  if add_meta_arc:
    t.add_arc(2, 1, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(2, 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
  
  t[0].final = True
  return t


  
def ssp_transducer(add_meta_arc=True):
  """complex onsets rise in sonority toward the nucleus, 
     complex codas fall in sonority."""
  t = pt.Transducer()
  """Simplified version for open syllables
  sonority_letters = set()
  for i, sonority_set in enumerate(pt.abc.SONORITY_LIST[:-2]):
    state_num = i + 1
    for l in sonority_set:
      sonority_letters.add(l)
      for j in range(state_num+1):
        t.add_arc(j, state_num, l, l)

  for i in range(0, state_num + 1):
    for l in pt.abc.SYLLABLE_BOUNDARIES | (pt.abc.ALL_LETTERS - sonority_letters):
      t.add_arc(i, 0, l, l)

  for i in range(1, state_num + 1):
    rule_name = "<<SSP>>"
    if add_meta_arc:
      t.add_arc(i, 0, pt.abc.EPSILON, rule_name)
    else:
      t.add_arc(i, 0, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])

  t[0].final = True
  return t
  """
  # going up in sonority in a syllable
  for i, sonority_set in enumerate(pt.abc.SONORITY_LIST):
    t.add_arc(i, i+1, pt.abc.EPSILON, pt.abc.EPSILON)
    for l in sonority_set:
      t.add_arc(i, i+1, l, l)
      t.add_arc(i+1, i+1, l, l)
  max_sonority = len(pt.abc.SONORITY_LIST)

  # going down in sonority in a syllable
  max_state = max_sonority
  for i, sonority_set in enumerate(reversed(pt.abc.SONORITY_LIST)):
    i += max_sonority
    max_state = i+1
    t.add_arc(i, i+1, pt.abc.EPSILON, pt.abc.EPSILON)
    for l in sonority_set:
      t.add_arc(i, i+1, l, l)
      t.add_arc(i+1, i+1, l, l)

  t.add_arc(max_state, 0, pt.abc.CONSONANT_DOT, pt.abc.CONSONANT_DOT)
  t.add_arc(max_state, 0, pt.abc.VOWEL_DOT, pt.abc.VOWEL_DOT)

  # if syllable letters are not in bell shape -- violation 
  rule_name = "<<SSP>>"
  if add_meta_arc:
    t.add_arc(max_state, 0, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(max_state, 0, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
  t[0].final = True
  return t
  #"""
  
def no_complex_vow_transducer(add_meta_arc=True):
  """No vowel clusters."""
  t = pt.Transducer()
  for l in pt.abc.CONSONANTS:
    t.add_arc(0, 0, l, l)
    t.add_arc(1, 0, l, l)

  for l in pt.abc.VOWELS - pt.abc.CONSONANTS:
    t.add_arc(0, 1, l, l)  
    t.add_arc(1, 2, l, l)  
    
  rule_name = "<<*COMPLEX_VOW>>"
  if add_meta_arc:
    t.add_arc(2, 1, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(2, 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])

  for l in pt.abc.SYLLABLE_BOUNDARIES:
    t.add_arc(0, 0, l, l)
    t.add_arc(1, 1, l, l)

  t[0].final = True
  t[1].final = True
  return t

def onset_transducer(add_meta_arc=True):
  """Syllables start with a consonant."""
  t = pt.Transducer()
  for l in pt.abc.CONSONANTS:
    t.add_arc(0, 1, l, l)
    t.add_arc(3, 1, l, l)

  for l in pt.abc.VOWELS - pt.abc.SEMIVOWELS:
    t.add_arc(0, 2, l, l)
    t.add_arc(3, 2, l, l)

  for l in pt.abc.ALL_LETTERS:
    t.add_arc(1, 1, l, l)

  for l in pt.abc.SYLLABLE_BOUNDARIES:
    t.add_arc(1, 3, l, l)

  rule_name = "<<ONSET>>"
  if add_meta_arc:
    t.add_arc(2, 1, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(2, 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])

  t[1].final = True
  t[3].final = True
  return t


def length_transducer(add_meta_arc=True):
  """Syllables should have at most 3 letters."""
  t = pt.Transducer()
  for l in pt.abc.ALL_LETTERS:
    t.add_arc(0, 1, l, l)
    t.add_arc(1, 2, l, l)
    t.add_arc(2, 3, l, l)
    t.add_arc(3, 4, l, l)


  for l in pt.abc.SYLLABLE_BOUNDARIES:
    t.add_arc(1, 0, l, l)
    t.add_arc(2, 0, l, l)
    t.add_arc(3, 0, l, l)

  rule_name = "<<LEN>>"
  if add_meta_arc:
    t.add_arc(4, 3, pt.abc.EPSILON, rule_name)
  else:
    t.add_arc(4, 3, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])

  t[0].final = True 
  t[5].final = True
  return t

