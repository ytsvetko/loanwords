#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import phone_transducer as pt
import syllabification, morphology
import operations, ot_constraints
import collections
import hashlib
import math
import argparse
import sys, os, glob
import time
import operator
from functools import reduce

parser = argparse.ArgumentParser()
parser.add_argument('--test_file')

parser.add_argument('--ar_pronunciation_dict')
parser.add_argument('--sw_pronunciation_dict')


parser.add_argument('--remove_meta_arcs', default=False, action='store_true')
parser.add_argument('--with_syllabification', default=False, action='store_true')
parser.add_argument('--only_initialize_transducers', default=False, action='store_true')

parser.add_argument('--in_ot_constraint_weights')
parser.add_argument('--out_ot_constraint_weights')
parser.add_argument('--default_weight', default=0.0, type=float)

parser.add_argument('--min_consonant_count', default=1, type=int)
parser.add_argument('--shortest_sw_word_len', default=3, type=int)
parser.add_argument('--start_line', default=0, type=int)
parser.add_argument('--worker_id', default=0, type=int)
parser.add_argument('--num_workers', default=1, type=int)

parser.add_argument('--num_predicted_best_paths', default=1, type=int)
parser.add_argument('--minimize_final_transducer', action='store_true')
args = parser.parse_args()


class DirNames(object):
  def __init__(self, base_dir, ar_pron_dict_file_name, test_file_name,
               add_meta_arc, with_syllabification):
    self.syms_hash = self.SetHash(pt.abc.ALL_SYMS)
    self.ar_pron_dict_hash = self.FileHash(ar_pron_dict_file_name)
    if not add_meta_arc:
      self.weights_hash = self.DictHash(pt.abc.OT_CONSTRAINTS)
    else:
      self.weights_hash = "no_weights"
    self.test_file_hash = self.FileHash(test_file_name)
    self.add_meta_arc = add_meta_arc
    self.base_dir = base_dir
    depends_on_syms_dir = os.path.join(self.base_dir, "syms_" + self.syms_hash)
    reachable_paths_dir = os.path.join(self.base_dir, "reachable_paths")
    depends_on_meta_dir = os.path.join(depends_on_syms_dir, "with_meta_" + str(add_meta_arc).lower())
    depends_on_weights = os.path.join(depends_on_meta_dir, "weight_" +self.weights_hash)
    if with_syllabification:
      depends_on_syllabification = os.path.join(depends_on_weights, "with_syllabification")
    else:
      depends_on_syllabification = depends_on_weights
    self.paths = {
        'reachable_test_dir' : os.path.join(reachable_paths_dir, self.test_file_hash),
        'loanwords_tr' : os.path.join(depends_on_syllabification, 'loanwords.tr'),
        'ar_post_tr' : os.path.join(depends_on_weights, 'ar_post.tr'),
        'sw_pre_tr' : os.path.join(depends_on_syllabification, 'sw_pre.tr'),
        'ar_vocab_dir' : os.path.join(depends_on_syms_dir, 'ar_vocab_' + self.ar_pron_dict_hash),
        'test_samples_dir' : os.path.join(depends_on_syllabification, 'test_samples_' + self.test_file_hash),
        'test_out_dir' : os.path.join(depends_on_syllabification, 'test_out_' + self.test_file_hash),
    }
    self.MakeDirs()

  def MakeDirs(self):
    for k, path in self.paths.items():
      if not k.endswith('_dir'):
        path = os.path.dirname(path)
      os.makedirs(path, exist_ok=True)

  def FileHash(self, filename):
    if not filename:
      return "no_file"
    m = hashlib.md5()
    for byte_line in open(filename, "rb"):
      m.update(byte_line)
    return m.hexdigest()

  def SetHash(self, s):
    m = hashlib.md5()
    m.update(str(tuple(sorted(s))).encode("utf-8"))
    return m.hexdigest()

  def DictHash(self, d):
    m = hashlib.md5()
    m.update(str(tuple(sorted(d.items()))).encode("utf-8"))
    return m.hexdigest()

