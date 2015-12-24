# -*- coding: utf-8 -*-

import phone_transducer as pt
import itertools

def phone_substitution_transducer(add_meta_arc=True):
  """Substitute similar phones (optionally)."""
  def DetectViolation(l_ar, l_sw, group):
    if l_ar == pt.abc.EPSILON or l_sw == pt.abc.EPSILON:
      return False
    if group[l_ar] != group[l_sw]:
      return True
    return False
  
  max_node = 0
  t = pt.Transducer()
  for l in pt.abc.ALL_SYMS:
    t.add_arc(0, 0, l, l)
  for s_ar, s_sw in pt.abc.AR_SW_SIMILAR_PHONES:
    prev_node = 0
    manner_violated = False
    place_violated = False
    sonority_violated = False
    voiced_violated = False
    #frontness_violated = False
    #openness_violated = False
    #roundness_violated = False
    rule_violated = False
    
    for l_ar, l_sw in itertools.zip_longest(s_ar, s_sw, fillvalue=pt.abc.EPSILON):
      max_node += 1
      t.add_arc(prev_node, max_node, l_ar, l_sw) 
      prev_node = max_node
      if not manner_violated:
        manner_violated = DetectViolation(l_ar, l_sw, pt.abc.MANNER_OF_ARTICULATION)
      if not place_violated:
        place_violated = DetectViolation(l_ar, l_sw, pt.abc.PLACE_OF_ARTICULATION)
      sonority_violated = DetectViolation(l_ar, l_sw, pt.abc.SONORITY)
      if not (manner_violated or place_violated):
        voiced_violated = DetectViolation(l_ar, l_sw, pt.abc.STATE_OF_GLOTTIS)
      """
      if not frontness_violated:
        frontness_violated = DetectViolation(l_ar, l_sw, pt.abc.VOWEL_FRONTNESS)
      if not openness_violated:
        openness_violated = DetectViolation(l_ar, l_sw, pt.abc.VOWEL_OPENNESS)
      if not roundness_violated:
        roundness_violated = DetectViolation(l_ar, l_sw, pt.abc.VOWEL_ROUNDNESS)  
      """      
    if manner_violated:
      rule_violated = True
      rule_name = "<<IDENT-IO-manner>>"
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1

    if place_violated:
      rule_violated = True
      rule_name = "<<IDENT-IO-place>>"
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1
    
    if sonority_violated:
      rule_violated = True
      rule_name = "<<IDENT-IO-sonority>>"
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1
    
    if voiced_violated:
      rule_violated = True
      rule_name = "<<IDENT-IO-voiced>>"
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1
    rule_name = None
   
    if s_ar in pt.abc.PHARYNGEAL:
      rule_name = "<<IDENT-IO-PHARYNGEAL>>"
    elif s_ar in pt.abc.PHARYNGEALIZED:
      rule_name = "<<IDENT-IO-PHARYNGEALIZED>>"
    elif s_ar in pt.abc.GLOTTAL:
      rule_name = "<<IDENT-IO-GLOTTAL>>"
    
    """
    el
    if frontness_violated:
      rule_violated = True
      rule_name = "<<IDENT-IO-frontness>>"
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1
      
    if openness_violated:
      rule_violated = True
      rule_name = "<<IDENT-IO-openness>>"
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1

    if roundness_violated:
      rule_violated = True
      rule_name = "<<IDENT-IO-roundness>>"
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1
    """
    rule_name = None
    if s_ar in pt.abc.VOWELS or s_sw in pt.abc.VOWELS and not rule_violated:
      rule_name = "<<IDENT-IO-v>>"
    elif rule_violated: 
      rule_name = "<<IDENT-IO-c>>"
    if rule_name:
      if add_meta_arc:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, rule_name)
      else:
        t.add_arc(max_node, max_node + 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
      max_node += 1

    t.add_arc(max_node, 0, pt.abc.EPSILON, pt.abc.EPSILON)

  t[0].final = True
  return t


def epenthesis_transducer(add_meta_arc=True):
  """Inserts a vowel between two consonants (states 1 and 2) or at the end of
     the word after a consonant. Or just outputs the letters as-is."""
  t = pt.Transducer()
  for l in pt.abc.ALL_SYMS:
    t.add_arc(0, 0, l, l)
  for l in pt.abc.CONSONANTS:
    t.add_arc(0, 1, l, l)
    t.add_arc(2, 0, l, l)
  next_node = 3
  for l in pt.abc.VOWELS:
    t.add_arc(1, next_node, pt.abc.EPSILON, l)

    rule_name = "<<DEP-IO>>"
    if add_meta_arc:
      t.add_arc(next_node, 2, pt.abc.EPSILON, rule_name)
    else:
      t.add_arc(next_node, 2, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
    next_node += 1

  t[0].final = True
  t[2].final = True
  return t

def degemination_transducer(add_meta_arc=True): 
  """Remove repeated consonants (optionally)."""
  t = pt.Transducer()
  for l in pt.abc.ALL_SYMS:
    t.add_arc(0, 0, l, l)
  next_node = 1
  for l in pt.abc.CONSONANTS:
    t.add_arc(0, next_node, l, l)

    rule_name = "<<MAX-IO>>"
    if add_meta_arc:
      t.add_arc(next_node, 0, pt.abc.EPSILON, rule_name)
    else:
      t.add_arc(next_node, 0, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
    next_node += 1

  t[0].final = True
  return t

def final_vowel_substitution_transducer(add_meta_arc=True):
  """Substitute final vowels (optionally)."""
  t = pt.Transducer()
  for l in pt.abc.ALL_SYMS:
    t.add_arc(0, 0, l, l)
    t.add_arc(0, 1, l, l)
  max_node = 1
  for s_ar, s_sw in pt.abc.AR_SW_FINAL_VOWELS:
    prev_node = 0
    for l_ar, l_sw in itertools.zip_longest(s_ar, s_sw, fillvalue=pt.abc.EPSILON):
      max_node += 1
      t.add_arc(prev_node, max_node, l_ar, l_sw) 
      prev_node = max_node
    """
    if len(s_ar) < len(s_sw):
      rule_name = "<<DEP-IO>>"
    else:
      rule_name = "<<IDENT-IO-final>>"
    """
    rule_name = "<<RO_MORPH>>"
    if add_meta_arc:
      t.add_arc(max_node, 1, pt.abc.EPSILON, rule_name)
    else:
      t.add_arc(max_node, 1, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
    max_node += 1

  t.add_arc(1, 1, pt.abc.CONSONANT_DOT, pt.abc.CONSONANT_DOT)
  t.add_arc(1, 1, pt.abc.VOWEL_DOT, pt.abc.VOWEL_DOT)

  t[1].final = True
  return t

def vowel_deletion_transducer(add_meta_arc=True):
  """Deletion of vowels."""
  t = pt.Transducer()
  for l in pt.abc.ALL_SYMS:
    t.add_arc(0, 0, l, l)
  next_node = 1
  for l in pt.abc.VOWELS:
    t.add_arc(0, next_node, l, pt.abc.EPSILON)

    rule_name = "<<MAX-V>>"
    if add_meta_arc:
      t.add_arc(next_node, 0, pt.abc.EPSILON, rule_name)
    else:
      t.add_arc(next_node, 0, pt.abc.EPSILON, pt.abc.EPSILON, pt.abc.OT_CONSTRAINTS[rule_name])
    next_node += 1

  t[0].final = True
  if add_meta_arc:
    pt.AddPassThroughArcs(t)
  return t


def min_consonant_count_transducer(min_consonant_count=3, add_meta_arc=True):
  """Allows only strings with at least |min_consonant_count| consonants."""
  t = pt.Transducer()
  for i in range(min_consonant_count+1):
    for l in pt.abc.ALL_SYMS:
      t.add_arc(i, i, l, l)
    if i > 0:
      for l in pt.abc.CONSONANTS:
        t.add_arc(i-1, i, l, l)
  t[min_consonant_count].final = True
  if add_meta_arc:
    pt.AddPassThroughArcs(t)
  return t

