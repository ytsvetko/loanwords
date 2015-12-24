#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fst
import collections
# arabic sounds "ʔ w j n a u i iː ɛ b t θ dʒ ħ x d ð r z s ʃ sʰ dʰ tʰ zʰ ʕ ɣ f q k l h m n"
# swahili sounds not in arabic 'pʰ', 'g', 'ŋ', 'ɲ', 'tʃʰ', 'ɑ', 'p', 'kʰ', 'ɔ', 'v', 'tʃ', 'ɟ'

class Alphabet(object):
  def __init__(self):
    # All regular alphabet chars.
    self.SEMIVOWELS = set("ʔwj")
    self.VOWELS = set("a u i iː ɛ ɑ ɔ e o".split()) | self.SEMIVOWELS
    self.CONSONANTS = set("ʎ b t ʁ θ dʒ ħ x d ð r z s ʒ ʃ sʰ dʰ tʰ zʰ ʕ ɣ f q k l h m n ŋ ɲ pʰ g ŋ ɲ tʃʰ p kʰ v tʃ ɟ".split()) | self.SEMIVOWELS

    self.ALL_LETTERS = self.VOWELS | self.CONSONANTS
    # Special chars.
    self.EPSILON = fst.EPSILON
    self.CONSONANT_DOT = ".C."
    self.VOWEL_DOT = ".V."

    self.SYLLABLE_BOUNDARIES = set([self.CONSONANT_DOT, self.VOWEL_DOT])
    self.ALL_SYMS = self.ALL_LETTERS | self.SYLLABLE_BOUNDARIES  # This is updated in ReInitSymbolTable

    # Consonant categories
    #--SONORITY--------------------------------------------------
    self.FLAPS = set("rʁ")
    self.LATERALS = set("lʎ")
    self.NASALS = set("mnŋɲ")
    self.VOICED_FRICATIVES = set("ð z zʰ dʒ ɣ ʕ v ʒ ħ".split())
    self.VOICELESS_FRICATIVES = set("f s sʰ θ ʃ x h tʃʰ tʃ".split()) # Swahili dj ch tʃ and dʒ
    self.VOICED_STOPS = set("b d dʰ g ɟ".split())
    self.VOICELESS_STOPS = set("p pʰ t tʰ k q ʔ kʰ".split())

    # Hogg and McCully’s Sonority Scale (1987)
    self.SONORITY_LIST = [self.VOICELESS_STOPS, self.VOICED_STOPS,
                          self.VOICELESS_FRICATIVES, self.VOICED_FRICATIVES,
                          self.NASALS, self.LATERALS, self.FLAPS,
                          self.SEMIVOWELS, self.VOWELS - self.SEMIVOWELS]
    self.SONORITY = self.UpdateCategory(self.SONORITY_LIST)

    #--MANNER_OF_ARTICULATION-------------------------------------
    self.NASAL = set("mnŋɲ")
    self.STOP = self.VOICED_STOPS | self.VOICELESS_STOPS
    self.FRICATIVE = self.VOICED_FRICATIVES | self.VOICELESS_FRICATIVES
    self.APPROXIMANT = set("jwʔɥ")
    self.TRILL = set("r")
    self.MANNER_OF_ARTICULATION = [self.NASAL, self.STOP,
                          self.FRICATIVE, self.APPROXIMANT, self.TRILL]
    self.MANNER_OF_ARTICULATION = self.UpdateCategory(self.MANNER_OF_ARTICULATION)


    
    #--PLACE_OF_ARTICULATION--------------------------------------
    self.LABIAL = set("mbfwpv")
    self.PHARYNGEALIZED = set("sʰ dʰ tʰ pʰ tʃʰ kʰ".split())
    self.DENTAL_ALVEOLAR = set("ð s d t n θ l r ŋ ɲ z".split())
    self.POSTALVEOLAR = set("ʃ dʒ ʒ tʃ".split())
    self.PALATAL = set("ɲ ɥ j ʎ ɟ".split())
    self.VELAR_UVULAR = set("k q x ɣ g ŋ".split())
    self.PHARYNGEAL = set("ħ ʕ") # check in a separate constraint
    self.GLOTTAL = set("h ʔ".split()) # check in a separate constraint

 


    self.PLACE_OF_ARTICULATION = [self.LABIAL, 
                          self.PHARYNGEALIZED, 
                          self.DENTAL_ALVEOLAR,
                          self.POSTALVEOLAR, self.PALATAL, 
                          self.VELAR_UVULAR, self.PHARYNGEAL, 
                          self.GLOTTAL]
    self.PLACE_OF_ARTICULATION = self.UpdateCategory(self.PLACE_OF_ARTICULATION)
        
    #--STATE_OF_GLOTTIS-------------------------------------------
    self.VOICED = self.VOICED_FRICATIVES | self.VOICED_STOPS
    self.VOICELESS = self.VOICELESS_FRICATIVES | self.VOICELESS_STOPS
    self.STATE_OF_GLOTTIS = [self.VOICED, self.VOICELESS]
    self.STATE_OF_GLOTTIS = self.UpdateCategory(self.STATE_OF_GLOTTIS)


    #-------------------------------------------------------------
  
    # Vowel categories
    """
    self.FRONT_VOWELS = set("i y e ɛ œ ɛ̃ œ̃ e̯ i̯".split())
    self.CENTRAL_VOWELS = set("ə a ɨ".split())
    self.BACK_VOWELS = set("o u ɑ ɔ ɑ̃ ɔ̃ o̯ u̯".split())
    self.VOWEL_FRONTNESS = [self.FRONT_VOWELS, self.CENTRAL_VOWELS, self.BACK_VOWELS]
    self.VOWEL_FRONTNESS = self.UpdateCategory(self.VOWEL_FRONTNESS)
    
    self.HIGH_VOWELS = set("i ɨ i̯ u u̯".split())
    self.MID_VOWELS = set("e ə a o o̯".split())
    self.LOW_VOWELS = set("ɑ ɔ ɑ̃ ɔ̃".split())
    self.VOWEL_OPENNESS = [self.HIGH_VOWELS, self.MID_VOWELS, self.LOW_VOWELS]
    self.VOWEL_OPENNESS = self.UpdateCategory(self.VOWEL_OPENNESS)

    self.ROUNDED_VOWELS = set("o o̯ y u u̯ œ œ̃ ɔ ɔ̃".split())
    self.UNROUNDED_VOWELS = set("e e̯ ə a ɨ i i̯ ɛ ɛ̃ ɑ̃ ɑ".split())   
    self.VOWEL_ROUNDNESS = [self.ROUNDED_VOWELS, self.UNROUNDED_VOWELS]
    self.VOWEL_ROUNDNESS = self.UpdateCategory(self.VOWEL_ROUNDNESS)

    self.NASALIZED = set("ɑ̃ ɛ̃ œ̃ ɔ̃".split()) # French
    """
    self.SetWeights(None)

    # Additional data (not charset). 
    self.AR_SW_SIMILAR_VOWELS = set([
      ('ʔ', 'ɑ'),
      (('a', 'j'), 'ɛ'),
      (('j', 'ʔ'), 'ɑ'),
      ('ʕ', 'ɑ'),
      ('w', 'ɔ'),
      ('a', 'u'),
      ('w', 'u'),
      ('j', ('i', 'ɑ')),
      ('a', 'i'),
      ('ʔ', 'ɔ'),
      ('j', 'ɛ'),
      ('ʔ', 'i'),
      ('a', 'ɛ'),
      ('w', 'i'),
      ('j', 'i'),
      ('i', 'ɛ'),
      ('w', 'ɛ'),
      ('i', 'ɑ'),
      ('w', 'ɑ'),
    ])

    self.AR_SW_SIMILAR_CONSONANTS = set([
      ('ɣ', 'g'),
      (('tʰ',), 't'),
      (('dʒ',), 'ɟ'),
      (('zʰ',), 'ð'),
      (('dʰ',), 'ð'),
      (('dʒ', 'j'), 'ɟ'),
      ('w', 'v'),
      ('θ', 't'),
      ('ħ', 'h'),
      (('sʰ',), 's'),
      (('n', 'ɣ'), 'ŋ'),
      (('sʰ',), 'z'),
      ('ʕ', 'r'),
      ('ʃ', ('tʃ',)),
      ('x', 'h'),
      (('t', 'ʃ'),
      ('tʃ',)),
      (('q', 'r'), 'k'),
      ('f', 'v'),
      ('q', 'k'),
      (('n', 'j'), 'ɲ'),
      ('s', 'ʃ'),
      (('n', 'dʒ'), 'ŋ'),
      ('r', 'ɑ'),
      ('q', 'g'),
      (('dʒ',), 'g'),
      ('f', 'w'),
      ('b', 'p'),
    ])


    self.AR_SW_SIMILAR_PHONES = self.AR_SW_SIMILAR_CONSONANTS  | self.AR_SW_SIMILAR_VOWELS #| set([(j, i) for (i, j) in self.AR_SW_SIMILAR_VOWELS]) 

    self.AR_SW_FINAL_VOWELS = set([
        ('w', 'i'), 
        ('u', 'i'), 
        ('u', 'a'), 
        ('a', 'i'), 
        ('ʔ', 'i'), 
        ('j', 'a'), 
        ('j', 'i'),
    ])
  
   
  def UpdateCategory(self, category_list):
    category = {}
    for i, s_set in enumerate(category_list):
      for l in s_set:
        category[l] = i+1
    for l in self.ALL_SYMS:
      if l not in category:
        category[l] = i+1
    return category

  def SetWeights(self, ot_constraint_weights):
    self.OT_CONSTRAINTS = ot_constraint_weights
    self.ReInitSymbolTable()

  def ReInitSymbolTable(self, syms=None):
    unexpected_syms = set()
    self.PASS_THROUGH_SYMS = set()
    if self.OT_CONSTRAINTS is not None:
      if syms is not None:
        # Figure out all possible OT_CONSTRAINTS from the symbol table.
        for s, _ in list(syms.items()):
          if s.startswith("<") and len(s) > 1:
            self.OT_CONSTRAINTS[s]
          else:
            if s != fst.EPSILON and s not in self.ALL_SYMS:
              unexpected_syms.add(s)
        assert len(unexpected_syms) == 0, unexpected_syms
      self.PASS_THROUGH_SYMS.update(list(self.OT_CONSTRAINTS.keys()))
    self.ALL_SYMS = self.ALL_LETTERS | self.SYLLABLE_BOUNDARIES | self.PASS_THROUGH_SYMS