def LoadWeightsFromFile(filename):
  def default_weight():
    return args.default_weight
  result = collections.defaultdict(default_weight)
  if filename and os.path.isfile(filename):
    for line in open(filename):
      line = line.strip()
      if len(line) == 0 or line.startswith("#"):
        continue
      key, weight = line.split("\t")
      assert key not in result, key
      result[key] = max(0.0, float(weight))
  return result

def SaveWeightsToFile(weight_dict, filename):
  if filename:
    f = open(filename + ".tmp", "w")
    for k, v in weight_dict.items():
      f.write("{}\t{}\n".format(k, v))
    os.rename(filename + ".tmp", filename)

def LoadVocabFromFile(pron_dict, limit=None, group_size=5000, transducer_file_pattern=None):
  """Returns a transducer that accepts and outputs all words in the input file."""
  #Load and return groups of minimized ar_vocab transducers (if exist)
  filenames = list(glob.iglob(transducer_file_pattern))
  if len(filenames) > 0 :
    all_transducers = [LoadTransducerFromFile(f) for f in filenames]
    return all_transducers, True

  print("Loading the vocab file")
  vocab = set()
  for word, ipa_pron_set in pron_dict.items():
    for ipa_pron in ipa_pron_set:
      vocab.add(ipa_pron)  # ipa_pron is tuple('d', 'o̯', 'e̯')
    if limit is not None and len(vocab) > limit:
      break

  print("Checking missing letters in Alphabet")
  seen_letters = set()
  for w in vocab:
    seen_letters.update(set(w))
  missing_letters = seen_letters - pt.abc.ALL_LETTERS
  assert len(missing_letters) == 0, missing_letters

  print("Building transducer")
  print("Vocab size:", len(vocab), "num groups:", math.ceil(len(vocab) / group_size))

  all_transducers = []
  for i, w in enumerate(vocab):
    if i % group_size == 0:
      print(".", sep="", end="")
      t = pt.Transducer()
      all_transducers.append(t)
    t.set_union(pt.linear_chain(w))
  print()
  return all_transducers, False

def ComposeAllTransducers(add_meta_arc=True, with_syllabification=False, only_init=False):
  print("  initializing transducers")
  transducers = [
      # All Operations go here.
      operations.degemination_transducer(add_meta_arc=add_meta_arc),
      operations.phone_substitution_transducer(add_meta_arc=add_meta_arc),
      operations.epenthesis_transducer(add_meta_arc=add_meta_arc),
      operations.final_vowel_substitution_transducer(add_meta_arc=add_meta_arc),

      syllabification.syllabification_transducer(add_meta_arc=add_meta_arc),

      # All OT Constraints transducers here.
      ot_constraints.nocoda_transducer(add_meta_arc=add_meta_arc),
      ot_constraints.no_complex_transducer(add_meta_arc=add_meta_arc),
      ot_constraints.no_complex_margin_transducer(add_meta_arc=add_meta_arc),
      ot_constraints.no_complex_vow_transducer(add_meta_arc=add_meta_arc),
      ot_constraints.onset_transducer(add_meta_arc=add_meta_arc),
      ot_constraints.peak_transducer(add_meta_arc=add_meta_arc),
      ot_constraints.ssp_transducer(add_meta_arc=add_meta_arc),
      ot_constraints.length_transducer(add_meta_arc=add_meta_arc),
  ]
  if not with_syllabification:
    transducers.append(syllabification.unsyllabification_transducer(add_meta_arc=add_meta_arc))
  #"""

  if only_init:
    return None

  combined = pt.Compose(transducers, add_meta_arc=add_meta_arc)
  combined.arc_sort_output()
  return combined

