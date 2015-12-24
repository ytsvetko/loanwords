#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import collections
import os

parser = argparse.ArgumentParser()
parser.add_argument('--test_file_name')
parser.add_argument('--test_out_dir', required=True)
parser.add_argument('--reachability_dir')
parser.add_argument('--accuracy_at_n', default=1, type=int)
parser.add_argument('--max_weight', default=1000000000000.0, type=float)
parser.add_argument('--ar_pronunciation_dict', default="../data/pron-dict/pron-dict.loan.ar")
args = parser.parse_args()

def LoadPronDict(filename):
  result = collections.defaultdict(set)
  for line in open(filename):
    tokens = line.strip().split(" ||| ")
    if len(tokens) != 2:
      continue
    word, pron = tokens
    pron = pron.replace(" ː", "ː")
    result[word].add("".join(pron.split()))
  return result

def ReadWordsToSet(filename):
  result = set()
  for line in open(filename):
    result.add("".join(line.strip().split()))
  return result

def ReadInput(ar_pron_dict, test_file_name, test_out_getter, reachability_dir):
  for i, line in enumerate(open(test_file_name)):
    tokens = line.strip().split(" ||| ")
    en, sw, ar_buck = tokens[:3]
    correct_ar_words = set()
    for w in ar_buck.split():
      for w_pron in ar_pron_dict.get(w, []):
        correct_ar_words.add(w_pron)
    for sw_w in sw.split():
      print("Line {} SW word {}".format(i, sw_w))
      sample_filename = "{}_{}".format(i, sw_w)
      reachability_filename = os.path.join(reachability_dir, sample_filename)
      if not os.path.isfile(reachability_filename):
        continue
      reachable_ar_words = ReadWordsToSet(reachability_filename)
      test_result = TestResult(en, i, sw_w, correct_ar_words, reachable_ar_words)
      test_output = test_out_getter.GetTestResults(sample_filename)
      if test_output is None:
        continue
      test_result.SetTestOutput(*test_output)
      yield test_result

class TestOutGetterFromDir(object):
  def __init__(self, test_out_dir):
    self.test_out_dir = test_out_dir

  def GetTestResults(self, filename):
    line = open(os.path.join(self.test_out_dir, filename)).readlines()[0]
    return self.ConvertLineToTestResult(line)

  def ConvertLineToTestResult(self, line):
    sw_word, ar_words, constraints, weights, full_out_str, full_paths = line.split(" ||| ")
    if ar_words:
      ar_words = ar_words.split(" ")
    if constraints:
      constraints = [c_str.split("#") for c_str in constraints.split(" ")]
    else:
      constraints = ["" for _ in ar_words]
    if weights:
      weights = [float(w) for w in weights.split(" ")]
    assert len(ar_words) == len(constraints), (ar_words, constraints)
    assert len(ar_words) == len(weights), (ar_words, weights)
    return sw_word, list(zip(ar_words, constraints, weights))

class TestResult(object):
  def __init__(self, en, line_num, sw_w, correct_ar_words, reachable_ar_words):
    self.en = en
    self.line_num = line_num
    self.sw_w = sw_w
    self.correct_ar_words = correct_ar_words
    self.reachable_ar_words = reachable_ar_words

  def SetTestOutput(self, test_out_sw_word, test_result_tuples_list):
    assert self.sw_w == test_out_sw_word, (self.line_num, self.sw_w, test_out_sw_word)
    self.test_result_tuples_list = test_result_tuples_list

  def IsCorrectReachable(self):
    result = len(self.correct_ar_words & self.reachable_ar_words) > 0
    if not result:
      print("No correct reachable")
      print("Correct:", self.correct_ar_words)
      print("Reachable:", self.reachable_ar_words)
    return result

  def GetNumResultsAt(self, n, max_weight):
    results_at_n = 0
    correct_results_at_n = 0
    prev_w = None
    for ar_word, constraints, weight in self.test_result_tuples_list:
      if float(weight) > max_weight:
        break
      if prev_w != weight:
        n -= 1
        if n < 0:
          break
        prev_w = weight
      results_at_n += 1
      if ar_word in self.correct_ar_words:
        correct_results_at_n += 1
    return results_at_n, correct_results_at_n

def main():
  print("Loading pronunciation dicts")
  ar_pron_dict = LoadPronDict(args.ar_pronunciation_dict)
  test_out_getter = TestOutGetterFromDir(args.test_out_dir)

  input_iter = ReadInput(ar_pron_dict, args.test_file_name,
                         test_out_getter, args.reachability_dir)
  num_of_reachable_samples = 0
  num_of_reachable_correct_samples = 0
  num_of_unreachable_samples = 0
  sum_reachable_correct_hard_accuracy = 0.0
  sum_reachable_correct_soft_accuracy = 0.0
  sum_hard_accuracy = 0.0
  sum_soft_accuracy = 0.0
  for test_result in input_iter:
    results_at_n, correct_results_at_n = test_result.GetNumResultsAt(args.accuracy_at_n, args.max_weight)
    if results_at_n == 0:
      num_of_unreachable_samples += 1
      continue
    num_of_reachable_samples += 1
    hard_accuracy = 1 if correct_results_at_n > 0 else 0
    soft_accuracy = correct_results_at_n / results_at_n
    sum_hard_accuracy += hard_accuracy
    sum_soft_accuracy += soft_accuracy
    if test_result.IsCorrectReachable():
      num_of_reachable_correct_samples += 1
      sum_reachable_correct_hard_accuracy += hard_accuracy
      sum_reachable_correct_soft_accuracy += soft_accuracy
  print("SUMMARY:")
  print("Number of unreachable samples:", num_of_unreachable_samples)
  print("Number of reachable samples:", num_of_reachable_samples)
  print("Number of reachable correct:", num_of_reachable_correct_samples)
  print("Total hard accuracy:", sum_hard_accuracy / num_of_reachable_samples)
  print("Total soft accuracy:", sum_soft_accuracy / num_of_reachable_samples)
  print("Reachable correct hard accuracy:", sum_hard_accuracy / num_of_reachable_correct_samples)
  print("Reachable correct soft accuracy:", sum_soft_accuracy / num_of_reachable_correct_samples)
  # Objective function - Reachable correct soft accuracy
  print("\n\n\n")
  print(sum_soft_accuracy / num_of_reachable_correct_samples)

if __name__ == '__main__':
  main()
