#!/usr/bin/env python3

# objective function is accuracy on the dev set.

"""
./lw_score.py --dev_file ../data/train.sw-en-ar --weights_file_hash <md5_hash>
"""
import subprocess
import argparse
import hashlib
import os
import shutil
import json
from operator import itemgetter

parser = argparse.ArgumentParser()
parser.add_argument("--weights_file_hash", required=True)
parser.add_argument("--parallel_exec_command", default="./run_parallel_loanwords.sh --remove_meta_arcs")
parser.add_argument("--eval_command", default="./eval.py --accuracy_at_n 1")
parser.add_argument("--dev_file", default="../data/train.sw-en-ar")
parser.add_argument("--log_dir", default="logs")
parser.add_argument("--weights_dir", default="weights")
# Only when running a multi-threaded config.
parser.add_argument("--exec_command", default="./loanwords.py --remove_meta_arcs")
args = parser.parse_args()

def ObjFunc(test_out_dir, reachable_test_dir, weights_file_hash):
  # find out out file names for eval 
  # ./eval.py  --test_file args.dev_file
  #            --test_out_dir hyp_filename 
  #            --reachability_dir reachable_paths/dc2ab1450500df0fd1272f3dba54dfd3/ 
  #            --accuracy_at_n 1 
  eval_command = args.eval_command.split()
  eval_command.append("--test_file")
  eval_command.append(args.dev_file)
  eval_command.append("--test_out_dir")
  eval_command.append(test_out_dir)
  eval_command.append("--reachability_dir")
  eval_command.append(reachable_test_dir)
  stdout_filename = os.path.join(args.log_dir, weights_file_hash + "_eval_stdout")
  stderr_filename = os.path.join(args.log_dir, weights_file_hash + "_eval_stderr")
  with open(stdout_filename, "w") as stdout_file:
    with open(stderr_filename, "w") as stderr_file:
      print(" ".join(eval_command))
      print("Output is written to:", stdout_filename)
      print("Output is written to:", stderr_filename)
      exit_code = subprocess.call(eval_command, stdout=stdout_file, stderr=stderr_file)
      if exit_code != 0:
        print("Error running: eval.py")
        raise subprocess.CalledProcessError(exit_code, " ".join(eval_command))
  output = open(stdout_filename).readlines()[-1]
  return -float(output.strip())

def RunLoanwords(weights_file_hash, quick_init=False):
  # run loanwords.py with with vals for constraint weights
  # ./loanwords.py --remove_meta_arcs
  #                --test_file args.dev_file
  #                --in_ot_constraint_weights WeightsFile(args.weights_dir, vals)
  out_file_prefix = weights_file_hash
  if quick_init:
    out_file_prefix = out_file_prefix + "_quick_init"
  if quick_init:
    loanwords_exec_command = args.exec_command.split()
  else:
    loanwords_exec_command = args.parallel_exec_command.split()
    loanwords_exec_command.append("--test_file")
    loanwords_exec_command.append(args.dev_file)
  loanwords_exec_command.append("--in_ot_constraint_weights")
  loanwords_exec_command.append(os.path.join(args.weights_dir, weights_file_hash))
  stdout_filename = os.path.join(args.log_dir, out_file_prefix + "_lw_stdout")
  stderr_filename = os.path.join(args.log_dir, out_file_prefix + "_lw_stderr")

  if not (os.path.isfile(stdout_filename) and os.path.isfile(stderr_filename)
          and os.path.getsize(stderr_filename) == 0):
    with open(stdout_filename, "w") as stdout_file:
      with open(stderr_filename, "w") as stderr_file:
        print(" ".join(loanwords_exec_command))
        print("Output is written to:", stdout_filename)
        print("Output is written to:", stderr_filename)
        exit_code = subprocess.call(loanwords_exec_command, stdout=stdout_file, stderr=stderr_file)
        if exit_code != 0:
          print("Error running loanwords.py")
          raise subprocess.CalledProcessError(exit_code, " ".join(loanwords_exec_command)) 
  return stdout_filename

def Score(weights_file_hash, quick_init=False):
  stdout_filename = RunLoanwords(weights_file_hash, quick_init=quick_init)
  if not quick_init:
    test_out_dir, reachable_test_dir, transducers_dir = FindTestOutDir(stdout_filename)
    result = ObjFunc(test_out_dir, reachable_test_dir, weights_file_hash)
    shutil.rmtree(transducers_dir)
    return result

def FindTestOutDir(stdout_filename):
  test_out_dir, reachable_test_dir, transducers_dir = None, None, None
  for line in open(stdout_filename):
    if line.startswith('test_out_dir\t'):
      test_out_dir = line.strip().split('\t')[1]
    elif line.startswith('reachable_test_dir\t'):
      reachable_test_dir = line.strip().split('\t')[1]
    elif line.startswith('test_samples_dir\t'):
      transducers_dir = line.strip().split('\t')[1]
    if test_out_dir and reachable_test_dir and transducers_dir:
      return test_out_dir, reachable_test_dir, transducers_dir

def main():
  assert os.path.isfile(os.path.join(args.weights_dir, args.weights_file_hash))
  os.makedirs(args.log_dir, exist_ok=True)  
  print("COST:", Score(args.weights_file_hash))

if __name__ == '__main__':
  main()