class TrainingSample(object):
  def __init__(self, sw_w, sw_pron_list, ar_word_list):
    self.sw_word = sw_w
    self.sw_pron_list = sw_pron_list
    self.ar_word_list = ar_word_list
    print("sw_pron_list=", sw_pron_list)

  def ApplyLoanwords(self, ar_vocab_groups, loanwords_transducer,
                     sw_pre_transducer, add_meta_arc, with_syllabification):
    time_a = time.time()
    sw_word_transducer = pt.UnionLinearChains(self.sw_pron_list)
    if add_meta_arc:
      pt.AddPassThroughArcs(sw_word_transducer)
    if with_syllabification:
      pt.AddSyllabificationArcs(sw_word_transducer)
    sw_word_transducer.arc_sort_input()
    time_sw = time.time()
    print("    building SW transducer took:", time_sw-time_a, "sec")

    ar_transducer = pt.UnionLinearChains(self.ar_word_list)
    ar_transducer.arc_sort_output()
    time_b = time.time()
    print("    building AR transducer took:", time_b-time_sw, "sec")

    print("  sw_pre_transducer")
    sw_vocab = sw_pre_transducer >> sw_word_transducer
    sw_vocab.arc_sort_input()
    time_c = time.time()
    print("    applying sw_pre_transducer took:", time_c-time_b, "sec")

    print("  loanwords")
    combined = loanwords_transducer >> sw_vocab
    combined.arc_sort_input()
    time_d = time.time()
    print("    applying loanwords took:", time_d-time_c, "sec")

    print("  ar_vocab")
    self.t_all = pt.Transducer()
    for ar_vocab in ar_vocab_groups:
      print(".", sep="", end="")
      sys.stdout.flush()
      self.t_all.set_union(ar_vocab >> combined)
    print()
    self.t_all.arc_sort_input()
    time_e = time.time()
    print("    ar_vocab >> combined took:", time_e-time_d, "sec")

    print("  t_correct")
    self.t_correct = ar_transducer >> self.t_all
    self.t_correct.arc_sort_output()
    self.t_all.arc_sort_output()
    time_g = time.time()
    print("    building t_correct took:", time_g-time_e, "sec")
    print("    total ApplyLoanwords took:", time_g-time_a, "sec")

  def Write(self, file_prefix):
   self.t_correct.write(file_prefix + "t_correct.tr", True, True)
   self.t_all.write(file_prefix + "t_all.tr", True, True)

  def Read(self, file_prefix):
    print("  reading from file")
    self.t_correct = LoadTransducerFromFile(file_prefix + "t_correct.tr")
    self.t_all = LoadTransducerFromFile(file_prefix + "t_all.tr")
    print("  reading done.")
    return (self.t_correct is not None) and (self.t_all is not None)

