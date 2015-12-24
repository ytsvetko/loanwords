#!/usr/bin/env python3

# Implements loanwords parameter optimization
# objective function is accuracy on the dev set.
# Algorithm: Nelder-Mead http://en.wikipedia.org/wiki/Nelder%E2%80%93Mead_method

"""
./nm.py --dev_file ../data/train.en-mt-it --init_simplex ../data/constraints/uniform.txt |& tee nm.out
"""
import subprocess
import numpy as np
import argparse
import hashlib
import os
import shutil
from operator import itemgetter
from concurrent import futures

ALPHA = 1
GAMMA = 2
RO = -0.5
SIGMA = 0.5

parser = argparse.ArgumentParser()
parser.add_argument("--exec_command", default="./loanwords.py --remove_meta_arcs")
parser.add_argument("--parallel_exec_command", default="./run_parallel_loanwords.sh --remove_meta_arcs")
parser.add_argument("--eval_command", default="./eval.py --accuracy_at_n 1")
parser.add_argument("--dev_file", default="../data/train.en-mt-it")
parser.add_argument("--max_iterations", default=10000, type=int)
parser.add_argument("--work_dir", default="nm_optimization")
parser.add_argument("--num_parallel_vertices", default=1, type=int)
parser.add_argument("--weights_dir", default="weights")
parser.add_argument("--eval_dir", default="eval_data")
parser.add_argument("--obj_func", default="accuracy")
parser.add_argument("--init_simplex", help="initial weights file")
parser.add_argument("--simplex_radius", default=500.0, type=float)
args = parser.parse_args()

constraint_list = None  # Initialized in main

def DictHash(d):
  m = hashlib.md5()
  m.update(str(tuple(sorted(d.items()))).encode("utf-8"))
  return m.hexdigest()

def WeightsFile(filename, vals): 
  with open(filename, "w") as f:
    for c, val in zip(constraint_list, vals):
      f.write("{}\t{}\n".format(c, val))
  return filename

def ObjFunc(test_out_dir, reachable_test_dir, params_suffix):
  # find out out file names for eval 
  # ./eval.py  --test_file args.dev_file
  #            --test_out_file hyp_filename 
  #            --reachability_dir reachable_paths/dc2ab1450500df0fd1272f3dba54dfd3/ 
  #            --accuracy_at_n 1 
  #            --out_file   os.path.join(args.eval_dir, os.path.basename(hyp_filename))
  eval_command = args.eval_command.split()
  eval_command.append("--test_file")
  eval_command.append(args.dev_file)
  eval_command.append("--test_out_dir")
  eval_command.append(test_out_dir)
  eval_command.append("--reachability_dir")
  eval_command.append(reachable_test_dir)
  stdout_filename = os.path.join(args.eval_dir, "stdout_" + params_suffix)
  stderr_filename = os.path.join(args.eval_dir, "stderr_" + params_suffix)
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
  return 1.0 - float(output.strip())

def RunLoanwords(vals, quick_init=False):
  # run loanwords.py with with vals for constraint weights
  # ./loanwords.py --remove_meta_arcs
  #                --test_file args.dev_file
  #                --in_ot_constraint_weights WeightsFile(args.weights_dir, vals)
  weights = dict(zip(constraint_list, vals))
  params_suffix = DictHash(weights)
  if quick_init:
    params_suffix = params_suffix + "_quick_init"
  print (params_suffix)
  weights_filename = os.path.join(args.weights_dir, "constraint_weights_" + params_suffix)
  if quick_init:
    loanwords_exec_command = args.exec_command.split()
  else:
    loanwords_exec_command = args.parallel_exec_command.split()
    loanwords_exec_command.append("--test_file")
    loanwords_exec_command.append(args.dev_file)
  loanwords_exec_command.append("--in_ot_constraint_weights")
  loanwords_exec_command.append(WeightsFile(weights_filename, vals))
  stdout_filename = os.path.join(args.work_dir, "stdout_" + params_suffix)
  stderr_filename = os.path.join(args.work_dir, "stderr_" + params_suffix)

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
  return stdout_filename, params_suffix

