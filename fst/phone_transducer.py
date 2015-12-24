#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import math
import fst, operator
import alphabet
import sys
from functools import reduce

abc = alphabet.Alphabet()

syms = fst.SymbolTable()

semiring = 'tropical'

def Transducer(isyms=None, osyms=None, semiring=semiring):
  global syms
  if isyms is None:
    isyms = syms
  if osyms is None:
    osyms = syms
  return fst.Transducer(isyms=isyms, osyms=osyms, semiring=semiring)

def GetPaths(t, return_full_path_in_ostring=False):
  if len(t) == 0:
    raise StopIteration
  seen_paths = set()
  for path in t.paths():
    path_istring = []
    path_ostring = []
    path_ot_constraints = []
    path_weights = []
    full_path = []
    for arc in path:
      path_weights.append(arc.weight)
      isymbol = abc.EPSILON
      osymbol = abc.EPSILON
      if arc.ilabel != fst.EPSILON_ID:
        isymbol = t.isyms.find(arc.ilabel)
        if isymbol in abc.ALL_LETTERS:
          path_istring.append(isymbol)
      if arc.olabel != fst.EPSILON_ID:
        osymbol = t.osyms.find(arc.olabel)
        if osymbol in abc.OT_CONSTRAINTS:
          path_ot_constraints.append(osymbol)
        elif osymbol in abc.SYLLABLE_BOUNDARIES:
          osymbol = "."
        else:
          assert osymbol in abc.ALL_LETTERS, osymbol
          path_ostring.append(osymbol)
      if isymbol != abc.EPSILON or osymbol != abc.EPSILON:
        full_path.append((isymbol, osymbol))
    path_istring = tuple(path_istring)
    path_ostring = ''.join(path_ostring)
    path_id = (path_istring, path_ostring, tuple(path_ot_constraints))
    if path_id in seen_paths:
      continue
    seen_paths.add(path_id)
    if return_full_path_in_ostring:
      path_ostring = full_path
    yield (path_istring, path_ostring, path_ot_constraints, path_weights)

def PrintPaths(t, num_shortest=None):
  """Prints paths of the transducer t."""
  if num_shortest is not None:
    t = t.shortest_path(num_shortest)
  if len(t) == 0:
    print("No paths found")
    return  
  for path_istring, path_ostring, path_ot_constraints, path_weights in GetPaths(t):
    if path_weights:
      # Use the overloaded multiply operator, which is a sum operation in the log space.
      path_weight = float(reduce(operator.mul, path_weights))
    else:
      path_weight = 0.0
    print(('{} | {} | {} | {} '.format(
        "".join(path_istring), path_ostring, path_weight, path_ot_constraints)))

def PrintFullPaths(t, num_shortest=None):
  if num_shortest is not None:
    t = t.shortest_path(num_shortest)
  if len(t) == 0:
    print("No paths found")
    return
  ar_words = []
  constraints = []
  weights = []
  full_out_string = []
  full_path_string = []
  for path_istring, full_path, path_ot_constraints, path_weights in GetPaths(t, return_full_path_in_ostring=True):
    if path_weights:
      # Use the overloaded multiply operator, which is a sum operation in the log space.
      path_weight = float(reduce(operator.mul, path_weights))
    else:
      path_weight = 0.0
    ar_words.append("".join(path_istring))
    full_out_string.append("".join([ochar for ichar, ochar in full_path if ochar != abc.EPSILON]))
    full_path_string.append(str(full_path))
    constraints.append("#".join(path_ot_constraints))
    weights.append(str(path_weight))
  print("{} ||| {} ||| {} ||| {} ||| {}\n".format(
      " ".join(ar_words),
      " ".join(constraints),
      " ".join(weights),
      " ".join(full_out_string),
      " $ ".join(full_path_string)))

def PrintOutputsForInput(transducer, input_str):
  inp = fst.linear_chain(input_str, syms=transducer.isyms, semiring=semiring)
  combined = (inp >> transducer)
  PrintFullPaths(combined)

def AddPassThroughArcs(transducer):
  for state_num in range(len(transducer)):
    for sym in abc.PASS_THROUGH_SYMS:
      transducer.add_arc(state_num, state_num, sym, sym)

def AddSyllabificationArcs(transducer):
  for state_num in range(len(transducer)):
    for sym in abc.SYLLABLE_BOUNDARIES:
      transducer.add_arc(state_num, state_num, sym, sym)

def Minimize(t):
  t.remove_epsilon()
  # FST seems to not always determinize on the first try.
  for _ in range(100):
    if t.input_deterministic:
      break
    t = t.determinize()
  assert t.input_deterministic
  t.minimize()
  assert t.isyms == syms
  assert t.osyms == syms
  return t

def linear_chain(in_str, out_str=None, total_weight=None):
  """Creates a transducer that accepts only input string 'in_str' and outputs 'out_str'."""
  if out_str is None:
    out_str = in_str
  t = Transducer()
  i = 0
  for in_char, out_char in itertools.zip_longest(in_str, out_str, fillvalue=abc.EPSILON):
    t.add_arc(i, i+1, in_char, out_char)
    i += 1
  if total_weight:
    t.add_arc(i, i+1, abc.EPSILON, abc.EPSILON, total_weight)
    i += 1
  t[i].final = True
  return t

def accept_all_transducer():
  t = Transducer()
  for l in abc.ALL_SYMS:
    t.add_arc(0, 0, l, l)
  t[0].final = True
  return t

def weights_transducer():
  t = Transducer()
  for l in abc.ALL_SYMS:
    if l in abc.OT_CONSTRAINTS:
      t.add_arc(0, 0, l, l, abc.OT_CONSTRAINTS[l])
    else:
      # Regular non-operation character
      t.add_arc(0, 0, l, l)
  t[0].final = True
  t.arc_sort_input()
  return t

def Compose(transducers, add_meta_arc=True):
  if add_meta_arc:
    print("  adding pass through")
    for t in transducers:
      AddPassThroughArcs(t)
      t.arc_sort_input()

  print("  combining")
  combined = transducers[0]
  for t in transducers[1:]:
    print(".", sep="", end="")
    sys.stdout.flush()
    combined.arc_sort_output()
    combined = combined >> t
  print()
  return combined

def UnionLinearChains(in_word_list, out_str=None):
  t = Transducer()
  for w in in_word_list:
    t.set_union(linear_chain(w, out_str=out_str))
  return t