def MakeSample(sample_file_prefix, ar_words_to_sample_filename, sw_w, sw_pron_list,
               ar_correct_words, ar_vocab_groups, ar_post_transducer,
               loanwords_transducer, sw_pre_transducer, add_meta_arc,
               with_syllabification):
  sample = TrainingSample(sw_w, sw_pron_list, ar_correct_words)
  time_a = time.time()
  if os.path.isfile(ar_words_to_sample_filename):
    with open(ar_words_to_sample_filename) as f:
      reachable_ar_words = []
      for line in f:
        line = line.strip()
        if len(line):
          reachable_ar_words.append(tuple(line.split()))
    #print("Using reachable only AR vocab:", reachable_ar_words)
    ar_vocab = pt.UnionLinearChains(reachable_ar_words)
    print("  minimizing")
    ar_vocab = pt.Minimize(ar_vocab)
    ar_vocab.arc_sort_output()
    print("  compose with ar_post_transducer")
    ar_vocab = ar_vocab >> ar_post_transducer
    ar_vocab.arc_sort_output()
    ar_vocab_groups = [ar_vocab]
    save_reachability = False
  else:
    save_reachability = True
  time_b = time.time()
  print("     ar_vocab took:", time_b-time_a, "sec")
  if not sample.Read(sample_file_prefix):
    time_c = time.time()
    print("  ApplyLoanwords")
    sample.ApplyLoanwords(ar_vocab_groups, loanwords_transducer,
                          sw_pre_transducer, add_meta_arc=add_meta_arc,
                          with_syllabification=with_syllabification)
    time_d = time.time()
    print("     loanwords took:", time_d-time_c, "sec")
    print("  write transducers")
    sample.Write(sample_file_prefix)
  if len(sample.t_all) == 0:
    print("    NOT reachable from ANY AR word")
  elif len(sample.t_correct) == 0:
    print("    NOT reachable from CORRECT AR words")
  else:
    print("    reachable")
  time_e = time.time()
  print("    building sample took:", time_e - time_b, "sec")
  if save_reachability:
    print("  minimizing sample.t_all")
    sw_pron_to_deterministic_str = pt.UnionLinearChains(sw_pron_list, pt.abc.EPSILON)
    assert sample.t_all.isyms == pt.syms
    assert sample.t_all.osyms == pt.syms
    assert sw_pron_to_deterministic_str.osyms == pt.syms
    assert sw_pron_to_deterministic_str.isyms == pt.syms
    t_all_inputs = sample.t_all >> sw_pron_to_deterministic_str
    t_all_inputs = pt.Minimize(t_all_inputs)
    print("  save reachability")
    reachable_ar_words = set()
    for path_istring, _, _, _ in pt.GetPaths(t_all_inputs):
      reachable_ar_words.add(" ".join(path_istring))
    with open(ar_words_to_sample_filename, "w") as out_f:
      out_f.write("\n".join(reachable_ar_words))
    time_f = time.time()
    print("    saving reachability took:", time_f - time_e, "sec")
  time_g = time.time()
  print("    total MakeSample time:", time_g - time_a, "sec", sample_file_prefix)
  return sample

def LoadSamples(filename, sw_pron_dict, ar_pron_dict, ar_vocab_groups, ar_post_transducer,
                loanwords_transducer, sw_pre_transducer,
                transducers_dir, ar_words_to_sample_dir, add_meta_arc=True,
                with_syllabification=False, start_line=0, worker_id=0, num_workers=1):
  for i, line in enumerate(open(filename)):
    if i < start_line:
      continue
    if i % num_workers != worker_id:
      continue
    tokens = line.strip().split(" ||| ")
    if len(tokens) > 1:
      en, sw, ar_buck = tokens[:3]
    else:
      # Test with just SW word per line.
      en, ar_buck = "", ""
      sw = tokens[0]
    ar_words = set()
    for w in ar_buck.split():
      #ar_words.add(w)
      for w_pron in ar_pron_dict.get(w, []):
        ar_words.add(w_pron)
    for sw_w in sw.split():
      print("Line {} SW word {}".format(i, sw_w))
      sw_pron_list = []
      for sw_pron in sw_pron_dict.get(sw_w, []):
        if len(sw_pron) >= args.shortest_sw_word_len:
          sw_pron_list.append(sw_pron)
      if len(sw_pron_list) == 0:
        print("Skipping. No long pronunciations")
        continue
      sample_filename = "{}_{}".format(i, sw_w)
      sample_file_prefix = os.path.join(transducers_dir, sample_filename)
      ar_words_to_sample_filename = os.path.join(ar_words_to_sample_dir, sample_filename)
      if args.only_initialize_transducers:
        if os.path.isfile(sample_file_prefix+"t_all.tr") and os.path.isfile(sample_file_prefix+"t_correct.tr"):
          continue

      sample = MakeSample(sample_file_prefix, ar_words_to_sample_filename,
                          sw_w, sw_pron_list, ar_words, ar_vocab_groups,
                          ar_post_transducer, loanwords_transducer,
                          sw_pre_transducer, add_meta_arc=add_meta_arc,
                          with_syllabification=with_syllabification)
      yield (sample, sample_filename)

