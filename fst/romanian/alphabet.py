#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fst
import collections

class Alphabet(object):
  def __init__(self):
    # All regular alphabet chars.
    self.SEMIVOWELS = set("jwyɥ")
    self.VOWELS = set("a e i o u œ ɑ ɔ ə ɛ ɨ e̯ i̯ o̯ u̯ ɑ̃ ɛ̃ œ̃ ɔ̃".split()) | self.SEMIVOWELS
    self.CONSONANTS = set("bdfghiklmnprstvzŋɲʁʃʒ") | self.SEMIVOWELS

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
    self.LATERALS = set("l")
    self.NASALS = set("mnŋɲ")
    self.VOICED_FRICATIVES = set("vzʒ")
    self.VOICELESS_FRICATIVES = set("sfʃh") # Swahili dj ch tʃ and dʒ
    self.VOICED_STOPS = set("bdg")
    self.VOICELESS_STOPS = set("ptk")

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
    self.APPROXIMANT = set("jwɥ")
    self.TRILL = set("r")
    self.MANNER_OF_ARTICULATION = [self.NASAL, self.STOP,
                          self.FRICATIVE, self.APPROXIMANT, self.TRILL]
    self.MANNER_OF_ARTICULATION = self.UpdateCategory(self.MANNER_OF_ARTICULATION)


    
    #--PLACE_OF_ARTICULATION--------------------------------------
    self.LABIAL = set("mpbvfw")
    self.DENTAL_ALVEOLAR = set("ntdzslr")
    self.POSTALVEOLAR = set("ʃʒ")
    self.PALATAL = set("ɲɥj")
    self.VELAR_UVULAR = set("kgxŋw")
    self.GLOTTAL = set("h") # check in a separate constraint

    self.PLACE_OF_ARTICULATION = [self.LABIAL, self.DENTAL_ALVEOLAR,
                          self.POSTALVEOLAR, self.PALATAL, 
                          self.VELAR_UVULAR, self.GLOTTAL]
    self.PLACE_OF_ARTICULATION = self.UpdateCategory(self.PLACE_OF_ARTICULATION)
        
    #--STATE_OF_GLOTTIS-------------------------------------------
    self.VOICED = self.VOICED_FRICATIVES | self.VOICED_STOPS
    self.VOICELESS = self.VOICELESS_FRICATIVES | self.VOICELESS_STOPS
    self.STATE_OF_GLOTTIS = [self.VOICED, self.VOICELESS]
    self.STATE_OF_GLOTTIS = self.UpdateCategory(self.STATE_OF_GLOTTIS)


    #-------------------------------------------------------------
  
    # Vowel categories
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

    self.SetWeights(None)

    # Additional data (not charset). 
    self.AR_SW_SIMILAR_VOWELS = set([
        ('ə','o',1.0380364370703896),
        ('ə','jo',1.0735966974535809),
        ('ə','e',0.895027650487594),
        ('ə',('e̯',),0.8949884726994906),
        ('œ',('o̯',),0.9530024723692424),
        ('œ','o',0.9333464516581533),
        ('œ','jo',0.9499134427345964),
        ('œ','e',0.9610085171188425),
        ('œ',('o̯', 'a'),0.9379085409195214),
        ('œ','oa',0.9255700392699587),
        ('ɥ','u',1.0430088499491836),
        ('ɥ','w',0.9286364684248306),
        (('ɑ̃',),'an',None),
        (('ɑ̃',),'en',None),
        (('ɑ̃',),'a',None),
        (('ɑ̃',),'na',None),
        ('ɑ','a',0.8907307067785608),
        (('ɛ̃',),'en',None),
        (('ɛ̃',),'in',None),
        (('ɛ̃',),'ne',None),
        (('ɛ̃',),'e',None),
        ('ɛ','e',0.661038984774555),
        ('ɛ',('e̯',),0.6363860054716742),
        ('ɛ','a',0.8135370366482215),
        ('ɛ','je',0.7206182572479011),
        (('œ̃',),'um',None),
        (('œ̃',),'un',None),
        (('ɔ̃',),'om',None),
        (('ɔ̃',),'on',None),
        (('ɔ̃',),'un',None),
        ('ɔ','o',0.5267476166319659),
        ('ɔ',('o̯',),0.5460810905231345),
        ('ɔ',('a', 'u̯'),0.8447842738510711),
        ('i',('ɨ',),0.8229457884229936),
        ('i',('i̯',),1.0249674944809453),
        ('j',('i̯',),1.0810464532607336),
        ('j',('i̯', 'e'),0.47243828766042717),
        ('e',('e̯',),0.15232798316865637),
        ('y','u',0.7574463982950856),
        ('y',('i̯',),1.0190294362493542),
        ('i','hi',0.38934059863046455),
    ])
    self.AR_SW_SIMILAR_CONSONANTS = set([
        ('ʁ','r',0.4293191088244016),
        ('j',('l', 'i̯'),0.8719546737830226),
        ('s','z',0.6347500015603716),
        ('s','ts',0.19180840435855329),
        ('s','tʃ',0.39100183811107025),
        ('k','tʃ',0.6640136007178203),
        ('ʒ','dʒ',0.23854837716324828),
        ('k','kh',0.0),
        ('ʒ','g',0.9777029365578627),
        ('z','s',0.6347500015603716),
        ('ɲ','gn',0.7342010200701818),
        ('ŋ','ng',0.7547104822137045),
    ]) 

    self.AR_SW_SIMILAR_PHONES = self.AR_SW_SIMILAR_CONSONANTS  | self.AR_SW_SIMILAR_VOWELS
                                # | set([(j, i) for (i, j) in self.AR_SW_SIMILAR_VOWELS])) 

    self.AR_SW_FINAL_VOWELS = set([
        ('e','ə',0.895027650487594),
        ('','e',None),
        ('','ə',None),
        ('','u',None),
        ('e','a',0.9883779902819968),
        ('e','er',0.0),
        (('ɑ̃',),'ent',None),
        ('aʁ','a',None),
        ('',('i̯',),None),
    ])
  
    self.VOWEL_OPERATION_COSTS = set([
        ("j", None, None),   # (Letter, INS cost, DEL cost)
        ("w", None, None),
        ("y", None, None),
        ("ɥ", None, None),
        ("a", None, None),
        ("e", None, None),
        ("i", None, None),
        ("o", None, None),
        ("u", None, None),
        ("œ", None, None),
        ("ɑ", None, None),
        ("ɔ", None, None),
        ("ə", None, None),
        ("ɛ", None, None),
        ("ɨ", None, None),
        ("e̯", None, None),
        ("i̯", None, None),
        ("o̯", None, None),
        ("u̯", None, None),
        ("ɑ̃", None, None),
        ("ɛ̃", None, None),
        ("œ̃", None, None),
        ("ɔ̃", None, None),
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
    self.PASS_THROUGH_SYMS = set()
    if self.OT_CONSTRAINTS is not None:
      if syms is not None:
        # Figure out all possible OT_CONSTRAINTS from the symbol table.
        for s, _ in list(syms.items()):
          if s.startswith("<") and len(s) > 1:
            self.OT_CONSTRAINTS[s]
          else:
            assert s == fst.EPSILON or s in self.ALL_SYMS, s
      self.PASS_THROUGH_SYMS.update(list(self.OT_CONSTRAINTS.keys()))
    self.ALL_SYMS = self.ALL_LETTERS | self.SYLLABLE_BOUNDARIES | self.PASS_THROUGH_SYMS