def Score(vals, quick_init=False):
  stdout_filename, params_suffix = RunLoanwords(vals, quick_init=quick_init)
  if not quick_init:
    test_out_dir, reachable_test_dir, transducers_dir = FindTestOutDir(stdout_filename)
    result = ObjFunc(test_out_dir, reachable_test_dir, params_suffix)
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

class Simplex(object):
  def __init__(self, init_simplex):
    x0 = np.array(init_simplex)
    dim = len(init_simplex)
    vertices = [x0]
    for i in range(dim):
      vertices.append((x0 + args.simplex_radius*np.eye(1, dim, i)).ravel())

    if args.num_parallel_vertices > 1:
      Score(x0, quick_init=True)
    with futures.ThreadPoolExecutor(max_workers=args.num_parallel_vertices) as executor:
      scores = executor.map(Score, vertices)
      self.vertices = list(zip(scores, vertices))

  def Order(self):
    self.vertices = sorted(self.vertices, key=itemgetter(0))

  def Centroid(self):
    bestN = self.vertices[:-1]
    centroid = sum( (x for b,x in bestN) ) / len(bestN)
    return centroid

  def Reflection(self, centroid):
    reflection = centroid + ALPHA * (centroid - self.vertices[-1][1])
    accuracy = Score(reflection)
    return accuracy, reflection

  def Expansion(self, centroid):
    expansion = centroid + GAMMA * (centroid - self.vertices[-1][1])
    accuracy = Score(expansion)
    return accuracy, expansion

  def Contraction(self, centroid):
    contraction = centroid + RO * (centroid - self.vertices[-1][1])
    accuracy = Score(contraction)
    return accuracy, contraction

  def Reduction(self):
    x1 = self.vertices[0]
    new_vertices = []
    for _, x_i in self.vertices[1:]:
      new_x_i = x1[1] + SIGMA * (x_i - x1[1])
      new_vertices.append(new_x_i)
    with futures.ThreadPoolExecutor(max_workers=args.num_parallel_vertices) as executor:
      scores = executor.map(Score, new_vertices)
      self.vertices = [x1] + list(zip(scores, new_vertices))

  def __repr__(self):
    best_score, best_coord = self.vertices[0]
    if args.obj_func == "accuracy":
      best_accuracy = 1.0 - best_score
      file_hash = DictHash(dict(zip(constraint_list, best_coord)))
      return "Best accuracy: {} at {} filename {}".format(best_accuracy, best_coord, file_hash)

def NelderMead(init_simplex):
  simplex = Simplex(init_simplex)
  for i in range(args.max_iterations):
    print("Iteration:", i)
    simplex.Order()
    print(simplex)
    x0 = simplex.Centroid()
    r_accuracy, reflection = simplex.Reflection(x0)
    if r_accuracy < simplex.vertices[0][0]:
      print("Expansion")
      ex_accuracy, expansion = simplex.Expansion(x0)
      if ex_accuracy < r_accuracy:
        simplex.vertices[-1] = (ex_accuracy, expansion)
      else:
        simplex.vertices[-1] = (r_accuracy, reflection)
    elif r_accuracy < simplex.vertices[-2][0]:
      print("Insert reflected (step 3)")
      simplex.vertices[-1] = (r_accuracy, reflection)
    else:
      print("Contraction")
      c_accuracy, contraction = simplex.Contraction(x0)
      if c_accuracy < simplex.vertices[-1][0]:
        simplex.vertices[-1] = (c_accuracy, contraction)
      else:
        print("Reduction")
        simplex.Reduction()

def LoadWeightsFromFile(filename):
  result = {}
  for line in open(filename):
    line = line.strip()
    if len(line) == 0 or line.startswith("#"):
      continue
    key, weight = line.split("\t")
    assert key not in result, key
    result[key] = float(weight)
  constraint_list, init_weights = [], []
  for k,v in sorted(result.items()):
    constraint_list.append(k)
    init_weights.append(v)
  return constraint_list, init_weights

def main():
  assert os.path.isfile(args.init_simplex)
  global constraint_list
  constraint_list, init_weights = LoadWeightsFromFile(args.init_simplex)
  os.makedirs(args.work_dir, exist_ok=True)
  os.makedirs(args.weights_dir, exist_ok=True)
  os.makedirs(args.eval_dir, exist_ok=True)
  NelderMead(init_weights)

if __name__ == '__main__':
  main()