def LoadPronDict(filename):
  result = collections.defaultdict(set)
  for line_num, line in enumerate(open(filename)):
    tokens = line.strip().split(" ||| ")
    if len(tokens) != 2:
      print("Error in pron dict {}\n{}: {}".format(filename, line_num + 1, line))
      continue
    word, pron = tokens
    pron = pron.replace(" ː", "ː")
    while "ːː" in pron:
      pron = pron.replace("ːː", "ː")
    pron = tuple(pron.split())
    for x in pron:
      assert x in pt.abc.ALL_LETTERS, (filename, line_num, word, pron)
    result[word].add(pron)
  return result

def InitSymbols(initialize_syms=True, add_meta_arc=True):
  # Load OT Constraint weights from files (or use default_weight)
  ot_constraint_weights = LoadWeightsFromFile(args.in_ot_constraint_weights)
  # Set the weights in abc and initalize ALL_SYMS and PASS_THROUGH.
  pt.abc.SetWeights(ot_constraint_weights)

  # Initialize all transducers to populate the Symbol Table with all possible
  # symbols.
  if initialize_syms:
    #print("1", list(pt.syms.items()))
    unused_composed = ComposeAllTransducers(add_meta_arc=add_meta_arc, only_init=True)
    #print("2", list(pt.syms.items()))
    morphology.ar_morphology_transducer(add_meta_arc=add_meta_arc)
    #print("3", list(pt.syms.items()))
    morphology.sw_morphology_transducer(add_meta_arc=add_meta_arc)
    #print("4", list(pt.syms.items()))
    operations.vowel_deletion_transducer(add_meta_arc=add_meta_arc)
    #print("5", list(pt.syms.items()))

  # Update ALL_SYMS and PASS_THROUGH.
  pt.abc.ReInitSymbolTable(pt.syms)

def Test(test_samples, test_out_dir, add_meta_arc=True):
  print("Printing best paths")
  if add_meta_arc:
    weights_transducer = pt.weights_transducer()
  else:
    weights_transducer = None
  for sample, sample_filename in test_samples:
    print("testing the sample")
    time_a = time.time()
    test_out_file = open(os.path.join(test_out_dir, sample_filename), "w")
    if weights_transducer:
      print("  sample.t_all >> weights_transducer")
      weighted = sample.t_all >> weights_transducer
    elif args.minimize_final_transducer:
      print("  pt.Minimize(sample.t_all)")
      weighted = pt.Minimize(sample.t_all)
    else:
      weighted = sample.t_all
    print("  weighted.shortest_path(args.num_predicted_best_paths)")
    weighted = weighted.shortest_path(args.num_predicted_best_paths)
    ar_words = []
    constraints = []
    weights = []
    full_out_string = []
    full_path_string = []
    time_b = time.time()
    print("   applying weights took:", time_b-time_a, "sec")
    for path_istring, full_path, path_ot_constraints, path_weights in pt.GetPaths(weighted, return_full_path_in_ostring=True):
      if path_weights:
        # Use the overloaded multiply operator, which is a sum operation in the log space.
        path_weight = float(reduce(operator.mul, path_weights))
      else:
        path_weight = 0.0
      ar_words.append("".join(path_istring))
      full_out_string.append("".join([ochar for ichar, ochar in full_path if ochar != pt.abc.EPSILON]))
      full_path_string.append(str(full_path))
      constraints.append("#".join(path_ot_constraints))
      weights.append(str(path_weight))
    test_out_file.write("{} ||| {} ||| {} ||| {} ||| {} ||| {}\n".format(
        sample.sw_word,
        " ".join(ar_words),
        " ".join(constraints),
        " ".join(weights),
        " ".join(full_out_string),
        " $ ".join(full_path_string)))
    test_out_file.close()
    time_c = time.time()
    print("   writing output took:", time_c-time_b, "sec")
    print("   total sample writing time:", time_c-time_a, "sec", sample_filename)

