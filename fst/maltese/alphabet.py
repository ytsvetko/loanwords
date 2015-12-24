#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fst
import collections

class Alphabet(object):
  def __init__(self):
    # All regular alphabet chars.
    self.SEMIVOWELS = set("jwyɥʎ")
    self.VOWELS = set("ɐ ʌ ʊ a ɑ e i o u œ ɔ ə ɛ ɨ e̯ i̯ o̯ u̯ ɑ̃ ɛ̃ œ̃ ɔ̃ iː uː ɛː ɔː ʊː ɐː".split()) | self.SEMIVOWELS
    self.CONSONANTS = set("bdfghiklmnprstvzŋɲʁʃʒʔħ") | self.SEMIVOWELS

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
    self.VOICED_FRICATIVES = set("vzʒħ")
    self.VOICELESS_FRICATIVES = set("sfʃh") # Swahili dj ch tʃ and dʒ
    self.VOICED_STOPS = set("bdg")
    self.VOICELESS_STOPS = set("ptkʔ")



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
    self.PALATAL = set("ɲɥjʎ")
    self.VELAR_UVULAR = set("kgxŋw")
    self.PHARYNGEAL = set("ħ")
    self.GLOTTAL = set("hʔ") # check in a separate constraint

    self.PLACE_OF_ARTICULATION = [self.LABIAL, self.DENTAL_ALVEOLAR,
                          self.POSTALVEOLAR, self.PALATAL, 
                          self.VELAR_UVULAR, self.PHARYNGEAL, self.GLOTTAL]
    self.PLACE_OF_ARTICULATION = self.UpdateCategory(self.PLACE_OF_ARTICULATION)
        
    #--STATE_OF_GLOTTIS-------------------------------------------
    self.VOICED = self.VOICED_FRICATIVES | self.VOICED_STOPS
    self.VOICELESS = self.VOICELESS_FRICATIVES | self.VOICELESS_STOPS
    self.STATE_OF_GLOTTIS = [self.VOICED, self.VOICELESS]
    self.STATE_OF_GLOTTIS = self.UpdateCategory(self.STATE_OF_GLOTTIS)


    #-------------------------------------------------------------
  
    # Vowel categories    
    self.FRONT_VOWELS = set("i y e ɛ œ ɛ̃ œ̃ e̯ i̯ iː ɛː".split())
    self.CENTRAL_VOWELS = set("ə a ɨ ɐ".split())
    self.BACK_VOWELS = set("ʊ ʌ o u ɑ ɔ ɑ̃ ɔ̃ o̯ u̯ ʊː ɔː uː".split())
    self.VOWEL_FRONTNESS = [self.FRONT_VOWELS, self.CENTRAL_VOWELS, self.BACK_VOWELS]
    self.VOWEL_FRONTNESS = self.UpdateCategory(self.VOWEL_FRONTNESS)
    
    self.HIGH_VOWELS = set("i ɨ i̯ u u̯ ʊ y ʊː".split())
    self.MID_VOWELS = set("e ə a o o̯".split())
    self.LOW_VOWELS = set("ɐ ʌ ɑ ɔ ɑ̃ ɔ̃ ɔː".split())
    self.VOWEL_OPENNESS = [self.HIGH_VOWELS, self.MID_VOWELS, self.LOW_VOWELS]
    self.VOWEL_OPENNESS = self.UpdateCategory(self.VOWEL_OPENNESS)

    self.ROUNDED_VOWELS = set("o o̯ y u u̯ œ œ̃ ɔ ɔ̃ uː".split())
    self.UNROUNDED_VOWELS = set("e e̯ ə a ɨ i i̯ ɛ ɛ̃ ɑ̃ ɑ a ɐ ʌ ʊ ʊː ɛː iː".split())   
    self.VOWEL_ROUNDNESS = [self.ROUNDED_VOWELS, self.UNROUNDED_VOWELS]
    self.VOWEL_ROUNDNESS = self.UpdateCategory(self.VOWEL_ROUNDNESS)


    self.LONG_VOWELS = set("iː uː ɛː ɔː ʊː ɐː".split()) # Maltese
    
    self.NASALIZED = set("ɑ̃ ɛ̃ œ̃ ɔ̃".split()) # French

    self.SetWeights(None)

    # Additional data (not charset). 
    self.AR_SW_SIMILAR_VOWELS = set([
        ('o','u',0.8635526532464384),
        ('o','ɔ',0.5017466145764166),
        ('ɐ','a',0.4993900215954731),
        ('o','e',0.9000758533663158),
        ('a','ɔ',0.7923736000905441),
        ('a','e',1.0226192197562562),
        ('ɛ','i',0.8475354471982393),
        ('ɛ','ji',1.0962188469412133),
        ('u','iu',0.19121045433174555),
        ('u','ɛ',0.7789459899391081),
        ('a','ɐ',0.4993900215954731),
        ('u','w',1.1041530055092486),
        ('i','j',0.6064094293522735),
        ('i','ij',1.1102230246251565e-16),
        ('j','ij',0.05786191896961701),
        ('e','ɛ',0.661038984774555),
        ('o','ʊ',0.8772431730633656),
        ('u','ʊ',0.6094528503703797),
        (('iː',),'i',1.0159740365032093),
        (('uː',),'u',0.6241847955105598),
        (('ɛː',),'ɛ',1.0121906052533176),
        (('ɔː',),'ɔ',0.989765553088179),
        (('ʊː',),'ʊ',0.8265934882246353),
        (('ɐː',),'ɐ',0.9747035957994935),
    ]) 
    
    self.AR_SW_SIMILAR_CONSONANTS = set([
        ('s','z',0.6347500015603716),
        ('z','s',0.6347500015603716),
        ('z','ʒ',0.8924809863315492),
        ('dz','z',0.6734825407846924),
        ('k','g',0.6969555949868861),
        ('g','k',0.6969555949868861),
        ('ɲ','gn',0.7342010200701818),
        ('ɲ','ng',0.7590434132274297),
        ('ʃ','ʒ',0.9260538344228461),
        ('f','v',0.7955288456934504),
        ('p','b',0.7209159856070133),
        #('s', 'ts'), ('s', 'tʃ'), ('k', 'tʃ'), 
    ]) 

    self.AR_SW_SIMILAR_PHONES = (self.AR_SW_SIMILAR_CONSONANTS  | 
                                 self.AR_SW_SIMILAR_VOWELS | 
                                 set([(j, i, d) for (i, j, d) in self.AR_SW_SIMILAR_VOWELS])) 

    self.AR_SW_FINAL_VOWELS = set([
        ('a','u',0.7706785467908345),
        ('ɛ','u',0.7789459899391081),
        ('o','u',0.8635526532464384),
        ('ɔ','u',0.726343452239635),
        ('ɛ','a',0.8135370366482215),
        ('o','a',0.8876386907223511),
        ('ɔ','a',0.7923736000905441),
        ('ɐ','a',0.4993900215954731),
        ('i','ɛ',0.9926375648823907),
        ('e','ɛ',0.661038984774555),
        ('o','',None),
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