def AssertReachable(ar_str, sw_str, ar_post_transducer, loanwords_transducer,
                    sw_pre_transducer, add_meta_arc=True, with_syllabification=False):
  print("Constructing input transducer for word:", ar_str)
  in_t = pt.linear_chain(ar_str)
  in_t = in_t >> ar_post_transducer

  print("Constructing output transducer for word:", sw_str)
  out_t = pt.linear_chain(sw_str)
  if add_meta_arc:
    pt.AddPassThroughArcs(out_t)
  if with_syllabification:
    pt.AddSyllabificationArcs(out_t)
  out_t = sw_pre_transducer >> out_t
  if add_meta_arc:
    out_t = out_t >> pt.weights_transducer()

  out_t.arc_sort_input()
  in_t.arc_sort_output()
  print("Combining loanwords with output")
  test_t1 = loanwords_transducer >> out_t
  if len(test_t1) == 0:
    print("NOT REACHABLE: loanwords_transducer >> out_t")   

  print("Testing input with loanwords")
  test_t3 = in_t >> loanwords_transducer
  if len(test_t3) == 0:
    print("NOT REACHABLE: in_t >> loanwords_transducer")

  print("Combining with input")
  test_t2 = in_t >> test_t1
  if len(test_t2) == 0:
    print("NOT REACHABLE: in_t >> test_t1")
  else:
    print("Reachable!")

  print("Printing full paths")
  pt.PrintFullPaths(test_t2, num_shortest=1)
  print("AssertReachable done.")

def LoadTransducerFromFile(filename):
  if filename and os.path.isfile(filename):
    return pt.fst._fst.read(filename)
  else:
    return None

def main():
  add_meta_arc = not args.remove_meta_arcs
  with_syllabification = args.with_syllabification

  assert args.worker_id < args.num_workers, (args.worker_id, args.num_workers)

  print("Initializing")
  os.makedirs("weights", exist_ok=True)
  cached_data_dir = 'cached_data'
  syms_file = os.path.join(cached_data_dir, "syms_with_meta_" + str(add_meta_arc).lower())
  if os.path.isfile(syms_file):
    pt.syms = pt.fst._fst.read_symbols(syms_file)
    write_syms = False
  else:
    write_syms = True

  InitSymbols(initialize_syms=write_syms, add_meta_arc=add_meta_arc)

  dirnames = DirNames(base_dir=cached_data_dir, ar_pron_dict_file_name=args.ar_pronunciation_dict,
                      test_file_name=args.test_file,
                      add_meta_arc=add_meta_arc,
                      with_syllabification=with_syllabification)

  print("Cache paths:")
  for k, v in sorted(dirnames.paths.items()):
    print("{}\t{}".format(k, v))

  print("Composing all operations and constraints.")
  
  loanwords_transducer = LoadTransducerFromFile(dirnames.paths['loanwords_tr'])
  if not loanwords_transducer:
    loanwords_transducer = ComposeAllTransducers(add_meta_arc=add_meta_arc, with_syllabification=with_syllabification)
    loanwords_transducer.write(dirnames.paths['loanwords_tr'], True, True)

  print("Size of loanwords transducer:", len(loanwords_transducer))

  if args.out_ot_constraint_weights:
    SaveWeightsToFile(pt.abc.OT_CONSTRAINTS, args.out_ot_constraint_weights)

  print("Building AR morphology and vowel deletion")
  ar_post_transducer = LoadTransducerFromFile(dirnames.paths['ar_post_tr'])
  if not ar_post_transducer:
    transducers = [
        morphology.ar_morphology_transducer(add_meta_arc=add_meta_arc, with_syllabification=with_syllabification), 
        operations.vowel_deletion_transducer(add_meta_arc=add_meta_arc),
        operations.min_consonant_count_transducer(
            min_consonant_count=args.min_consonant_count, add_meta_arc=add_meta_arc),
    ]
    ar_post_transducer = pt.Compose(transducers, add_meta_arc=add_meta_arc)
    ar_post_transducer.arc_sort_input()
    ar_post_transducer.write(dirnames.paths['ar_post_tr'], True, True) 

  print("Building SW morphology transducer")
  sw_pre_transducer = LoadTransducerFromFile(dirnames.paths['sw_pre_tr'])
  if not sw_pre_transducer:
    transducers = [
        #pt.accept_all_transducer(), # Remove this one if adding more.
        morphology.sw_morphology_transducer(add_meta_arc=add_meta_arc, with_syllabification=with_syllabification),

    ]
    sw_pre_transducer = pt.Compose(transducers, add_meta_arc=add_meta_arc)
    sw_pre_transducer.arc_sort_output()
    sw_pre_transducer.write(dirnames.paths['sw_pre_tr'], True, True)

  print("Loading AR pronunciation_dict")
  ar_pron_dict = LoadPronDict(args.ar_pronunciation_dict)
  print("Loading SW pronunciation_dict")
  sw_pron_dict = LoadPronDict(args.sw_pronunciation_dict)
  
  print("Loaded pronunciation dicts")

  # Load Arabic vocabulary
  class LazyArVocabGroups(object):
    def __init__(self):
      self.val = None

    def __getitem__(self, i):
      if self.val is None:
        self.val = self.RealInit()
      return self.val[i]

    def __iter__(self):
      if self.val is None:
        self.val = self.RealInit()
      return iter(self.val)

    def RealInit(self):
      print("Loading AR vocab")
      if add_meta_arc:
        ar_vocab_groups = []
      else:
        ar_vocab_groups, ar_vocab_groups_minimized = LoadVocabFromFile(
            pron_dict=ar_pron_dict, limit=None,
            transducer_file_pattern=dirnames.paths['ar_vocab_dir'] + "/ar_vocab_group_*.tr")
        if not ar_vocab_groups_minimized:
          print("Minimize AR vocab groups. Total group num:", len(ar_vocab_groups))
          for i in range(len(ar_vocab_groups)):
            print(".", sep="", end="")
            sys.stdout.flush()
            ar_vocab = ar_vocab_groups[i]
            ar_vocab = pt.Minimize(ar_vocab)
            ar_vocab_groups[i] = ar_vocab
            ar_vocab.write("{}/ar_vocab_group_{}.tr".format(dirnames.paths['ar_vocab_dir'], i), True, True)
          print()
        print("Applying ar_post_tranducer. Total group num:", len(ar_vocab_groups))
        for i in range(len(ar_vocab_groups)):
          print(".", sep="", end="")
          sys.stdout.flush()
          ar_vocab = ar_vocab_groups[i]
          ar_vocab.arc_sort_output()
          ar_vocab = ar_vocab >> ar_post_transducer
          ar_vocab.arc_sort_output()
          ar_vocab_groups[i] = ar_vocab
        print()
      return ar_vocab_groups

  ar_vocab_groups = LazyArVocabGroups()

  if write_syms:
    pt.syms.write(syms_file)

  if args.worker_id < 0:
    if not args.test_file:
      # Quick Init mode.
      ar_vocab_groups.RealInit()
    return

  if args.test_file:
    print("Running testing")
    test_samples_iter = LoadSamples(args.test_file, sw_pron_dict, ar_pron_dict,
        ar_vocab_groups,
        ar_post_transducer, loanwords_transducer, sw_pre_transducer,
        dirnames.paths['test_samples_dir'],
        dirnames.paths['reachable_test_dir'], add_meta_arc=add_meta_arc,
        with_syllabification=with_syllabification,
        start_line=args.start_line, worker_id=args.worker_id,
        num_workers=args.num_workers)
    if not args.only_initialize_transducers:
      Test(test_samples_iter, dirnames.paths['test_out_dir'], add_meta_arc=add_meta_arc)
    else:
      for sample in test_samples_iter:
        del sample

if __name__ == '__main__':
  main()
